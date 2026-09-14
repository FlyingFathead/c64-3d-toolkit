"""GMod3 HORS-V3 assembly orchestration, isolated from EasyFlash builders.

The current V3 picture planner and pure UI source generators are shared.
The image allocator, wide directory, bank reader and bootstrap are GMod3-owned.
"""
from dataclasses import asdict
import json
from pathlib import Path

from . import __version__, gmod3_stream
from .emit import bytes_lines
from .buildscreen import screen_codes
from .hors_v3 import encoding_plan, patch_literal_runtime, patch_runtime


def capacity_screen(source, size_mib, directory, directory_bank=None):
    # Count reserved/allocated 8 KiB banks, including their internal padding.
    occupied = len(set(range(4))|{d['bank'] for d in directory}|({directory_bank} if directory_bank is not None else set()))
    used_kib, free_kib = occupied*8, size_mib*1024-occupied*8
    texts = [('type', 'cart type: GMod3', 22),
             ('space', f'used: {used_kib} KiB | free: {free_kib} KiB', 23)]
    source = source.replace('build_screen_visible:\n',
                            '        jsr gmod3_capacity_screen\nbuild_screen_visible:\n', 1)
    # Dead after startup: frame-copy workspace is unused until SPACE exits.
    # $2200 is the V3 UI bootstrap and $2400 holds starfield staging.
    lines = ['* = $5000', 'gmod3_capacity_screen:']
    for name, text, row in texts:
        if len(text) > 40:
            raise ValueError('GMod3 capacity label exceeds 40 columns')
        address = 0x400 + 40*row + (40-len(text))//2
        lines += [f'        ldx #{len(text)-1}', f'gmod3_capacity_copy_{name}:',
            f'        lda gmod3_capacity_text_{name},x', f'        sta ${address:04x},x',
            '        dex', f'        bpl gmod3_capacity_copy_{name}']
    lines += ['        rts']
    for name, text, row in texts:
        lines += [f'gmod3_capacity_text_{name}:'] + bytes_lines(screen_codes(text))
    lines += ['.if * > $5200', '.error "GMod3 capacity screen exceeds startup workspace"', '.endif']
    return source+'\n'+'\n'.join(lines)+'\n', dict(
        units='KiB', used_kib=used_kib, free_kib=free_kib, capacity_kib=size_mib*1024,
        accounting='allocated 8 KiB banks including boot/runtime and bank padding; not CRT container size',
        used_bytes=used_kib*1024, free_bytes=free_kib*1024,
        lines=[dict(text=text, row=row, column=(40-len(text))//2) for _, text, row in texts])


def assemble_cartridge(root, frames, mesh, *, color_encoding='literal', interactive=True,
        include_starfield=False, background_effect='none', starfield_profile='light',
        mode_frames=0, presentation_variants=(), occlusion_bounds=None,
        hud_visible=True, collection=False, source_transform=None, renderer_name='hors-renderer-v3',
        allow_hud_toggle=None, exhibition_default='disabled', exhibition_order='sequential',
        exhibition_interval=5, optimize=False, draw_gap=None, **kwargs):
    from . import hors_v3_controls as ctrl, hors_v3_speed as sp, hors_v3_help as hp
    from . import hors_v3_hud as ui, hors_v3_exhibition as ex, hors_v3_intro as intro
    from . import hors_v3_effects as fx, hors_v3_density as sd, hors_v3_star_modes as sl
    from .hors_v3_occlusion import configure as opaque
    root = Path(root)
    original = frames
    base = (kwargs.get('color_index', 1) << 4) | kwargs.get('background_color', 0)
    colors = kwargs.get('colors', True)
    if draw_gap is not None:kwargs['gap']=draw_gap
    gap, budget = kwargs.get('gap', 6), kwargs.get('batch_budget', 2048)
    include_starfield=include_starfield and (interactive or background_effect!='none')
    effects = include_starfield or bool(mode_frames)
    toggle=interactive if allow_hud_toggle is None else allow_hud_toggle
    if mode_frames and (not interactive or len(frames) != mode_frames*(4+2*len(presentation_variants))):
        raise ValueError('GMod3 presentation frame count mismatch')
    frames, encode, policy, literal, runs, palette = encoding_plan(
        frames, colors, base, gap, budget, color_encoding)
    source = (root/'c64/gmod3/renderer.asm').read_text()
    if colors:
        source = patch_literal_runtime(source, runs, palette) if literal else patch_runtime(source)
    if interactive:
        source = ctrl.configure(source, palette=palette)
        source = source.replace("v3_background: .byte 0", f"v3_background: .byte {base&15}", 1)
    if effects:
        source = fx.configure(source, starfield=background_effect!='none', interactive=interactive,
            mode_frames=mode_frames, include_starfield=include_starfield, variants=presentation_variants)
    if interactive:
        source = sp.configure(source, samples=mode_frames or kwargs.get("page_frames") or len(frames))
        source = hp.configure(source, version=__version__, effects=effects, modes=bool(mode_frames),
            stars=include_starfield, variants=presentation_variants, hud=toggle, interval=exhibition_interval)
        if include_starfield:
            if occlusion_bounds is not None:
                source = opaque(source, occlusion_bounds)
            source = sd.configure(source, opaque=occlusion_bounds is not None)
            source = sl.configure(source, default_profile=starfield_profile or 'light')
    source = ui.configure(source, effects=effects, visible=hud_visible, toggle=toggle, internal=interactive)
    if interactive:
        source = ex.configure(source, mode_frames=mode_frames, variants=presentation_variants,
            stars=include_starfield, enabled=exhibition_default=='enabled', order=exhibition_order, interval=exhibition_interval)
    capacity = None
    if not collection:
        source, _ = intro.configure(source, (root/'c64/gmod3/boot.asm').read_text(),
            version=__version__, interactive=interactive)
        from .renderer_names import display_name
        from .renderer_labels import short_intro
        source=short_intro(source,display_name(renderer_name,'gmod3'))
        _, directory = gmod3_stream.pack_frames(frames, size_mib=kwargs.get('size_mib', 2),
            first_bank=kwargs.get('first_bank', 4), colors=colors, encode=encode,page_frames=kwargs.get('page_frames',0))
        source, capacity = capacity_screen(source, kwargs.get('size_mib', 2), directory,kwargs.get('directory_bank'))
        if not interactive:
            source = source.replace('        sei\n        cld\n',
                '        sei\n        cld\n        jsr v3_intro_start\n', 1)
    if source_transform is not None:
        source = source_transform(source)
    crt, manifest = gmod3_stream.assemble_cartridge(root, frames, mesh, encode=encode,
        source=source, reclaim_luts=effects, **kwargs)
    from .renderer_names import display_name
    manifest.update(renderer=renderer_name, renderer_label=display_name(renderer_name,'gmod3'), implementation='HORS-V3 picture core / independent GMod3 backend',
        color_policy=policy, wire_format='hors-v3-color-indexed4-v1' if palette is not None else
        'hors-v3-color-literals-v1' if literal else 'hors-v3-complete-color-runs-v1',
        cartridge_capacity=capacity, interactive=interactive)
    if interactive:
        ctrl.describe(manifest)
        sp.describe(manifest, mode_frames or len(frames))
        hp.describe(manifest, __version__, effects=effects, modes=bool(mode_frames),
            variants=presentation_variants, hud=toggle, interval=exhibition_interval)
        ex.describe(manifest, mode_frames=mode_frames, variants=presentation_variants,
            enabled=exhibition_default=='enabled', order=exhibition_order, interval=exhibition_interval)
    ui.describe(manifest, visible=hud_visible, toggle=toggle)
    if effects:
        fx.describe(manifest, starfield=background_effect!='none', mode_frames=mode_frames,
            include_starfield=include_starfield, variants=presentation_variants)
        if occlusion_bounds is not None:
            manifest['background_effect']['opaque_bounds'] = occlusion_bounds
        if interactive and include_starfield:
            sd.describe(manifest)
            sl.describe(manifest, default_profile=starfield_profile or 'light')
    else:
        manifest['background_effect'] = dict(name='none', included=False, extra_reserved_RAM_bytes=0)
    if not collection:
        intro.describe(manifest, __version__, interactive=interactive)
        manifest['build_screen']['renderer']=display_name(renderer_name,'gmod3')
        manifest['build_screen'].update(cartridge='GMod3', capacity=capacity, capacity_rows=[22, 23])
    (root/manifest['runtime_work']/'oracle.json').write_text(json.dumps([asdict(f) for f in original])+'\n')
    (Path(kwargs['outdir'])/(kwargs['stem']+'-manifest.json')).write_text(json.dumps(manifest, indent=2)+'\n')
    return crt, manifest
