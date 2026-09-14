"""GMod3-owned object/SVG conversion front end.

Based on the current toolkit surface workflow; all cartridge preflight,
assembly and launch operations go exclusively through GMod3 modules.
"""
from pathlib import Path
from .surface_fill import build_frames, rebase_frames, SOURCE_RAMPS
from .surface_palettes import shade_codes
from .colors import c64_color_name
from .pipeline import Camera, fit_scale
from .mesh import transform_mesh

def cmd_build(a):
    from .input_flip import options as flip_options
    flips=flip_options(a)
    import json
    from dataclasses import asdict
    from . import cli
    from .colors import c64_color_index
    from .gmod3_stream import pack_frames
    from .gmod3_v3 import assemble_cartridge
    if a.renderer in ('hors-renderer-v3', 'hors-render-v3'):
        a.renderer = 'hors-renderer-v3'
    if a.renderer != 'hors-renderer-v3' or a.blend or a.scene:
        raise ValueError('GMod3 object/SVG processing requires the HORS-V3 picture core; scenes use the separate GMod3 scene module')
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
        raise ValueError('GMod3 object/SVG builds use the standard cartridge boot and HUD')
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
    renderer_name=getattr(a,'requested_renderer',None) or 'hors-renderer-v3'
    from .renderer_names import display_name
    renderer_label=display_name(renderer_name,'gmod3')
    stem = a.output or label.lower().replace(' ', '_') + '-surface-' + a.surface_fill + '-' + a.surface_encoding + '-' + renderer_label
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
        pack_frames(packed_frames, colors=colors, encode=pack_encoder, size_mib=a.gmod3_size_mib or 2, first_bank=a.gmod3_first_bank or 4)
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
        size_mib=a.gmod3_size_mib or 2, first_bank=a.gmod3_first_bank or 4,
        renderer_name=getattr(a,"requested_renderer",None) or "hors-renderer-v3",
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
        from .gmod3_cli import command
        vice = cli.resolve_executable(a.vice, 'vice')
        if not vice:
            raise ValueError('VICE not found')
        import subprocess
        subprocess.run(command(vice,crt,a.vice_args,clean_settings=a.vice_clean_settings),cwd=cli.ROOT,check=True)
    return 0
