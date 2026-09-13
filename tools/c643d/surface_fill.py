"""Experimental HORS-V3 surfaces and texture baking; old renderers are unchanged.

Metallic is a stylised flat-lit grey preset. Material uses the OBJ face's MTL
Kd colour, already mapped by objio to the C64 palette (no lighting/textures).
Native hires permits two colours per 8x8 cell, so shade boundaries can clash.
"""
import itertools
import math
from pathlib import Path

import numpy as np

from .colors import C64_PALETTE, palette_color_distances, c64_color_name
from .surface_palettes import SHADE_PALETTES, shade_codes
from .pipeline import Camera, FrameBuild, _rotate_axis, _frame_transform, fit_scale, raster_triangle
from .mesh import cross, dot, normalize, transform_mesh, vsub
from .optimize import picture_bytes
from .clearplan import selective_clear

GREYS = np.array([0, 51, 119, 187, 255], dtype=float)
GREY_CODES = np.array([0, 11, 12, 15, 1], dtype=np.uint8)
RGB = np.zeros((16, 3), dtype=float)
for _code, _rgb in C64_PALETTE.values():
    RGB[_code] = _rgb
PERCEPTUAL_ERROR = np.array([palette_color_distances(tuple(map(int, rgb))) for rgb in RGB])
SOURCE_RAMPS = np.array([shade_codes(c64_color_name(i))[1:] for i in range(16)], dtype=np.uint8)
# Source-colour shading preserves red paint instead of borrowing the brown
# shadow in the historical metallic red overlay. VIC-II has no darker red;
# repeat native red for the two darkest levels, then light red and white.
SOURCE_RAMPS[2] = (2, 2, 10, 1)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                  [3, 11, 1, 9], [15, 7, 13, 5]])


def raster(mesh, camera, index, count, preset='metallic', axis='y',
           fallback=1, source_colors=True, textures=None, shade_palette='grey', shade_ramp=None,
           background=0, two_sided=False, animation='spin', animation_tilt=62.0,
           animation_travel=120.0, animation_rise=54.0, coverage_bounds=None):
    codes = shade_codes(shade_palette, shade_ramp)
    levels = np.linspace(51, 255, len(codes) - 1)
    vertices = [_frame_transform(p, index, count, spin_axis=axis, animation=animation,
                animation_tilt=animation_tilt, animation_travel=animation_travel,
                animation_rise=animation_rise) for p in mesh.vertices]
    if any(camera.distance + z <= 0 for x, y, z in vertices):
        raise ValueError('Surface-fill mesh crosses the camera plane; increase --camera')
    points = [(camera.cx + camera.focal * x / (camera.distance + z),
               camera.cy - camera.focal * y / (camera.distance + z),
               1 / (camera.distance + z)) for x, y, z in vertices]
    owner, depth = [-1] * (256 * 192), [0.0] * (256 * 192)
    shades, light_levels = [], []
    light = normalize((-0.45, 0.65, -1.0))
    for ti, (face, a, b, c) in enumerate(mesh.triangulated_faces()):
        if preset in ('material', 'textured', 'gradient'):
            color = mesh.face_color(face) if source_colors else None
            shade = fallback if color is None else color
        if preset in ('metallic', 'gradient'):
            normal = normalize(cross(vsub(vertices[b], vertices[a]),
                                     vsub(vertices[c], vertices[a])))
            view = normalize((-vertices[a][0], -vertices[a][1],
                              -camera.distance - vertices[a][2]))
            if two_sided and dot(normal, view) < 0:
                normal = tuple(-v for v in normal)
            half = normalize(tuple(light[i] + view[i] for i in range(3)))
            intensity = 255 * min(1.0, 0.12 + 0.55 * max(0, dot(normal, light))
                                 + 0.8 * max(0, dot(normal, half)) ** 18)
            if preset == 'metallic':
                shade = int(codes[np.argmin(abs(levels - intensity)) + 1])
            light_levels.append(int(np.argmin(abs(np.linspace(51,255,4) - intensity))))
        shades.append(shade)
        raster_triangle(depth, owner, ti, points[a], points[b], points[c],
                        width=256, height=192)
    owners = np.array(owner).reshape(192, 256)
    picture = np.full((192, 256), background, dtype=np.uint8)
    covered = owners >= 0
    if coverage_bounds is not None:
        yy,xx=np.nonzero(covered)
        coverage_bounds.append([int(xx.min()),int(xx.max()),int(yy.min()),int(yy.max())] if len(xx) else None)
    picture[covered] = np.array(shades, dtype=np.uint8)[owners[covered]]
    if textures is not None:
        from .surface_textures import paint
        paint(picture, owners, points, mesh.triangulated_faces(), textures)
    if preset == 'gradient':
        picture[covered] = SOURCE_RAMPS[picture[covered], np.array(light_levels)[owners[covered]]]
    return picture


