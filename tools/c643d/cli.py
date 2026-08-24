from __future__ import annotations
import argparse, json, math, shutil, subprocess, sys
from pathlib import Path
from . import __version__
from .mesh import Mesh, normalize_mesh, transform_mesh, fix_winding_outward, mesh_diagnostics
from .shapes import (
    torus, cube, sphere, choose_torus_segments, choose_sphere_segments,
    choose_torus_segments_by_vertices, choose_sphere_segments_by_vertices,
)
from .objio import load_obj
from .svgio import load_svg, c64_color_index, c64_color_name
from .assets import load_object_preset, list_object_presets, import_obj_asset, import_svg_asset
from .pipeline import Camera, fit_scale, build_frames, classify_feature_edges
from .emit import emit_tables, emit_hud
from .toolchain import (
    command as tool_command, config_request, load_toolchain_settings,
    resolve_executable,
)

ROOT=Path(__file__).resolve().parents[2]
OBJECTS=ROOT/'objects'; GENERATED=ROOT/'generated'; BUILD=ROOT/'build'; C64=ROOT/'c64'; EXAMPLES=ROOT/'examples'
RENDERERS={'step':'renderer-step.asm','bytechunk':'renderer-bytechunk.asm','yunroll':'renderer-yunroll.asm'}


def preflight(*, tass_name='64tass', vice_name='x64sc', tass_args=(), vice_args=(), need_assemble=True, need_run=False, verbose=True):
    tass=resolve_executable(tass_name,'tass')
    vice=resolve_executable(vice_name,'vice')
    ok=True
    if need_assemble and not tass:
        print(f'error: 64tass not found as {tass_name!r}; install 64tass, configure config/c643d.ini, or pass --tass PATH.', file=sys.stderr)
        ok=False
    elif verbose and tass:
        print(f'preflight: 64tass = {tass}')
        if tass_args: print(f'preflight: 64tass args = {" ".join(tass_args)}')
    if need_run and not vice:
        print(f'error: VICE C64 emulator not found as {vice_name!r}; install VICE, configure config/c643d.ini, or pass --vice PATH.', file=sys.stderr)
        if sys.platform=='darwin':
            print('hint: macOS VICE packages may keep x64sc inside VICE.app/Contents/Resources/bin/ or a top-level bin/ directory.', file=sys.stderr)
        ok=False
    elif not vice and verbose:
        print(f'warning: VICE C64 emulator {vice_name!r} not found; PRG build is still available, but --run will fail.', file=sys.stderr)
        if sys.platform=='darwin':
            print('hint: macOS users can use Homebrew (brew install vice) or set vice=... in config/c643d.ini.', file=sys.stderr)
    elif verbose and vice:
        print(f'preflight: VICE = {vice}')
        if vice_args: print(f'preflight: VICE args = {" ".join(vice_args)}')
    return ok,tass,vice


def cmd_doctor(a):
    ok,_,_=preflight(tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,need_assemble=True,need_run=False,verbose=True)
    print(f'python:    {sys.executable} ({sys.version.split()[0]})')
    print(f'platform:  {getattr(a,"_tool_platform",sys.platform)}')
    cfg=getattr(a,'_tool_config_path',None)
    print(f'config:    {cfg if cfg else "built-in defaults (no config/c643d.ini found)"}')
    print(f'objects:   {OBJECTS}')
    print(f'examples:  {EXAMPLES}')
    return 0 if ok else 2


def cmd_generate_examples(a):
    ok,tass,_=preflight(tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,need_assemble=True,need_run=False,verbose=True)
    if not ok:
        return 2
    manifest=EXAMPLES/'examples.json'
    specs=json.loads(manifest.read_text(encoding='utf-8'))
    EXAMPLES.mkdir(parents=True,exist_ok=True)
    print(f'generating {len(specs)} example PRGs -> {EXAMPLES.relative_to(ROOT)}/')
    for spec in specs:
        name=spec['name']; args=list(spec['args'])
        cmd=[sys.executable,str(ROOT/'c643d.py'),'build',*args,'--output',name,'--tass',a.tass,'--vice',a.vice]
        for extra in a.tass_args: cmd.append(f'--tass-arg={extra}')
        for extra in a.vice_args: cmd.append(f'--vice-arg={extra}')
        if getattr(a,'no_tass_default_args',False): cmd.append('--no-tass-default-args')
        if getattr(a,'no_vice_default_args',False): cmd.append('--no-vice-default-args')
        if getattr(a,'_config_disabled',False): cmd.append('--no-config')
        elif getattr(a,'_tool_config_path',None): cmd.extend(['--config',str(a._tool_config_path)])
        print('\n==',name,'==')
        print('+',' '.join(cmd))
        subprocess.run(cmd,cwd=ROOT,check=True)
        src=BUILD/f'{name}.prg'; dst=EXAMPLES/f'{name}.prg'
        shutil.copy2(src,dst)
        print(f'example: {dst.relative_to(ROOT)}')
    return 0


