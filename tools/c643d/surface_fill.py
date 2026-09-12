"""Experimental HORS-V3 surfaces and texture baking; old renderers are unchanged.

Metallic is a stylised flat-lit grey preset. Material uses the OBJ face's MTL
Kd colour, already mapped by objio to the C64 palette (no lighting/textures).
Native hires permits two colours per 8x8 cell, so shade boundaries can clash.
"""
import itertools
import math
from pathlib import Path

import numpy as np

from .colors import C64_PALETTE
from .pipeline import Camera, FrameBuild, _rotate_axis, fit_scale, raster_triangle
from .mesh import cross, dot, normalize, transform_mesh, vsub
from .optimize import picture_bytes
from .clearplan import selective_clear

GREYS = np.array([0, 51, 119, 187, 255], dtype=float)
GREY_CODES = np.array([0, 11, 12, 15, 1], dtype=np.uint8)
RGB = np.zeros((16, 3), dtype=float)
for _code, _rgb in C64_PALETTE.values():
    RGB[_code] = _rgb
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                  [3, 11, 1, 9], [15, 7, 13, 5]])


def raster(mesh, camera, index, count, preset='metallic', axis='y',
           fallback=1, source_colors=True, textures=None):
    vertices = [_rotate_axis(p, 2 * math.pi * index / count, axis)
                for p in mesh.vertices]
    if any(camera.distance + z <= 0 for x, y, z in vertices):
        raise ValueError('Surface-fill mesh crosses the camera plane; increase --camera')
    points = [(camera.cx + camera.focal * x / (camera.distance + z),
               camera.cy - camera.focal * y / (camera.distance + z),
               1 / (camera.distance + z)) for x, y, z in vertices]
    owner, depth = [-1] * (256 * 192), [0.0] * (256 * 192)
    shades = []
    light = normalize((-0.45, 0.65, -1.0))
    for ti, (face, a, b, c) in enumerate(mesh.triangulated_faces()):
        if preset in ('material', 'textured'):
            color = mesh.face_color(face) if source_colors else None
            shade = fallback if color is None else color
        else:
            normal = normalize(cross(vsub(vertices[b], vertices[a]),
                                     vsub(vertices[c], vertices[a])))
            view = normalize((-vertices[a][0], -vertices[a][1],
                              -camera.distance - vertices[a][2]))
            half = normalize(tuple(light[i] + view[i] for i in range(3)))
            intensity = 255 * min(1.0, 0.12 + 0.55 * max(0, dot(normal, light))
                                 + 0.8 * max(0, dot(normal, half)) ** 18)
            shade = int(GREY_CODES[np.argmin(abs(GREYS[1:] - intensity)) + 1])
        shades.append(shade)
        raster_triangle(depth, owner, ti, points[a], points[b], points[c],
                        width=256, height=192)
    owners = np.array(owner).reshape(192, 256)
    picture = np.zeros((192, 256), dtype=np.uint8)
    covered = owners >= 0
    picture[covered] = np.array(shades, dtype=np.uint8)[owners[covered]]
    if textures is not None:
        from .surface_textures import paint
        paint(picture, owners, points, mesh.triangulated_faces(), textures)
    return picture


def quantize(picture, encoding='native', preset='metallic'):
    bit = np.zeros((192, 320), dtype=bool)
    screen = np.full((24, 40), 0x10, dtype=np.uint8)
    expected = np.zeros((192, 320), dtype=np.uint8)
    if encoding == 'dither':
        threshold = np.tile((BAYER + 0.5) / 16, (48, 64))
        bit[:, :256] = RGB[picture, 0] / 255 > threshold
        expected[bit] = 1
        return bit, screen, expected
    for cy in range(24):
        for cx in range(32):
            cell = picture[cy*8:cy*8+8, cx*8:cx*8+8]
            counts = np.bincount(cell.ravel(), minlength=16)
            if counts[0] == 64:
                continue
            candidates = list(map(int, GREY_CODES)) if preset == 'metallic' else sorted(set(cell.ravel()) | {0})
            best = None
            for lo, hi in itertools.combinations(candidates, 2):
                if counts[0] and lo != 0:
                    continue
                errlo = np.sum((RGB - RGB[lo])**2, axis=1)
                errhi = np.sum((RGB - RGB[hi])**2, axis=1)
                score = float(counts @ np.minimum(errlo, errhi))
                if best is None or score < best[0]:
                    best = score, lo, hi, errlo, errhi
            _, lo, hi, errlo, errhi = best
            bits = errhi[cell] <= errlo[cell]
            screen[cy, cx] = hi * 16 + lo
            bit[cy*8:cy*8+8, cx*8:cx*8+8] = bits
            expected[cy*8:cy*8+8, cx*8:cx*8+8] = np.where(bits, hi, lo)
    return bit, screen, expected