def quantize(picture, encoding='native', preset='metallic', shade_palette='grey', shade_ramp=None, cell_metric='perceptual', background=0):
    if cell_metric not in ('perceptual', 'rgb'):
        raise ValueError('Unknown surface cell colour metric')
    codes = shade_codes(shade_palette, shade_ramp)
    if (shade_palette != 'grey' or shade_ramp is not None) and (preset != 'metallic' or encoding != 'native'):
        raise ValueError('Coloured shade palettes require metallic fill with native encoding')
    bit = np.zeros((192, 320), dtype=bool)
    screen = np.full((24, 40), 0x10 | background, dtype=np.uint8)
    expected = np.full((192, 320), background, dtype=np.uint8)
    if encoding == 'dither':
        threshold = np.tile((BAYER + 0.5) / 16, (48, 64))
        bit[:, :256] = RGB[picture, 0] / 255 > threshold
        expected[bit] = 1
        return bit, screen, expected
    for cy in range(24):
        for cx in range(32):
            cell = picture[cy*8:cy*8+8, cx*8:cx*8+8]
            counts = np.bincount(cell.ravel(), minlength=16)
            if counts[background] == 64:
                continue
            candidates = list(dict.fromkeys([*codes, background])) if preset == 'metallic' else sorted(set(cell.ravel()) | {background})
            best = None
            for lo, hi in itertools.combinations(candidates, 2):
                if counts[background] and background not in (lo, hi):
                    continue
                errlo = np.sum((RGB - RGB[lo])**2, axis=1) if preset == 'metallic' or cell_metric == 'rgb' else PERCEPTUAL_ERROR[:, lo]
                errhi = np.sum((RGB - RGB[hi])**2, axis=1) if preset == 'metallic' or cell_metric == 'rgb' else PERCEPTUAL_ERROR[:, hi]
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
                 axis='y', fallback=1, source_colors=True, uniform_foreground=None, textures=None,
                 shade_palette='grey', shade_ramp=None, cell_metric='perceptual', background=0, two_sided=False,
                 animation='spin', animation_tilt=62.0, animation_travel=120.0, animation_rise=54.0, coverage_bounds=None, flip_horizontal=False, flip_vertical=False):
    if preset not in ('metallic', 'material', 'textured', 'gradient') or encoding not in ('native', 'dither'):
        raise ValueError('Unknown surface preset or encoding')
    if preset != 'metallic' and encoding != 'native':
        raise ValueError('Material fill uses native colours; dither is a metallic-preset option')
    codes = shade_codes(shade_palette, shade_ramp)
    if (shade_palette != 'grey' or shade_ramp is not None) and (preset != 'metallic' or encoding != 'native'):
        raise ValueError('Coloured shade palettes require metallic fill with native encoding')
    if not mesh.faces:
        raise ValueError('Surface fill requires polygon faces, not only line edges')
    frames = []
    for i in range(count):
        picture = raster(mesh, camera, i, count, preset, axis, fallback, source_colors, textures, shade_palette, shade_ramp, background, two_sided,
                         animation, animation_tilt, animation_travel, animation_rise, coverage_bounds)
        if uniform_foreground is not None:
            bits = np.zeros((192, 320), dtype=bool)
            bits[:, :256] = picture != background
            base_screen = (uniform_foreground << 4) | background
            screen = np.full((24, 40), base_screen, dtype=np.uint8)
        else:
            bits, screen, _ = quantize(picture, encoding, preset, shade_palette, shade_ramp, cell_metric, background)
            base_screen = 0x10 | background
        if flip_horizontal or flip_vertical:
            from .input_flip import surface as flip_surface, bounds as flip_bounds
            bits,screen=flip_surface(bits,screen,flip_horizontal=flip_horizontal,flip_vertical=flip_vertical)
            if coverage_bounds is not None:
                coverage_bounds[-1]=flip_bounds(coverage_bounds[-1],flip_horizontal=flip_horizontal,flip_vertical=flip_vertical)
        frames.append(frame_from_pixels(bits, screen, base_screen))
        if i % 24 == 0 or i == count - 1:
            print(f'Surface-fill raster: {i+1}/{count}', flush=True)
    return frames