def _apply_up_axis(mesh: Mesh, up_axis: str) -> Mesh:
    if up_axis=='y': return mesh
    if up_axis=='z': return transform_mesh(mesh,rx=math.radians(-90.0))
    raise ValueError(f'unsupported up axis: {up_axis}')


def _choose_detail(a, kind: str):
    if a.polycount is not None and a.vertices is not None:
        raise ValueError('use either --polycount or --vertices, not both')
    if kind=='torus':
        if a.vertices is not None: return choose_torus_segments_by_vertices(a.vertices)
        if a.polycount is not None: return choose_torus_segments(a.polycount)
        return a.major_segments,a.minor_segments
    if kind=='sphere':
        if a.vertices is not None: return choose_sphere_segments_by_vertices(a.vertices)
        if a.polycount is not None: return choose_sphere_segments(a.polycount)
        return a.lat_segments,a.lon_segments
    return None


def build_mesh(a):
    """Build the selected source asset and return mesh + render/animation metadata."""
    preset_rotate=(0.0,0.0,0.0); preset_scale=1.0; spin_axis='y'
    preset_visibility='auto'; preset_ztol=0.0008; preset_feature_angle=40.0
    preset_color='white'; preset_animation='spin'; preset_anim_tilt=62.0; preset_anim_travel=120.0; preset_anim_rise=54.0
    is_imported=False; is_svg=False

    if getattr(a,'svg',None):
        p=Path(a.svg); label=(a.name or p.stem).upper(); is_imported=is_svg=True
        info=load_svg(p,label,tolerance=a.svg_tolerance,curve_step=a.svg_curve_step,depth=a.svg_depth,connector_stride=a.svg_connector_stride)
        mesh=info.mesh; preset_color=info.c64_color
    elif a.obj:
        p=Path(a.obj); mesh=load_obj(p,a.name or p.stem); label=(a.name or p.stem).upper(); is_imported=True
        mesh=_apply_up_axis(mesh,a.obj_up)
    elif a.object or a.shape=='horse_head':
        slug=a.object or 'horse_head'
        preset=load_object_preset(OBJECTS,slug)
        label=(a.name or preset.name).upper(); is_imported=True
        if preset.obj_path.suffix.lower()=='.svg':
            is_svg=True
            info=load_svg(preset.obj_path,preset.name,tolerance=preset.svg_tolerance,curve_step=preset.svg_curve_step,depth=preset.svg_depth,connector_stride=preset.svg_connector_stride)
            mesh=info.mesh
        else:
            mesh=load_obj(preset.obj_path,preset.name)
            mesh=_apply_up_axis(mesh,preset.up_axis)
        preset_rotate=preset.rotate; preset_scale=preset.scale; spin_axis=preset.spin_axis
        preset_visibility=preset.visibility; preset_ztol=preset.z_tolerance; preset_feature_angle=preset.feature_angle
        preset_color=preset.color; preset_animation=preset.animation; preset_anim_tilt=preset.animation_tilt
        preset_anim_travel=preset.animation_travel; preset_anim_rise=preset.animation_rise
    elif a.shape=='cube':
        mesh=cube(); label='CUBE'
    elif a.shape=='sphere':
        lat,lon=_choose_detail(a,'sphere')
        mesh=sphere(lat,lon); label='SPHERE'
    else:
        major,minor=_choose_detail(a,'torus')
        mesh=torus(major,minor); label='TORUS'

    mesh=normalize_mesh(mesh,46.0)
    if not a.keep_winding:
        mesh=fix_winding_outward(mesh)

    prx,pry,prz=(math.radians(v) for v in preset_rotate)
    mesh=transform_mesh(mesh,rx=prx,ry=pry,rz=prz,scale=preset_scale)
    rx=math.radians(a.rotate_x); ry=math.radians(a.rotate_y); rz=math.radians(a.rotate_z)
    if a.shape=='torus' and not a.obj and not getattr(a,'svg',None) and not a.object and a.rotate_x==0.0:
        rx=math.radians(28.0)
    mesh=transform_mesh(mesh,rx=rx,ry=ry,rz=rz,scale=a.scale); mesh.name=label

    requested_visibility=getattr(a,'visibility','auto')
    if requested_visibility=='auto':
        if preset_visibility!='auto': visibility=preset_visibility
        elif is_imported: visibility='surface'
        else: visibility='frontface'
    else: visibility=requested_visibility
    ztol=getattr(a,'z_tolerance',None)
    if ztol is None: ztol=preset_ztol if is_imported else 0.0008
    feature_angle=getattr(a,'feature_angle',None)
    if feature_angle is None: feature_angle=preset_feature_angle

    requested_color=getattr(a,'color',None)
    color_name=c64_color_name(c64_color_index(requested_color if requested_color is not None else preset_color))
    animation=getattr(a,'animation',None) or preset_animation
    anim_tilt=getattr(a,'animation_tilt',None); anim_tilt=preset_anim_tilt if anim_tilt is None else anim_tilt
    anim_travel=getattr(a,'animation_travel',None); anim_travel=preset_anim_travel if anim_travel is None else anim_travel
    anim_rise=getattr(a,'animation_rise',None); anim_rise=preset_anim_rise if anim_rise is None else anim_rise
    return mesh,label,(a.spin_axis or spin_axis),visibility,float(ztol),float(feature_angle),color_name,animation,float(anim_tilt),float(anim_travel),float(anim_rise)