def frame_from_pixels(bit, screen, base_screen=0x10):
    records = []
    for y, row in enumerate(bit):
        edges = np.flatnonzero(np.diff(np.r_[False, row, False].astype(np.int8)))
        for start, end in zip(edges[::2], edges[1::2]):
            for x in range(int(start), int(end), 127):
                n = min(127, int(end) - x)
                offset = (y // 8) * 320 + (x // 8) * 8
                records.append((offset & 255, offset >> 8, n,
                                (x & 7) | ((y & 7) << 3),
                                *([0] * ((x % 8 + n + 7) // 8))))
    bitmap = np.packbits(bit.reshape(24, 8, 40, 8).transpose(0, 2, 1, 3),
                        axis=3).reshape(24, 40, 8)
    clear = []
    for cy, row in enumerate(bitmap.any(axis=2)):
        edges = np.flatnonzero(np.diff(np.r_[False, row, False].astype(np.int8)))
        for start, end in zip(edges[::2], edges[1::2]):
            off = cy * 320 + int(start) * 8
            clear.append((off & 255, off >> 8, int(end - start)))
    colors, flat, i = [], screen.ravel(), 0
    while i < len(flat):
        if flat[i] == base_screen:
            i += 1
            continue
        start, value = i, int(flat[i])
        i += 1
        while i < len(flat) and flat[i] == value and i - start < 255:
            i += 1
        colors.append((start & 255, start >> 8, i - start, value))
    frame = FrameBuild(records, clear, int(bit.sum()), int(bit.sum()), [],
                       colors, int(np.sum(screen != base_screen)), 0,
                       tuple(int(x) for x in np.unique(screen)))
    if picture_bytes(frame, base_screen) != bitmap.tobytes() + screen.tobytes():
        raise AssertionError('Surface-fill bitmap packing mismatch')
    return selective_clear(frame)[0]


def build_frames(mesh, count, camera, *, preset='metallic', encoding='native',
                 axis='y', fallback=1, source_colors=True, uniform_foreground=None, textures=None):
    if preset not in ('metallic', 'material', 'textured') or encoding not in ('native', 'dither'):
        raise ValueError('Unknown surface preset or encoding')
    if preset != 'metallic' and encoding != 'native':
        raise ValueError('Material fill uses native colours; dither is a metallic-preset option')
    if not mesh.faces:
        raise ValueError('Surface fill requires polygon faces, not only line edges')
    frames = []
    for i in range(count):
        picture = raster(mesh, camera, i, count, preset, axis, fallback, source_colors, textures)
        if uniform_foreground is not None:
            bits = np.zeros((192, 320), dtype=bool)
            bits[:, :256] = picture != 0
            base_screen = uniform_foreground << 4
            screen = np.full((24, 40), base_screen, dtype=np.uint8)
        else:
            bits, screen, _ = quantize(picture, encoding, preset)
            base_screen = 0x10
        frames.append(frame_from_pixels(bits, screen, base_screen))
        if i % 24 == 0 or i == count - 1:
            print(f'Surface-fill raster: {i+1}/{count}', flush=True)
    return frames


def cmd_build(a):
    import json
    from dataclasses import asdict
    from . import cli
    from .colors import c64_color_index
    from .hors_v2_stable import assemble_cartridge, encoder
    from .cartstream import pack_frames
    if a.renderer in ('hors-renderer-v3', 'hors-render-v3'):
        a.renderer = 'hors-renderer-v3'
        from .hors_v3 import assemble_cartridge, prepare_colors, color_plan, color_plan_fits, literal_encoder
    if a.renderer != 'hors-renderer-v3' or a.blend or a.scene:
        raise ValueError('Experimental --surface-fill requires hors-renderer-v3; scenes are unsupported (V3 interactive rotation is supported)')
    if not a.text_overlay or a.rastertime_profiler or cli._viewport_height(a) != 192:
        raise ValueError('Experimental --surface-fill requires the standard 192-line viewport and text overlay, without raster profiler')
    if c64_color_index(a.background_color) != 0:
        raise ValueError('Experimental --surface-fill currently requires a black background')
    if a.legacy_cart or a.hud_text or a.intro or a.ending:
        raise ValueError('Experimental --surface-fill uses standard standalone cartridge boot and HUD')
    mesh, label, axis, vis, ztol, angle, color, source, percell, anim, tilt, travel, rise = cli.build_mesh(a)
    if anim != 'spin':
        raise ValueError('Experimental --surface-fill currently supports spin animations')
    count = a.frames if a.frames is not None else 128
    if not 1 <= count <= 255:
        raise ValueError('--surface-fill requires 1..255 orientations')
    camera = Camera(distance=a.camera, focal=a.focal, cx=128, cy=96)
    scale = fit_scale(mesh, count, camera, margin=a.margin,
                      max_scale=a.max_fit_scale, spin_axis=axis, height=192) if not a.no_auto_fit else 1.0
    mesh = transform_mesh(mesh, scale=scale)
    outdir = Path(a.output_dir).resolve() if a.output_dir else cli.BUILD
    stem = a.output or label.lower().replace(' ', '_') + '-surface-' + a.surface_fill + '-' + a.surface_encoding + '-' + a.renderer
    if not a.output and a.interactive_cart:
        stem += '-interactive'
    if stem.endswith('.crt'):
        stem = stem[:-4]
    targets = [outdir / (stem + suffix) for suffix in ('.crt', '.lbl', '-manifest.json', '-surface.json')]
    if not cli._check_overwrite(targets, a.overwrite_policy):
        return 2
    fallback = c64_color_index(color)
    palette = {mesh.face_color(i) if source and mesh.face_color(i) is not None else fallback
               for i in range(len(mesh.faces))}
    textures = None
    if a.surface_fill == 'textured':
        if not a.obj:
            raise ValueError('Experimental textured surfaces currently require --obj')
        if a.ignore_colors or a.color is not None:
            raise ValueError('Textured surfaces use map_Kd and Kd; remove --no-color/--color')
        from .surface_textures import load_textures
        textures = load_textures(a.obj, mesh)
    uniform = next(iter(palette)) if a.surface_fill == 'material' and len(palette) == 1 else None
    if a.surface_fill == 'none':
        from .pipeline import build_frames as build_wire_frames
        from .optimize import optimize_frames
        from .runjoin import join_frames
        from .clearplan import selective_clear_frames
        frames, _ = build_wire_frames(mesh, count, camera, spin_axis=axis,
            visibility_mode=vis, z_tolerance=ztol, feature_angle=angle,
            enable_source_colors=percell, fallback_color=fallback,
            background_color=0, height=192, max_visible_runs=65535)
        frames, _ = optimize_frames(frames, fallback << 4)
        frames, _ = join_frames(frames)
        frames, _ = selective_clear_frames(frames)
        uniform = None if percell else fallback
    else:
        frames = build_frames(mesh, count, camera, preset=a.surface_fill,
                              encoding=a.surface_encoding, axis=axis,
                              fallback=fallback, source_colors=source,
                              uniform_foreground=uniform, textures=textures)
    outdir.mkdir(parents=True, exist_ok=True)
    settings = dict(experimental=True, preset=a.surface_fill, encoding=a.surface_encoding,
                    frames=count, fit_scale=scale, triangles=len(mesh.triangulated_faces()),
                    lighting='flat Blinn-Phong grey preset' if a.surface_fill == 'metallic' else 'perspective-correct map_Kd times Kd' if a.surface_fill == 'textured' else 'unlit MTL Kd / --color',
                    native_limit='two colours per 8x8 cell; black preserved at silhouettes',
                    host_rasterized=True, runtime_triangle_lighting=False,
                    uniform_material_fast_path=uniform is not None)
    (outdir / (stem + '-surface.json')).write_text(json.dumps(settings, indent=2) + '\n')
    oracle = outdir / (stem + '-oracle.json')
    oracle.write_text(json.dumps([asdict(f) for f in frames]))
    colors = percell if a.surface_fill == 'none' else a.surface_encoding == 'native' and uniform is None
    try:
        packed_frames, pack_encoder = frames, encoder(a.v2_draw_gap, a.v2_batch_budget)
        if colors:
            base_screen = fallback << 4 if a.surface_fill == 'none' else 0x10
            active, runs = color_plan(frames, base_screen)
            pair_palette = None
            if a.v3_color_encoding == 'indexed4':
                screen_maps = [picture_bytes(f, base_screen)[7680:] for f in frames]
                pair_palette = sorted({screen[i] for screen in screen_maps for i in active})
                if len(pair_palette) > 16:
                    raise ValueError('indexed4 needs at most 16 colour pairs; use literal')
            if color_plan_fits(frames, active, runs, pair_palette):
                pack_encoder = literal_encoder(active, base_screen, a.v2_draw_gap, a.v2_batch_budget, pair_palette)
            else:
                if a.v3_color_encoding == 'indexed4':
                    raise ValueError('indexed4 colour address plan exceeds reserved space; use literal')
                packed_frames = prepare_colors(frames, base_screen)[0]
        pack_frames(packed_frames, colors, encoder=pack_encoder)
    except ValueError as exc:
        raise ValueError(f'Surface-fill packing: {exc}. Use fewer --frames; no geometry or frame-count reduction is automatic. Oracle saved to {oracle}') from exc
    if a.no_assemble:
        print(f'Surface-fill oracle saved: {oracle}', flush=True)
        return 0
    tass = cli.resolve_executable(a.tass, 'tass')
    cartconv = cli.require_cartconv(a.cartconv, verbose=True)
    if not tass or not cartconv:
        return 2
    crt, manifest = assemble_cartridge(cli.ROOT, frames, mesh, tass=tass,
        cartconv=cartconv, outdir=outdir, stem=stem, tass_args=a.tass_args,
        colors=colors, optimize=False, prefer=a.prefer, color_index=fallback if a.surface_fill == 'none' else uniform if uniform is not None else 1,
        background_color=0, border_color=c64_color_index(a.border_color),
        draw_gap=a.v2_draw_gap, batch_budget=a.v2_batch_budget, color_encoding=a.v3_color_encoding,
        interactive=a.interactive_cart)
    manifest['surface_fill'] = settings
    (outdir / (stem + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    if a.run:
        from .cartlaunch import run
        vice = cli.resolve_executable(a.vice, 'vice')
        if not vice:
            raise ValueError('VICE not found')
        run(vice, crt, a.vice_args, clean_settings=a.vice_clean_settings, cwd=cli.ROOT)
    return 0
