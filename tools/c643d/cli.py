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
from .assets import load_object_preset, list_object_presets, import_obj_asset
from .pipeline import Camera, fit_scale, build_frames, classify_feature_edges
from .emit import emit_tables, emit_hud

ROOT=Path(__file__).resolve().parents[2]
OBJECTS=ROOT/'objects'; GENERATED=ROOT/'generated'; BUILD=ROOT/'build'; C64=ROOT/'c64'; EXAMPLES=ROOT/'examples'
RENDERERS={'step':'renderer-step.asm','bytechunk':'renderer-bytechunk.asm','yunroll':'renderer-yunroll.asm'}


def preflight(*, tass_name='64tass', vice_name='x64sc', need_assemble=True, need_run=False, verbose=True):
    tass=shutil.which(tass_name)
    vice=shutil.which(vice_name)
    ok=True
    if need_assemble and not tass:
        print(f'error: 64tass not found as {tass_name!r}; install 64tass or pass --tass PATH.', file=sys.stderr)
        ok=False
    elif verbose and tass:
        print(f'preflight: 64tass = {tass}')
    if need_run and not vice:
        print(f'error: VICE C64 emulator not found as {vice_name!r}; install VICE or pass --vice PATH.', file=sys.stderr)
        ok=False
    elif not vice and verbose:
        print(f'warning: VICE C64 emulator {vice_name!r} not found; PRG build is still available, but --run will fail.', file=sys.stderr)
    elif verbose and vice:
        print(f'preflight: VICE = {vice}')
    return ok,tass,vice


def cmd_doctor(a):
    ok,_,_=preflight(tass_name=a.tass,vice_name=a.vice,need_assemble=True,need_run=False,verbose=True)
    print(f'python:    {sys.executable} ({sys.version.split()[0]})')
    print(f'objects:   {OBJECTS}')
    print(f'examples:  {EXAMPLES}')
    return 0 if ok else 2


def cmd_generate_examples(a):
    ok,tass,_=preflight(tass_name=a.tass,vice_name=a.vice,need_assemble=True,need_run=False,verbose=True)
    if not ok:
        return 2
    manifest=EXAMPLES/'examples.json'
    specs=json.loads(manifest.read_text(encoding='utf-8'))
    EXAMPLES.mkdir(parents=True,exist_ok=True)
    print(f'generating {len(specs)} example PRGs -> {EXAMPLES.relative_to(ROOT)}/')
    for spec in specs:
        name=spec['name']; args=list(spec['args'])
        cmd=[sys.executable,str(ROOT/'c643d.py'),'build',*args,'--output',name,'--tass',a.tass,'--vice',a.vice]
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


def build_mesh(a) -> tuple[Mesh,str,str,str,float,float]:
    """Return mesh, display label, spin axis, visibility mode, Z tolerance and feature angle."""
    preset_rotate=(0.0,0.0,0.0); preset_scale=1.0; spin_axis='y'; preset_visibility='auto'; preset_ztol=0.0008; preset_feature_angle=40.0
    if a.obj:
        p=Path(a.obj); mesh=load_obj(p,a.name or p.stem); label=(a.name or p.stem).upper()
        mesh=_apply_up_axis(mesh,a.obj_up)
    elif a.object or a.shape=='horse_head':
        slug=a.object or 'horse_head'
        preset=load_object_preset(OBJECTS,slug)
        mesh=load_obj(preset.obj_path,preset.name); label=(a.name or preset.name).upper()
        mesh=_apply_up_axis(mesh,preset.up_axis)
        preset_rotate=preset.rotate; preset_scale=preset.scale; spin_axis=preset.spin_axis; preset_visibility=preset.visibility; preset_ztol=preset.z_tolerance; preset_feature_angle=preset.feature_angle
    elif a.shape=='cube':
        mesh=cube(); label='CUBE'
    elif a.shape=='sphere':
        lat,lon=_choose_detail(a,'sphere')
        mesh=sphere(lat,lon); label='SPHERE'
    else:
        major,minor=_choose_detail(a,'torus')
        mesh=torus(major,minor); label='TORUS'

    # Normalize imported and built-in meshes to the same object-space budget.
    # The torus already uses the historical radii but normalizing it too makes
    # arbitrary detail settings and future shapes behave consistently.
    mesh=normalize_mesh(mesh,46.0)

    if not a.keep_winding:
        mesh=fix_winding_outward(mesh)

    prx,pry,prz=(math.radians(v) for v in preset_rotate)
    mesh=transform_mesh(mesh,rx=prx,ry=pry,rz=prz,scale=preset_scale)

    rx=math.radians(a.rotate_x); ry=math.radians(a.rotate_y); rz=math.radians(a.rotate_z)
    # Historical torus tilt, retained as the reference benchmark pose.
    if a.shape=='torus' and not a.obj and not a.object and a.rotate_x==0.0:
        rx=math.radians(28.0)
    mesh=transform_mesh(mesh,rx=rx,ry=ry,rz=rz,scale=a.scale)
    mesh.name=label
    requested_visibility=getattr(a,'visibility','auto')
    if requested_visibility=='auto':
        if preset_visibility!='auto': visibility=preset_visibility
        elif a.obj or a.object or a.shape=='horse_head': visibility='surface'
        else: visibility='frontface'
    else:
        visibility=requested_visibility
    ztol=getattr(a,'z_tolerance',None)
    if ztol is None: ztol=preset_ztol if (a.obj or a.object or a.shape=='horse_head') else 0.0008
    feature_angle=getattr(a,'feature_angle',None)
    if feature_angle is None: feature_angle=preset_feature_angle
    return mesh,label,(a.spin_axis or spin_axis),visibility,float(ztol),float(feature_angle)