def rebase_frames(frames, old_base, new_base):
    """Give mixed-presentation streams one shared screen initialisation byte."""
    from dataclasses import replace
    result = []
    for frame in frames:
        data = picture_bytes(frame, old_base)
        screen, spans, i = data[7680:], [], 0
        while i < len(screen):
            if screen[i] == new_base:
                i += 1
                continue
            start, value = i, screen[i]
            i += 1
            while i < len(screen) and screen[i] == value and i-start < 255:
                i += 1
            spans.append((start&255, start>>8, i-start, value))
        new = replace(frame, color_spans=spans, color_cells=sum(s[2] for s in spans))
        if picture_bytes(new, new_base) != data:
            raise AssertionError('Presentation mode changed while rebasing screen colours')
        result.append(new)
    return result


def cmd_build(a):
    from .input_flip import options as flip_options
    flips=flip_options(a)
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
    shade_palette = getattr(a, 'surface_palette', 'grey')
    shade_ramp = getattr(a, 'surface_ramp', None)
    if (shade_palette != 'grey' or shade_ramp is not None) and (a.surface_fill != 'metallic' or a.surface_encoding != 'native'):
        raise ValueError('--surface-palette colours require --surface-fill metallic and --surface-encoding native')
    # HUD visibility is independent of the precomputed artwork viewport.
    if getattr(a, 'viewport_height', None) is None:
        a.viewport_height = 192
    if a.rastertime_profiler or cli._viewport_height(a) != 192:
        raise ValueError('--surface-fill requires the standard 192-line viewport, without raster profiler')
    background = c64_color_index(a.background_color)
    if background and (a.interactive_cart or a.surface_encoding == 'dither'):
        raise ValueError('Interactive surface colours and dithering require a black background')
    if a.legacy_cart or a.hud_text or a.intro or a.ending:
        raise ValueError('Experimental --surface-fill uses standard standalone cartridge boot and HUD')
    mesh, label, axis, vis, ztol, angle, color, source, percell, anim, tilt, travel, rise = cli.build_mesh(a)
    svg = getattr(a, '_svg_surface', None)
    modes = getattr(a, 'svg_presentation_modes', False)
    variants={}
    for key,filename in [('card',getattr(a,'svg_background_card',None)),('outline',getattr(a,'svg_outline_variant',None))]:
        if filename:
            from copy import copy
            variant_args=copy(a);variant_args.svg=filename;variant_args.obj=None;variant_args.object=None
            variant_args.svg_keep_background=True
            variant_mesh,*_=cli.build_mesh(variant_args)
            variants[key]=(variant_mesh,variant_args._svg_surface)
    if modes and (not svg or not a.interactive_cart or a.surface_fill not in ('gradient','material') or not source):
        raise ValueError('--svg-presentation-modes requires an interactive SVG with source colours and solid/gradient fill')
    count = a.frames if a.frames is not None else 48 if modes else 128
    mode_count=4+2*len(variants)
    if modes and not 1 <= count <= 255//mode_count:
        raise ValueError(f'{mode_count} SVG presentation modes need 1..{255//mode_count} samples each; no samples are reduced automatically')
    if not 1 <= count <= 255:
        raise ValueError('--surface-fill requires 1..255 orientations')
    camera = Camera(distance=a.camera, focal=a.focal, cx=128, cy=96)
    motions = ('spin','crawl') if modes else (anim,)
    scale = min(fit_scale(candidate, count, camera, margin=a.margin,
                      max_scale=a.max_fit_scale, spin_axis=axis, animation=motion,
                      animation_tilt=tilt, animation_travel=travel, animation_rise=rise,
                      height=192) for candidate in [mesh,*[v[0] for v in variants.values()]] for motion in motions) if not a.no_auto_fit else 1.0
    mesh = transform_mesh(mesh, scale=scale)
    variants={key:(transform_mesh(value[0],scale=scale),value[1]) for key,value in variants.items()}
    occlusion_bounds=None
    outdir = Path(a.output_dir).resolve() if a.output_dir else cli.BUILD
    stem = a.output or label.lower().replace(' ', '_') + '-surface-' + a.surface_fill + '-' + a.surface_encoding + '-' + a.renderer
    if not a.output and a.interactive_cart:
        stem += '-interactive'
    if not a.output and (shade_palette != 'grey' or shade_ramp is not None):
        stem += '-' + ('ramp-' + '-'.join(map(str, shade_ramp)) if shade_ramp is not None else shade_palette)
    if stem.endswith('.crt'):
        stem = stem[:-4]
    targets = [outdir / (stem + suffix) for suffix in ('.crt', '.lbl', '-manifest.json', '-surface.json')]
    if not cli._check_overwrite(targets, a.overwrite_policy):
        return 2
    fallback = c64_color_index(color)
    palette = {mesh.face_color(i) if source and mesh.face_color(i) is not None else fallback
               for i in range(len(mesh.faces))}
    textures = None
    texture_report = {}
    if svg and a.surface_fill in ('material', 'textured', 'gradient') and source:
        textures = svg.bindings
    if a.surface_fill == 'textured':
        if not a.obj and svg is None:
            raise ValueError('Textured surfaces require --obj or an SVG source')
        if a.ignore_colors or a.color is not None:
            raise ValueError('Textured surfaces use map_Kd and Kd; remove --no-color/--color')
        if svg is None:
            from .surface_textures import load_textures
            textures = load_textures(a.obj, mesh, report=texture_report)
    uniform = next(iter(palette)) if a.surface_fill == 'material' and len(palette) == 1 and textures is None else None
    if a.surface_fill == 'none':
        from .pipeline import build_frames as build_wire_frames
        from .optimize import optimize_frames
        from .runjoin import join_frames
        from .clearplan import selective_clear_frames
        frames, _ = build_wire_frames(mesh, count, camera, spin_axis=axis,
            visibility_mode=vis, z_tolerance=ztol, feature_angle=angle,
            enable_source_colors=percell, fallback_color=fallback,
            background_color=background, height=192, max_visible_runs=65535,**flips)
        frames, _ = optimize_frames(frames, (fallback << 4) | background)
        frames, _ = join_frames(frames)
        frames, _ = selective_clear_frames(frames)
        uniform = None if percell else fallback
    elif modes:
        frames = []
        for motion in ('spin','crawl'):
            for preset, bg in (('material',1),('gradient',0)):
                selected_mesh,selected_svg=variants.get('outline',(mesh,svg)) if preset=='gradient' else (mesh,svg)
                rows = build_frames(selected_mesh, count, camera, preset=preset, axis=axis,
                    fallback=fallback, source_colors=True, textures=selected_svg.bindings,
                    cell_metric=a.surface_color_metric, background=bg, two_sided=selected_svg.two_sided,
                    animation=motion, animation_tilt=tilt, animation_travel=travel, animation_rise=rise,**flips)
                frames.extend(rebase_frames(rows, 0x10|bg, 0x10))
        if variants:
            occlusion_bounds=[None]*len(frames)
            for selected_mesh,selected_svg in variants.values():
                for motion in ('spin','crawl'):
                    frames.extend(build_frames(selected_mesh,count,camera,preset='material',axis=axis,
                        fallback=fallback,source_colors=True,textures=selected_svg.bindings,
                        cell_metric=a.surface_color_metric,background=0,two_sided=selected_svg.two_sided,
                        animation=motion,animation_tilt=tilt,animation_travel=travel,animation_rise=rise,
                        coverage_bounds=occlusion_bounds,**flips))
        uniform = None
        background = 0
    else:
        frames = build_frames(mesh, count, camera, preset=a.surface_fill,
                              encoding=a.surface_encoding, axis=axis,
                              fallback=fallback, source_colors=source,
                              uniform_foreground=uniform, textures=textures, shade_palette=shade_palette, shade_ramp=shade_ramp, cell_metric=a.surface_color_metric,
                              background=background, two_sided=bool(svg and svg.two_sided),
                              animation=anim, animation_tilt=tilt, animation_travel=travel, animation_rise=rise,**flips)
    outdir.mkdir(parents=True, exist_ok=True)
    settings = dict(input_flip=flips,experimental=False, preset=a.surface_fill, encoding=a.surface_encoding,
                    color_mapping='nearest VIC-II palette; weighted CIELAB (0.5 L squared + a squared + b squared)',
                    cell_mapping='RGB shade error' if a.surface_fill == 'metallic' or a.surface_color_metric == 'rgb' else 'weighted CIELAB error; two colours per cell',
                    frames=count, fit_scale=scale, triangles=len(mesh.triangulated_faces()),
                    lighting='flat Blinn-Phong grey preset' if a.surface_fill == 'metallic' else 'perspective-correct map_Kd times Kd' if a.surface_fill == 'textured' else 'unlit MTL Kd / --color',
                    native_limit='two colours per 8x8 cell; black preserved at silhouettes',
                    host_rasterized=True, runtime_triangle_lighting=False,
                    uniform_material_fast_path=uniform is not None)
    if svg:
        settings['svg'] = svg.report
        if a.surface_fill != 'metallic':
            settings['lighting'] = 'unlit SVG paint or mapped image' if source else 'uniform SVG silhouette'
    if a.surface_fill == 'gradient':
        settings['lighting'] = 'flat Blinn-Phong; each nearest source colour selects its native hue ramp'
        settings['source_color_ramps'] = {c64_color_name(i): list(map(int,SOURCE_RAMPS[i])) for i in range(16)}
    mode_names=['solid-spin','gradient-spin','solid-crawl','gradient-crawl']+[
        f'{key}-{motion}' for key in variants for motion in ('spin','crawl')]
    settings['animation'] = dict(modes=mode_names if modes else [anim],
                                 samples_per_mode=count, total_samples=len(frames))
    if a.obj and a.surface_fill in ('material', 'textured'):
        from .objio import material_color_report
        settings['material_color_mapping'] = material_color_report(a.obj)
        settings['texture_color_mapping'] = texture_report
        print(f"Nearest C64 colour mapping: {len(settings['material_color_mapping'])} materials, {len(texture_report)} texture maps (see -surface.json)", flush=True)
    if a.surface_fill == 'metallic':
        settings.update(shade_palette='custom' if shade_ramp is not None else shade_palette, shade_palette_indices=list(shade_codes(shade_palette, shade_ramp)), custom_ramp=shade_ramp is not None,
                        lighting='flat Blinn-Phong '+('custom ramp' if shade_ramp is not None else shade_palette+' preset'))
    (outdir / (stem + '-surface.json')).write_text(json.dumps(settings, indent=2) + '\n')
    oracle = outdir / (stem + '-oracle.json')
    oracle.write_text(json.dumps([asdict(f) for f in frames]))
    colors = percell if a.surface_fill == 'none' else a.surface_encoding == 'native' and uniform is None
    try:
        from .hors_v3 import encoding_plan
        base_screen = (fallback << 4 if a.surface_fill == 'none' else (uniform << 4 if uniform is not None else 0x10)) | background
        packed_frames, pack_encoder, _, _, _, _ = encoding_plan(
            frames, colors, base_screen, a.v2_draw_gap, a.v2_batch_budget, a.v3_color_encoding)
        pack_frames(packed_frames, colors, encoder=pack_encoder)
    except ValueError as exc:
        raise ValueError(f'Surface-fill packing: {exc}. Only total ROM capacity errors can be helped by fewer --frames; per-frame limits require a smaller picture or another encoding. No geometry or frame-count reduction is automatic. Oracle saved to {oracle}') from exc
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
        background_color=background, border_color=c64_color_index(a.border_color),
        draw_gap=a.v2_draw_gap, batch_budget=a.v2_batch_budget, color_encoding=a.v3_color_encoding,
        interactive=a.interactive_cart, background_effect=getattr(a,'background_effect','none'),
        include_starfield=getattr(a,'include_starfield',True),
        starfield_profile=getattr(a,'starfield_profile',None),
        exhibition_default=getattr(a,'exhibition_default',None) or 'disabled',
        exhibition_order=getattr(a,'exhibition_order',None) or 'sequential',
        exhibition_interval=getattr(a,'exhibition_interval',None) or 5,
        presentation_variants=tuple(variants),occlusion_bounds=occlusion_bounds,
        hud_visible=getattr(a,'hud_visible',True),allow_hud_toggle=getattr(a,'hud_toggle_allowed',None),
        mode_frames=count if modes else 0)
    manifest['surface_fill'] = settings
    (outdir / (stem + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    if a.run:
        from .cartlaunch import run
        vice = cli.resolve_executable(a.vice, 'vice')
        if not vice:
            raise ValueError('VICE not found')
        run(vice, crt, a.vice_args, clean_settings=a.vice_clean_settings, cwd=cli.ROOT)
    return 0