def prepare_asm(renderer:str,frames:int,color_index:int=1) -> Path:
    src=(C64/RENDERERS[renderer]).read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {frames}',1)
    src=src.replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${color_index:X}0',1)
    src=src.replace('.include "generated/hud.inc"', '.include "../generated/hud.inc"')
    src=src.replace('.include "generated/tables.inc"', '.include "../generated/tables.inc"')
    out=BUILD/'main.asm'; out.write_text(src)
    return out


def print_stats(mesh:Mesh,label:str,renderer:str,scale:float,stats:dict,hud:str,spin_axis:str,visibility:str,z_tolerance:float,feature_angle:float,color_name:str,animation:str):
    print(f'shape:      {label}')
    print(f'vertices:   {len(mesh.vertices)}')
    print(f'edges:      {len(mesh.edges)}')
    print(f'faces:      {len(mesh.faces)}')
    d=mesh_diagnostics(mesh)
    if d['boundary_edges'] or d['nonmanifold_edges']:
        print(f'topology:   boundary {d["boundary_edges"]}; non-manifold {d["nonmanifold_edges"]}')
    print(f'renderer:   {renderer}')
    print(f'spin axis:  {spin_axis}')
    print(f'animation:  {animation}')
    print(f'color:      {color_name}')
    print(f'visibility: {visibility} (z tolerance {z_tolerance:g})')
    if visibility=='surface_creases':
        _,fs=classify_feature_edges(mesh,feature_angle)
        print(f'features:   angle >= {feature_angle:g} deg; {fs["features"]}/{fs["edges"]} edges ({fs["crease"]} crease, {fs["boundary"]} boundary, {fs["nonmanifold"]} non-manifold)')
    print(f'fit scale:  {scale:.4f}')
    print(f'frames:     {stats["frames"]}')
    print(f'runs/frame: {stats["runs_min"]}..{stats["runs_max"]} avg {stats["runs_avg"]:.1f}')
    print(f'pixels:     {stats["pixels_min"]}..{stats["pixels_max"]} avg {stats["pixels_avg"]:.1f}')
    print(f'clear:      {stats["clear_min"]}..{stats["clear_max"]} bytes avg {stats["clear_avg"]:.1f}')
    if stats.get('line_overflow_bytes',0):
        print(f'table spill: {stats["line_overflow_bytes"]} line bytes in low-RAM overflow arena; {stats["line_primary_bytes"]} in primary arena')
    if 'xchunk_reduction' in stats:
        print(f'x-byte LUT: {stats["xchunk_reduction"]:.1f}% RMW reduction in eligible full X chunks')
    print(f'HUD:        {hud}')