def prepare_asm(renderer:str,frames:int) -> Path:
    src=(C64/RENDERERS[renderer]).read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {frames}',1)
    src=src.replace('.include "generated/hud.inc"', '.include "../generated/hud.inc"')
    src=src.replace('.include "generated/tables.inc"', '.include "../generated/tables.inc"')
    out=BUILD/'main.asm'; out.write_text(src)
    return out


def print_stats(mesh:Mesh,label:str,renderer:str,scale:float,stats:dict,hud:str,spin_axis:str,visibility:str,z_tolerance:float,feature_angle:float):
    print(f'shape:      {label}')
    print(f'vertices:   {len(mesh.vertices)}')
    print(f'edges:      {len(mesh.edges)}')
    print(f'faces:      {len(mesh.faces)}')
    d=mesh_diagnostics(mesh)
    if d['boundary_edges'] or d['nonmanifold_edges']:
        print(f'topology:   boundary {d["boundary_edges"]}; non-manifold {d["nonmanifold_edges"]}')
    print(f'renderer:   {renderer}')
    print(f'spin axis:  {spin_axis}')
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
    ok,tass_found,vice_found=preflight(tass_name=a.tass,vice_name=a.vice,need_assemble=not a.no_assemble,need_run=a.run,verbose=True)
    if not ok: return 2
    GENERATED.mkdir(exist_ok=True); BUILD.mkdir(exist_ok=True); OBJECTS.mkdir(exist_ok=True)
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle=build_mesh(a)
    cam=Camera(distance=a.camera,focal=a.focal,cx=128.0,cy=72.0)
    fitted=fit_scale(mesh,a.frames,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=spin_axis) if not a.no_auto_fit else 1.0
    mesh=transform_mesh(mesh,scale=fitted)

    frame_candidates=[a.frames]
    if not a.strict_frames:
        for n in (40,36,32,28,24,20,16,12,8):
            if n<a.frames and n not in frame_candidates: frame_candidates.append(n)
    last_error=None
    for actual_frames in frame_candidates:
        frames,candidate_edges=build_frames(mesh,actual_frames,cam,spin_axis=spin_axis,visibility_mode=visibility,z_tolerance=z_tolerance,feature_angle=feature_angle)
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
    asm=prepare_asm(a.renderer,actual_frames)
    subprocess.run([sys.executable,str(ROOT/'tools'/'asm_sanity.py'),str(asm)],cwd=ROOT,check=True)
    print_stats(mesh,label,a.renderer,fitted,stats,hud,spin_axis,visibility,z_tolerance,feature_angle)
    outname=a.output or f'{label.lower().replace(" ","_")}-{a.renderer}'
    outdir=Path(a.output_dir).resolve() if getattr(a,'output_dir',None) else BUILD
    outdir.mkdir(parents=True,exist_ok=True)
    prg=outdir/f'{outname}.prg'; lbl=outdir/f'{outname}.lbl'; lst=outdir/f'{outname}.lst'
    if a.no_assemble:
        print(f'generated assembler: {asm}')
        return 0
    tass=tass_found or shutil.which(a.tass)
    cmd=[tass,'--cbm-prg','--vice-labels','-l',str(lbl),'-L',str(lst),'-o',str(prg),str(asm)]
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
    print(f'built {prg.relative_to(ROOT)}')
    if a.run:
        vice=vice_found or shutil.which(a.vice)
        subprocess.run([vice,str(prg)],cwd=ROOT,check=False)
    return 0


