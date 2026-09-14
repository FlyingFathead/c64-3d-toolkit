"""GMod3-owned authored-scene conversion, paging and PAL pacing."""
from dataclasses import replace
import json
from pathlib import Path
from .gmod3_v3 import assemble_cartridge
from .gmod3_paging import configure as paging


def build(a):
    from . import cli
    from .sceneio import load_scene
    from .pipeline import build_scene_frames
    from .colors import c64_color_index
    from .input_flip import options
    from .hors_v3 import _optimize_wire_frames
    if sum(bool(x) for x in (a.blend,a.scene,a.obj,a.svg,a.object))!=1:
        raise ValueError('Select exactly one Blender or authored-scene input')
    if a.interactive_cart or a.legacy_cart or a.intro or a.ending or a.hud_text or a.rastertime_profiler:
        raise ValueError('GMod3 authored scenes use automatic playback and the standard GMod3 SPACE menu/HUD; native EasyFlash intro/ending programs remain available with --renderer hors-renderer-v3 --cart-type easyflash')
    if a.frames is not None or a.no_assemble or (a.viewport_height or 192)!=192:
        raise ValueError('GMod3 scenes retain authored samples and a 192-line viewport')
    if not 1<=a.frame_ticks<=255:raise ValueError('--frame-ticks must be 1..255')
    rate=a.blender_output_fps
    if rate is not None and (not a.blend or not 1<=rate<=50 or a.sample_step!=1):
        raise ValueError('--blender-output-fps requires --blend, rate 1..50 and --sample-step 1')
    out=Path(a.output_dir).resolve() if a.output_dir else cli.BUILD
    renderer=getattr(a,'requested_renderer',None) or 'hors-renderer-v3'
    from .renderer_names import display_name
    stem=(a.output or Path(a.blend or a.scene).stem+'-'+display_name(renderer,'gmod3')).removesuffix('.crt')
    if not cli._check_overwrite([out/(stem+s) for s in ('.crt','.lbl','-manifest.json')],a.overwrite_policy):return 2
    export=Path(a.scene) if a.scene else cli.BUILD/(stem+'.c643dscene')
    if a.blend:
        from .blender import export_blend_scene
        export_blend_scene(a.blend,export,blender=a.blender,frame_start=a.frame_start,frame_end=a.frame_end,
            sample_step=a.sample_step,root=cli.ROOT,viewport_height=192,viewport_width=a.viewport_width or 320,
            max_frames=1024,output_fps=rate)
    scene=load_scene(export);scene=replace(scene,viewport_width=a.viewport_width or scene.viewport_width)
    color,_,percell=cli._scene_color_policy(scene.mesh,a)
    foreground=c64_color_index(color);background=c64_color_index(a.background_color)
    frames,_=build_scene_frames(scene,visibility_mode='surface' if a.visibility=='auto' else a.visibility,
        z_tolerance=0.0008 if a.z_tolerance is None else a.z_tolerance,
        feature_angle=40 if a.feature_angle is None else a.feature_angle,enable_source_colors=percell,
        fallback_color=foreground,background_color=background,height=192,width=scene.viewport_width,
        max_frames=1024,max_visible_runs=65535,**options(a))
    frames=_optimize_wire_frames(frames,foreground<<4|background)
    paged=len(frames)>255
    if paged and len(frames)%128:
        raise ValueError('The GMod3 long-scene directory currently needs complete 128-picture pages; no samples are added or removed')
    directory_bank=4 if paged else None
    first=a.gmod3_first_bank if a.gmod3_first_bank is not None else 5 if paged else 4
    if paged and first<=4:raise ValueError('Paged GMod3 scenes reserve bank 4 for the directory')
    target=rate or 50/a.frame_ticks
    def transform(source):return paging(source,pages=len(frames)//128 if paged else 1,
        directory_bank=directory_bank or 0,interactive=False,target_fps=target)
    crt,meta=assemble_cartridge(cli.ROOT,frames,scene.mesh,tass=cli.resolve_executable(a.tass,'tass'),
        cartconv=cli.require_cartconv(a.cartconv,verbose=True),outdir=out,stem=stem,
        size_mib=a.gmod3_size_mib or 2,first_bank=first,directory_bank=directory_bank,
        page_frames=128 if paged else 0,colors=percell,color_index=foreground,background_color=background,
        border_color=c64_color_index(a.border_color),interactive=False,include_starfield=False,
        hud_visible=a.text_overlay and a.hud_default!='disabled',source_transform=transform,
        renderer_name=renderer,gap=a.v2_draw_gap,batch_budget=a.v2_batch_budget,
        tass_args=a.tass_args,color_encoding=a.v3_color_encoding,prefer=a.prefer)
    meta.update(authored_scene=True,output_fps=target,authored_frames=len(frames))
    (out/(stem+'-manifest.json')).write_text(json.dumps(meta,indent=2)+'\n')
    if a.run:
        from .gmod3_cli import run
        a.crt=crt;return run(a)
    return 0