def cmd_build(a):
    ok,tass_found,vice_found=preflight(tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,need_assemble=not a.no_assemble,need_run=a.run,verbose=True)
    if not ok: return 2
    GENERATED.mkdir(exist_ok=True); BUILD.mkdir(exist_ok=True); OBJECTS.mkdir(exist_ok=True)
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle,color_name,animation,anim_tilt,anim_travel,anim_rise=build_mesh(a)
    cam=Camera(distance=a.camera,focal=a.focal,cx=128.0,cy=72.0)
    fitted=fit_scale(mesh,a.frames,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=spin_axis,animation=animation,animation_tilt=anim_tilt,animation_travel=anim_travel,animation_rise=anim_rise) if not a.no_auto_fit else 1.0
    mesh=transform_mesh(mesh,scale=fitted)

    frame_candidates=[a.frames]
    if not a.strict_frames:
        for n in (40,36,32,28,24,20,16,12,8):
            if n<a.frames and n not in frame_candidates: frame_candidates.append(n)
    last_error=None
    for actual_frames in frame_candidates:
        frames,candidate_edges=build_frames(mesh,actual_frames,cam,spin_axis=spin_axis,visibility_mode=visibility,z_tolerance=z_tolerance,feature_angle=feature_angle,animation=animation,animation_tilt=anim_tilt,animation_travel=anim_travel,animation_rise=anim_rise)
        try:
            stats=emit_tables(GENERATED/'tables.inc',frames,a.renderer,candidate_edges)
            break
        except RuntimeError as e:
            if not any(k in str(e) for k in ('line tables reach','line tables need','clear tables reach','frame pointer tables reach')): raise
            last_error=e
            if a.strict_frames: raise
            print(f'note: table RAM: {actual_frames} orientations do not fit ({e}); trying fewer orientations; mesh detail unchanged')
    else:
        raise RuntimeError(f'could not fit generated tables: {last_error}')
    if actual_frames != a.frames:
        print(f'table RAM auto-fit: orientations {a.frames} -> {actual_frames}; mesh vertices/edges/faces preserved')
    hud=emit_hud(GENERATED/'hud.inc',label,len(mesh.vertices),len(mesh.edges))
    asm=prepare_asm(a.renderer,actual_frames,c64_color_index(color_name))
    subprocess.run([sys.executable,str(ROOT/'tools'/'asm_sanity.py'),str(asm)],cwd=ROOT,check=True)
    print_stats(mesh,label,a.renderer,fitted,stats,hud,spin_axis,visibility,z_tolerance,feature_angle,color_name,animation)
    outname=a.output or f'{label.lower().replace(" ","_")}-{a.renderer}'
    outdir=Path(a.output_dir).resolve() if getattr(a,'output_dir',None) else BUILD
    outdir.mkdir(parents=True,exist_ok=True)
    prg=outdir/f'{outname}.prg'; lbl=outdir/f'{outname}.lbl'; lst=outdir/f'{outname}.lst'
    if a.no_assemble:
        print(f'generated assembler: {asm}')
        return 0
    tass=tass_found or resolve_executable(a.tass,'tass')
    cmd=tool_command(tass,a.tass_args,['--cbm-prg','--vice-labels','-l',str(lbl),'-L',str(lst),'-o',str(prg),str(asm)])
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
    print(f'built {prg.relative_to(ROOT)}')
    if a.run:
        vice=vice_found or resolve_executable(a.vice,'vice')
        subprocess.run(tool_command(vice,a.vice_args,[str(prg)]),cwd=ROOT,check=False)
    return 0


def _print_mesh_report(label:str,mesh:Mesh):
    d=mesh_diagnostics(mesh)
    fs=', '.join(f'{n}-gon:{count}' for n,count in sorted(d['face_sizes'].items())) or '(wire-only)'
    print(f'{label}: {d["vertices"]} vertices, {d["edges"]} edges, {d["faces"]} faces')
    print(f'face mix: {fs}')
    print(f'boundary edges: {d["boundary_edges"]}; non-manifold edges: {d["nonmanifold_edges"]}; isolated vertices: {d["isolated_vertices"]}')


def cmd_inspect(a):
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle,color_name,animation,anim_tilt,anim_travel,anim_rise=build_mesh(a)
    _print_mesh_report(label,mesh)
    print(f'spin axis: {spin_axis}')
    print(f'animation: {animation}; tilt={anim_tilt:g} travel={anim_travel:g} rise={anim_rise:g}')
    print(f'color: {color_name}')
    print(f'visibility: {visibility} (z tolerance {z_tolerance:g})')
    if visibility=='surface_creases':
        _,fs=classify_feature_edges(mesh,feature_angle)
        print(f'features:   angle >= {feature_angle:g} deg; {fs["features"]}/{fs["edges"]} edges ({fs["crease"]} crease, {fs["boundary"]} boundary, {fs["nonmanifold"]} non-manifold)')
    return 0