def _print_mesh_report(label:str,mesh:Mesh):
    d=mesh_diagnostics(mesh)
    fs=', '.join(f'{n}-gon:{count}' for n,count in sorted(d['face_sizes'].items()))
    print(f'{label}: {d["vertices"]} vertices, {d["edges"]} edges, {d["faces"]} faces')
    print(f'face mix: {fs}')
    print(f'boundary edges: {d["boundary_edges"]}; non-manifold edges: {d["nonmanifold_edges"]}; isolated vertices: {d["isolated_vertices"]}')


def cmd_inspect(a):
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle=build_mesh(a)
    _print_mesh_report(label,mesh)
    print(f'spin axis: {spin_axis}')
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


def cmd_list_objects():
    presets=list_object_presets(OBJECTS)
    if not presets:
        print('(no imported objects)'); return 0
    for p in presets:
        mtl=(' mtl='+','.join(p.materials)) if p.materials else ''
        print(f'{p.slug:20} {p.name:20} up={p.up_axis} spin={p.spin_axis} file={p.obj_path.name}{mtl}')
    return 0


def make_parser():
    p=argparse.ArgumentParser(prog='c643d',description='C64 3D wireframe compiler/toolkit (WIP)')
    p.add_argument('--version',action='version',version=__version__)
    sub=p.add_subparsers(dest='command')
    def common(q):
        q.add_argument('--shape',choices=('torus','cube','sphere','horse_head'),default='torus')
        q.add_argument('--object',help='build a named object preset from objects/<name>.obj + optional .json metadata')
        q.add_argument('--obj',help='load a one-off arbitrary Wavefront OBJ instead of --shape')
        q.add_argument('--obj-up',choices=('y','z'),default='y',help='source up axis for one-off --obj')
        q.add_argument('--name',help='display/object name for custom OBJ')
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
        q.add_argument('--keep-winding',action='store_true',help='do not best-effort reorient mesh face winding')
        q.add_argument('--visibility',choices=('auto','surface_features','surface_creases','surface','frontface'),default='auto',help='hidden-line surface mode; auto uses robust surface Z-buffer for OBJ and front-face mode for procedural closed meshes')
        q.add_argument('--z-tolerance',type=float,help='reciprocal-depth tolerance for visible wire edges; OBJ presets may provide a default')
        q.add_argument('--feature-angle',type=float,help='surface_creases threshold in degrees; sharp manifold edges at/above this angle are preserved')
    b=sub.add_parser('build',help='generate tables, assemble PRG, optionally run VICE'); common(b)
    b.add_argument('--renderer',choices=tuple(RENDERERS),default='yunroll',help='step=v0.7, bytechunk=v0.8, yunroll=current fastest')
    b.add_argument('--frames',type=int,default=48,help='precomputed spin orientations (default 48)')
    b.add_argument('--strict-frames',action='store_true',help='fail instead of reducing orientation count when table RAM overflows')
    b.add_argument('--camera',type=float,default=110.0)
    b.add_argument('--focal',type=float,default=180.0)
    b.add_argument('--margin',type=int,default=4)
    b.add_argument('--max-fit-scale',type=float,default=1.4)
    b.add_argument('--no-auto-fit',action='store_true')
    b.add_argument('--output',help='output basename')
    b.add_argument('--output-dir',help='directory for PRG/LBL/LST outputs (default: build/)')
    b.add_argument('--tass',default='64tass')
    b.add_argument('--vice',default='x64sc')
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
    ge=sub.add_parser('generate-examples',help='compile bundled reference PRGs into examples/')
    ge.add_argument('--tass',default='64tass'); ge.add_argument('--vice',default='x64sc')
    doc=sub.add_parser('doctor',help='check local 64tass/VICE toolchain availability')
    doc.add_argument('--tass',default='64tass'); doc.add_argument('--vice',default='x64sc')
    sub.add_parser('list-shapes',help='list procedural/built-in shapes')
    sub.add_parser('list-objects',help='list OBJ presets in objects/')
    return p


def main(argv=None):
    p=make_parser(); argv=list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv=['build']
    elif argv[0]=='--generate-examples':
        argv=['generate-examples']+argv[1:]
    elif argv[0].startswith('-') and argv[0] not in ('-h','--help','--version'):
        argv=['build']+argv
    a=p.parse_args(argv)
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
    if a.command=='inspect': return cmd_inspect(a)
    return cmd_build(a)