def cmd_import_obj(a):
    source=Path(a.file)
    # Parse before copying so a bad OBJ never becomes a repository preset.
    mesh=load_obj(source,a.name or source.stem)
    _print_mesh_report((a.name or source.stem).upper(),mesh)
    preset=import_obj_asset(
        source,OBJECTS,slug=a.as_name,display_name=a.name,up_axis=a.up,
        spin_axis=a.spin_axis,rotate=(a.rotate_x,a.rotate_y,a.rotate_z),
        scale=a.scale,overwrite=a.overwrite,
    )
    print(f'imported:   {preset.obj_path.relative_to(ROOT)}')
    if preset.materials:
        print(f'materials:  {", ".join(preset.materials)}')
    print(f'metadata:   {(OBJECTS/(preset.slug+".json")).relative_to(ROOT)}')
    print(f'build with: ./build.sh --object {preset.slug} --run')
    return 0


def cmd_import_svg(a):
    source=Path(a.file)
    info=load_svg(source,a.name or source.stem,tolerance=a.svg_tolerance,curve_step=a.svg_curve_step,depth=a.svg_depth,connector_stride=a.svg_connector_stride)
    _print_mesh_report((a.name or source.stem).upper(),info.mesh)
    print(f'svg:        contours {info.contours}; points {info.source_points} -> {info.simplified_points}')
    print(f'color:      {info.source_color or "unknown"} -> C64 {info.c64_color}')
    preset=import_svg_asset(
        source,OBJECTS,slug=a.as_name,display_name=a.name,spin_axis=a.spin_axis,
        rotate=(a.rotate_x,a.rotate_y,a.rotate_z),scale=a.scale,color=a.color,
        animation=a.animation,animation_tilt=a.animation_tilt,animation_travel=a.animation_travel,
        animation_rise=a.animation_rise,svg_tolerance=a.svg_tolerance,svg_curve_step=a.svg_curve_step,
        svg_depth=a.svg_depth,svg_connector_stride=a.svg_connector_stride,overwrite=a.overwrite,
    )
    print(f'imported:   {preset.obj_path.relative_to(ROOT)}')
    print(f'metadata:   {(OBJECTS/(preset.slug+".json")).relative_to(ROOT)}')
    print(f'build with: ./build.sh --object {preset.slug} --run')
    return 0


def cmd_list_objects():
    presets=list_object_presets(OBJECTS)
    if not presets:
        print('(no imported objects)'); return 0
    for p in presets:
        mtl=(' mtl='+','.join(p.materials)) if p.materials else ''
        print(f'{p.slug:20} {p.name:20} spin={p.spin_axis} anim={p.animation} color={p.color} file={p.obj_path.name}{mtl}')
    return 0


def _add_config_args(q):
    q.add_argument('--config',help='toolchain config file (default: config/c643d.ini; env: C643D_CONFIG)')
    q.add_argument('--no-config',action='store_true',help='ignore config files and use built-in/CLI toolchain settings')


def _add_toolchain_args(q,settings):
    _add_config_args(q)
    q.add_argument('--tass',default=settings.tass,help='64tass executable name, path, or containing directory')
    q.add_argument('--vice',default=settings.vice,help='x64sc executable name/path, VICE directory, or macOS .app bundle')
    q.add_argument('--tass-arg',dest='tass_args',action='append',default=None,metavar='ARG',help='64tass argument; repeatable; when used, replaces configured default args')
    q.add_argument('--vice-arg',dest='vice_args',action='append',default=None,metavar='ARG',help='VICE argument; repeatable; when used, replaces configured default args')
    q.add_argument('--no-tass-default-args',action='store_true',help='discard configured/built-in 64tass default arguments for this invocation')
    q.add_argument('--no-vice-default-args',action='store_true',help='discard configured/built-in VICE default arguments for this invocation')


def make_parser(settings):
    p=argparse.ArgumentParser(prog='c643d',description='C64 3D wireframe compiler/toolkit')
    p.add_argument('--version',action='version',version=__version__)
    sub=p.add_subparsers(dest='command')
    def common(q):
        q.add_argument('--shape',choices=('torus','cube','sphere','horse_head'),default='torus')
        q.add_argument('--object',help='build a named OBJ/SVG preset from objects/<name> + optional .json metadata')
        q.add_argument('--obj',help='load a one-off arbitrary Wavefront OBJ instead of --shape')
        q.add_argument('--svg',help='load a one-off SVG as a planar/extruded wire object')
        q.add_argument('--obj-up',choices=('y','z'),default='y',help='source up axis for one-off --obj')
        q.add_argument('--svg-tolerance',type=float,default=3.0,help='SVG polyline simplification tolerance in source units')
        q.add_argument('--svg-curve-step',type=float,default=12.0,help='approximate SVG curve sampling step in source units')
        q.add_argument('--svg-depth',type=float,default=5.0,help='SVG wire extrusion depth in normalised toolkit units; 0=flat')
        q.add_argument('--svg-connector-stride',type=int,default=4,help='connect every Nth front/back SVG contour vertex')
        q.add_argument('--name',help='display/object name for custom OBJ/SVG')
        q.add_argument('--polycount',type=int,help='approximate FACE count for procedural torus/sphere')
        q.add_argument('--vertices',type=int,help='approximate VERTEX count for procedural torus/sphere')
        q.add_argument('--major-segments',type=int,default=10,help='torus major segments (default 10)')
        q.add_argument('--minor-segments',type=int,default=5,help='torus tube segments (default 5)')
        q.add_argument('--lat-segments',type=int,default=6,help='sphere latitude segments')
        q.add_argument('--lon-segments',type=int,default=10,help='sphere longitude segments')
        q.add_argument('--rotate-x',type=float,default=0.0,metavar='DEG')
        q.add_argument('--rotate-y',type=float,default=0.0,metavar='DEG')
        q.add_argument('--rotate-z',type=float,default=0.0,metavar='DEG')
        q.add_argument('--scale',type=float,default=1.0)
        q.add_argument('--spin-axis',choices=('x','y','z'),help='animation axis; named object metadata may provide a default')
        q.add_argument('--animation',choices=('spin','recede','crawl'),help='frame transform; named object metadata may provide a default')
        q.add_argument('--animation-tilt',type=float,help='crawl-plane X tilt in degrees')
        q.add_argument('--animation-travel',type=float,help='recede/crawl Z travel over the precomputed sequence')
        q.add_argument('--animation-rise',type=float,help='crawl Y travel over the precomputed sequence')
        q.add_argument('--color',help='C64 foreground colour name or index 0..15; SVG presets can infer this from artwork')
        q.add_argument('--keep-winding',action='store_true',help='do not best-effort reorient mesh face winding')
        q.add_argument('--visibility',choices=('auto','surface_features','surface_creases','surface','frontface'),default='auto',help='hidden-line surface mode; auto uses robust surface Z-buffer for OBJ and front-face mode for procedural closed meshes')
        q.add_argument('--z-tolerance',type=float,help='reciprocal-depth tolerance for visible wire edges; object presets may provide a default')
        q.add_argument('--feature-angle',type=float,help='surface_creases threshold in degrees; sharp manifold edges at/above this angle are preserved')
    b=sub.add_parser('build',help='generate tables, assemble PRG, optionally run VICE'); common(b)
    b.add_argument('--renderer',choices=tuple(RENDERERS),default='yunroll',help='step=v0.7, bytechunk=v0.8, yunroll=current fastest')
    b.add_argument('--frames',type=int,default=48,help='precomputed animation frames/orientations (default 48)')
    b.add_argument('--strict-frames',action='store_true',help='fail instead of reducing orientation count when table RAM overflows')
    b.add_argument('--camera',type=float,default=110.0)
    b.add_argument('--focal',type=float,default=180.0)
    b.add_argument('--margin',type=int,default=4)
    b.add_argument('--max-fit-scale',type=float,default=1.4)
    b.add_argument('--no-auto-fit',action='store_true')
    b.add_argument('--output',help='output basename')
    b.add_argument('--output-dir',help='directory for PRG/LBL/LST outputs (default: build/)')
    _add_toolchain_args(b,settings)
    b.add_argument('--no-assemble',action='store_true')
    b.add_argument('--run',action='store_true')
    i=sub.add_parser('inspect',help='report mesh topology/diagnostics'); common(i)
    imp=sub.add_parser('import-obj',help='copy a Wavefront OBJ into objects/ and create preset metadata')
    imp.add_argument('file')
    imp.add_argument('--as',dest='as_name',help='object slug under objects/ (default: source filename)')
    imp.add_argument('--name',help='display name')
    imp.add_argument('--up',choices=('y','z'),default='y')
    imp.add_argument('--spin-axis',choices=('x','y','z'),default='y')
    imp.add_argument('--rotate-x',type=float,default=0.0)
    imp.add_argument('--rotate-y',type=float,default=0.0)
    imp.add_argument('--rotate-z',type=float,default=0.0)
    imp.add_argument('--scale',type=float,default=1.0)
    imp.add_argument('--overwrite',action='store_true')
    isvg=sub.add_parser('import-svg',help='copy an SVG into objects/ and create a 3-D wire preset')
    isvg.add_argument('file')
    isvg.add_argument('--as',dest='as_name',help='object slug under objects/ (default: source filename)')
    isvg.add_argument('--name',help='display name')
    isvg.add_argument('--spin-axis',choices=('x','y','z'),default='y')
    isvg.add_argument('--rotate-x',type=float,default=0.0); isvg.add_argument('--rotate-y',type=float,default=0.0); isvg.add_argument('--rotate-z',type=float,default=0.0)
    isvg.add_argument('--scale',type=float,default=1.0)
    isvg.add_argument('--color',default='auto',help='C64 colour name/index, or auto to map from SVG stroke/fill')
    isvg.add_argument('--animation',choices=('spin','recede','crawl'),default='spin')
    isvg.add_argument('--animation-tilt',type=float,default=62.0)
    isvg.add_argument('--animation-travel',type=float,default=120.0)
    isvg.add_argument('--animation-rise',type=float,default=54.0)
    isvg.add_argument('--svg-tolerance',type=float,default=3.0)
    isvg.add_argument('--svg-curve-step',type=float,default=12.0)
    isvg.add_argument('--svg-depth',type=float,default=5.0)
    isvg.add_argument('--svg-connector-stride',type=int,default=4)
    isvg.add_argument('--overwrite',action='store_true')
    ge=sub.add_parser('generate-examples',help='compile bundled reference PRGs into examples/')
    _add_toolchain_args(ge,settings)
    doc=sub.add_parser('doctor',help='check local 64tass/VICE toolchain availability')
    _add_toolchain_args(doc,settings)
    sub.add_parser('list-shapes',help='list procedural/built-in shapes')
    sub.add_parser('list-objects',help='list imported OBJ/SVG presets in objects/')
    return p


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    config_path,config_explicit,config_disabled=config_request(argv,ROOT)
    try:
        settings=load_toolchain_settings(config_path,require=config_explicit and not config_disabled)
    except (OSError,ValueError) as e:
        print(f'error: could not load toolchain config: {e}',file=sys.stderr)
        return 2
    p=make_parser(settings)
    if not argv:
        argv=['build']
    elif argv[0]=='--generate-examples':
        argv=['generate-examples']+argv[1:]
    elif argv[0].startswith('-') and argv[0] not in ('-h','--help','--version'):
        argv=['build']+argv
    a=p.parse_args(argv)
    if hasattr(a,'tass_args') and a.tass_args is None:
        a.tass_args=[] if getattr(a,'no_tass_default_args',False) else list(settings.tass_args)
    if hasattr(a,'vice_args') and a.vice_args is None:
        a.vice_args=[] if getattr(a,'no_vice_default_args',False) else list(settings.vice_args)
    a._tool_config_path=settings.config_path
    a._tool_platform=settings.platform_key
    a._config_disabled=config_disabled
    if a.command=='list-shapes':
        print('torus       procedural; --major-segments/--minor-segments, --polycount or --vertices')
        print('cube        built-in 8-vertex cube')
        print('sphere      procedural; --lat-segments/--lon-segments, --polycount or --vertices')
        print('horse_head  compatibility alias for --object horse_head')
        return 0
    if a.command=='generate-examples': return cmd_generate_examples(a)
    if a.command=='doctor': return cmd_doctor(a)
    if a.command=='list-objects': return cmd_list_objects()
    if a.command=='import-obj': return cmd_import_obj(a)
    if a.command=='import-svg': return cmd_import_svg(a)
    if a.command=='inspect': return cmd_inspect(a)
    return cmd_build(a)
