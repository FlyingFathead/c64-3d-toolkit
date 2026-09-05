from __future__ import annotations
import argparse, json, math, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from . import __version__
from .mesh import Mesh, normalize_mesh, transform_mesh, fix_winding_outward, mesh_diagnostics
from .shapes import (
    torus, cube, sphere, choose_torus_segments, choose_sphere_segments,
    choose_torus_segments_by_vertices, choose_sphere_segments_by_vertices,
)
from .objio import load_obj
from .svgio import load_svg
from .colors import c64_color_index, c64_color_name
from .assets import load_object_preset, list_object_presets, import_obj_asset, import_svg_asset
from .pipeline import Camera, fit_scale, build_frames, build_scene_frames, classify_feature_edges
from .sceneio import load_scene
from .blender import export_blend_scene, probe_blender, require_blender
from .emit import emit_tables, emit_hud
from .toolchain import (
    command as tool_command, config_request, load_toolchain_settings,
    resolve_executable,
)
from .checksums import compare_prg, load_checksum_manifest, reference_set
from .cartridge import (
    assemble_smoke_bootstrap, build_smoke_raw, check_easyflash_crt,
    convert_easyflash, write_manifest, write_smoke_map,
    assemble_demo_boot, assemble_demo_control, assemble_demo_runtime, install_demo_boot,
    build_menu_charset, pack_demo_prgs, write_demo_include, write_demo_map,
    DEMO_MENU_STYLE_ORDER,
)

ROOT=Path(__file__).resolve().parents[2]
OBJECTS=ROOT/'objects'; GENERATED=ROOT/'generated'; BUILD=ROOT/'build'; C64=ROOT/'c64'; EXAMPLES=ROOT/'examples'
CART_DEMOS=EXAMPLES/'cart_demos'
CHECKSUM_MANIFEST=ROOT/'tests'/'data'/'golden_prg_checksums.json'
CART=C64/'cart'
RENDERERS={'step':'renderer-step.asm','bytechunk':'renderer-bytechunk.asm','yunroll':'renderer-yunroll.asm'}
CARTRIDGE_RENDERERS={'yunroll-cart':'renderer-yunroll-cart.asm'}
NO_OVERLAY_RENDERERS={name:f'variants/renderer-{name}-no-overlay.asm' for name in RENDERERS}
RASTERTIME_RENDERERS={'yunroll':'debug/renderer-yunroll-rastertime.asm'}


CARTRIDGE_DEMO_ENTRIES=(
    ('TORUS', EXAMPLES/'torus'/'torus.prg'),
    ('TORUS DENSE', EXAMPLES/'torus_dense'/'torus_dense.prg'),
    ('CUBE', EXAMPLES/'cube'/'cube.prg'),
    ('SPHERE', EXAMPLES/'sphere'/'sphere.prg'),
    ('HORSE HEAD', EXAMPLES/'horse_head'/'horse_head.prg'),
    ('SUNFLOWER TORUS', EXAMPLES/'sunflower_torus'/'sunflower_torus.prg'),
    ('SUNFLOWER COLOR', EXAMPLES/'sunflower_torus'/'sunflower_torus_color.prg'),
    ('SPACE HORSE SPIN', EXAMPLES/'space_horse_spin'/'space_horse_spin_color.prg'),
    ('SPACE HORSE CRAWL', EXAMPLES/'space_horse_crawl'/'space_horse_crawl_color.prg'),
    ('FALLING CUBES', EXAMPLES/'blender_falling_cubes'/'falling_cubes_c64_color-yunroll.prg'),
)


def _executable_version(executable:str) -> str | None:
    try:
        completed=subprocess.run(
            [executable,'--version'],capture_output=True,text=True,check=False,timeout=15,
        )
    except (OSError,subprocess.TimeoutExpired):
        return None
    lines=[line.strip() for line in (completed.stdout+'\n'+completed.stderr).splitlines() if line.strip()]
    return lines[0] if lines else None


def _cartconv_version(executable:str) -> str | None:
    """cartconv 3.10 prints a harmless filename error before --version."""
    try:
        completed=subprocess.run(
            [executable,'--version'],capture_output=True,text=True,check=False,timeout=15,
        )
    except (OSError,subprocess.TimeoutExpired):
        return None
    lines=[line.strip() for line in (completed.stdout+'\n'+completed.stderr).splitlines() if line.strip()]
    for line in lines:
        if line.lower().startswith('cartconv '):
            return line
    return lines[-1] if lines else None


def require_cartconv(spec:str, *, verbose:bool=True) -> str | None:
    found=resolve_executable(spec,'cartconv')
    if not found:
        print(
            f'error: EasyFlash cartridge output requires cartconv, but it was not found as {spec!r}.',
            file=sys.stderr,
        )
        print('Install VICE/cartconv, configure cartconv in config/c643d.ini, or pass --cartconv PATH.',file=sys.stderr)
        print('Normal .prg builds do not require cartconv.',file=sys.stderr)
        return None
    if verbose:
        version=_cartconv_version(found)
        print(f'preflight: cartconv = {found}{f" ({version})" if version else " (version unavailable)"}')
    return found


def preflight(*, tass_name='64tass', vice_name='x64sc', tass_args=(), vice_args=(), need_assemble=True, need_run=False, verbose=True):
    tass=resolve_executable(tass_name,'tass')
    vice=resolve_executable(vice_name,'vice')
    ok=True
    if need_assemble and not tass:
        print(f'error: 64tass not found as {tass_name!r}; install 64tass, configure config/c643d.ini, or pass --tass PATH.', file=sys.stderr)
        ok=False
    elif verbose and tass:
        version=_executable_version(tass)
        print(f'preflight: 64tass = {tass}{f" ({version})" if version else " (version unavailable)"}')
        if tass_args: print(f'preflight: 64tass args = {" ".join(tass_args)}')
    if need_run and not vice:
        print(f'error: VICE C64 emulator not found as {vice_name!r}; install VICE, configure config/c643d.ini, or pass --vice PATH.', file=sys.stderr)
        if sys.platform=='darwin':
            print('hint: downloaded macOS VICE packages commonly use a path such as /Applications/vice-arm64-gtk3-3.8/bin/x64sc; use the directory name of your installed package.', file=sys.stderr)
        ok=False
    elif not vice and verbose:
        print(f'warning: VICE C64 emulator {vice_name!r} not found; PRG build is still available, but --run will fail.', file=sys.stderr)
        if sys.platform=='darwin':
            print('hint: macOS users can use Homebrew (brew install vice) or set vice to the installed package bin/x64sc path in config/c643d.ini.', file=sys.stderr)
    elif verbose and vice:
        version=_executable_version(vice)
        print(f'preflight: VICE = {vice}{f" ({version})" if version else " (version unavailable)"}')
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
    blender=resolve_executable(a.blender,'blender')
    if blender:
        try:
            blender_version=probe_blender(blender)
            print(f'blender:   {blender} ({blender_version}; bpy OK)')
        except RuntimeError as e:
            print(f'blender:   {blender} (bpy FAILED: {e})')
    else:
        print('blender:   not found (optional; required only for --blend)')
    cartconv=resolve_executable(a.cartconv,'cartconv')
    if cartconv:
        version=_cartconv_version(cartconv)
        print(f'cartconv:  {cartconv}{f" ({version})" if version else ""}')
    else:
        print('cartconv:  not found (optional; required only for cartridge/.crt builds)')
    return 0 if ok else 2


def _example_variants(mode:str):
    # Golden example builds are intentionally independent of local render
    # defaults. Toolchain paths/arguments may come from config, but viewport
    # and ASM variant selection are pinned here for deterministic PRGs.
    normal=[('', ['--text-overlay','--no-rastertime-profiler','--viewport-height','192'])]
    legacy144=[('_legacy144',['--text-overlay','--no-rastertime-profiler','--viewport-height','144'])]
    no_overlay=[('_no_overlay',['--no-text-overlay','--no-rastertime-profiler','--viewport-height','200'])]
    profiler=[('_rastertime_profiler',['--text-overlay','--rastertime-profiler','--viewport-height','192'])]
    if mode=='normal': return normal
    if mode=='legacy144': return legacy144
    if mode=='no-overlay': return no_overlay
    if mode=='rastertime-profiler': return profiler
    if mode=='all': return normal+legacy144+no_overlay+profiler
    raise ValueError(f'unknown example variant mode: {mode}')


def _load_example_reference(name:str|None):
    data=load_checksum_manifest(CHECKSUM_MANIFEST)
    selected,ref=reference_set(data,name)
    return data,selected,ref


def _print_checksum_result(path:Path,ref:dict,*,filename:str|None=None):
    result=compare_prg(path,ref,filename=filename)
    print(
        f'checksum:  {result["status"]:<8} {result["filename"]} '
        f'sha256={result["actual_sha256"]} size={result["actual_size"]}'
    )
    if result['status']=='CHANGED':
        print(f'           expected sha256={result["expected_sha256"]} size={result["expected_size"]}')
    return result['status']


def _example_manifest_path(a) -> Path:
    if getattr(a,'blender_only',False):
        return EXAMPLES/'blender_falling_cubes'/'examples.json'
    return EXAMPLES/'examples.json'


def _example_specs(a):
    manifest=_example_manifest_path(a)
    specs=json.loads(manifest.read_text(encoding='utf-8'))
    only=getattr(a,'only',None)
    if only:
        selected=[spec for spec in specs if spec['name']==only]
        if not selected:
            available=', '.join(x['name'] for x in specs)
            raise ValueError(f'unknown example {only!r} in {manifest.relative_to(ROOT)}; available: {available}')
        specs=selected
    return specs


def _install_example_prg(prg:Path, *, spec:dict, install:bool) -> None:
    if not install:
        return
    subdir=spec.get('directory')
    installed_dir=EXAMPLES/subdir if subdir else EXAMPLES
    installed_dir.mkdir(parents=True,exist_ok=True)
    installed=installed_dir/prg.name
    shutil.copy2(prg,installed)
    print(f'example: {installed.relative_to(ROOT)}')


def _assemble_profiler_from_current_tables(a, *, tass:str, output_root:Path, name:str) -> Path:
    """Assemble the profiler derivative from the immediately preceding normal build.

    Normal and raster-profiler variants intentionally use the same 192-line
    geometry. Reusing generated tables here avoids doing the expensive host-side
    visibility/projection pass twice while still assembling a distinct debug ASM
    and distinct PRG. The production renderer source is never modified.
    """
    current=(BUILD/'main.asm').read_text(encoding='utf-8')
    def number(pattern:str, label:str, base:int=10) -> int:
        match=re.search(pattern,current,re.MULTILINE)
        if not match:
            raise RuntimeError(f'could not recover {label} from current generated assembler')
        return int(match.group(1),base)
    frames=number(r'^FRAME_COUNT\s*=\s*(\d+)\s*$', 'FRAME_COUNT')
    screen=number(r'^SCREEN_COLOR\s*=\s*\$([0-9a-fA-F]+)\s*', 'SCREEN_COLOR',16)
    colors=number(r'^COLORS_ENABLED\s*=\s*(\d+)\b', 'COLORS_ENABLED')
    asm=prepare_asm('yunroll',frames,(screen>>4)&0x0f,bool(colors),text_overlay=True,rastertime_profiler=True)
    subprocess.run([sys.executable,str(ROOT/'tools'/'asm_sanity.py'),str(asm)],cwd=ROOT,check=True)
    prg=output_root/f'{name}.prg'; lbl=output_root/f'{name}.lbl'; lst=output_root/f'{name}.lst'
    cmd=tool_command(tass,a.tass_args,['--cbm-prg','--vice-labels','-l',str(lbl),'-L',str(lst),'-o',str(prg),str(asm)])
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
    print(f'built {_display_path(prg)} (reused 192-line geometry tables; debug ASM reassembled)')
    return prg


def _merge_manifest_variant_args(base_args:list[str], override_args:list[str]) -> list[str]:
    """Apply manifest variant overrides without emitting duplicate long options.

    Example manifests sometimes need one historical variant to override a base
    value (the Blender falling-cubes legacy build uses sample-step 3 while the
    current builds use 4).  Keep the generated command line unambiguous by
    replacing the earlier option/value pair instead of appending a duplicate.
    """
    result=list(base_args)
    i=0
    while i < len(override_args):
        token=override_args[i]
        has_value=i+1 < len(override_args) and not override_args[i+1].startswith('--')
        if token.startswith('--'):
            while token in result:
                pos=result.index(token)
                del result[pos]
                if has_value and pos < len(result) and not result[pos].startswith('--'):
                    del result[pos]
        result.append(token)
        if has_value:
            result.append(override_args[i+1])
            i+=2
        else:
            i+=1
    return result


def _run_example_build_command(a, *, spec:dict, variant_args:list[str], name:str, output_root:Path, extra_build_args=(), variant_suffix:str='') -> Path:
    args=_merge_manifest_variant_args(
        list(spec['args']),
        list(spec.get('variant_args',{}).get(variant_suffix,())),
    )
    cmd=[
        sys.executable,str(ROOT/'c643d.py'),'build',*args,*variant_args,*extra_build_args,
        '--output',name,'--output-dir',str(output_root),
        '--overwrite-policy','allow','--tass',a.tass,'--vice',a.vice,'--blender',a.blender,
    ]
    for extra in a.tass_args: cmd.append(f'--tass-arg={extra}')
    for extra in a.vice_args: cmd.append(f'--vice-arg={extra}')
    if getattr(a,'no_tass_default_args',False): cmd.append('--no-tass-default-args')
    if getattr(a,'no_vice_default_args',False): cmd.append('--no-vice-default-args')
    if getattr(a,'_config_disabled',False): cmd.append('--no-config')
    elif getattr(a,'_tool_config_path',None): cmd.extend(['--config',str(a._tool_config_path)])
    print('+',' '.join(cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)
    return output_root/f'{name}.prg'


def _run_example_batch(a,*,install:bool):
    ok,tass,_=preflight(tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,need_assemble=True,need_run=False,verbose=True)
    if not ok:
        return 2
    try:
        specs=_example_specs(a)
        _data,ref_name,ref=_load_example_reference(getattr(a,'reference_set',None))
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f'error: {e}',file=sys.stderr)
        return 2
    reproduce_reference=bool(getattr(a,'reproduce_reference',False))
    reference_overrides=tuple(ref.get('build_overrides',())) if reproduce_reference else ()
    if reproduce_reference and a.variants!='normal':
        print('error: --reproduce-reference requires --variants normal because historical build overrides describe the production reference lane',file=sys.stderr)
        return 2
    variants=_example_variants(a.variants)
    total=sum(len([v for v in variants if not spec.get('variants') or v[0] in spec['variants']]) for spec in specs)
    destination='examples/' if install else 'temporary build directory'
    suite='Blender-only' if getattr(a,'blender_only',False) else 'standard'
    print(f'{"generating" if install else "testing"} {total} {suite} example PRG build(s) -> {destination}')
    print(f'checksum reference: {ref_name} ({ref.get("version","unknown version")})')
    if reproduce_reference:
        if reference_overrides:
            print(f'reference build overrides: {" ".join(reference_overrides)}')
        else:
            print('reference build overrides: (none recorded)')
    summary={'MATCHING':0,'CHANGED':0,'ABSENT':0}
    with tempfile.TemporaryDirectory(prefix='c643d-example-test-') as td:
        # Always assemble into a temporary directory. generate-examples copies
        # only the runnable PRG into examples/, keeping assembler LBL/LST files
        # out of the reference-output directory.
        output_root=Path(td)
        for spec in specs:
            variant_map={suffix:args for suffix,args in variants if not spec.get('variants') or suffix in spec['variants']}
            built={}

            # Normal first. With `all`, its generated 192-line geometry can be
            # reused for the profiler derivative before no-overlay replaces it.
            if '' in variant_map:
                name=spec['name']
                print(f'\n== {name} ==')
                prg=_run_example_build_command(a,spec=spec,variant_args=variant_map[''],name=name,output_root=output_root,extra_build_args=reference_overrides,variant_suffix='')
                built['']=prg
                _install_example_prg(prg,spec=spec,install=install)
                status=_print_checksum_result(prg,ref); summary[status]+=1

            profiler_suffix='_rastertime_profiler'
            if profiler_suffix in variant_map:
                name=spec['name']+profiler_suffix
                print(f'\n== {name} ==')
                can_reuse=(
                    '' in built
                    and '--renderer' in spec['args']
                    and spec['args'][spec['args'].index('--renderer')+1]=='yunroll'
                )
                if can_reuse:
                    prg=_assemble_profiler_from_current_tables(a,tass=tass,output_root=output_root,name=name)
                else:
                    prg=_run_example_build_command(a,spec=spec,variant_args=variant_map[profiler_suffix],name=name,output_root=output_root,variant_suffix=profiler_suffix)
                _install_example_prg(prg,spec=spec,install=install)
                status=_print_checksum_result(prg,ref); summary[status]+=1

            legacy_suffix='_legacy144'
            if legacy_suffix in variant_map:
                name=spec['name']+legacy_suffix
                print(f'\n== {name} ==')
                prg=_run_example_build_command(a,spec=spec,variant_args=variant_map[legacy_suffix],name=name,output_root=output_root,variant_suffix=legacy_suffix)
                _install_example_prg(prg,spec=spec,install=install)
                status=_print_checksum_result(prg,ref); summary[status]+=1

            no_suffix='_no_overlay'
            if no_suffix in variant_map:
                name=spec['name']+no_suffix
                print(f'\n== {name} ==')
                prg=_run_example_build_command(a,spec=spec,variant_args=variant_map[no_suffix],name=name,output_root=output_root,variant_suffix=no_suffix)
                _install_example_prg(prg,spec=spec,install=install)
                status=_print_checksum_result(prg,ref); summary[status]+=1

    print('\nchecksum summary: '
          f'{summary["MATCHING"]} MATCHING, {summary["CHANGED"]} CHANGED, '
          f'{summary["ABSENT"]} ABSENT; {sum(summary.values())} total')
    return 0

def cmd_generate_examples(a):
    return _run_example_batch(a,install=True)


def cmd_test_examples(a):
    return _run_example_batch(a,install=False)


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
    preset_color='white'; preset_use_colors=True
    preset_animation='spin'; preset_anim_tilt=62.0; preset_anim_travel=120.0; preset_anim_rise=54.0
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
        preset_color=preset.color; preset_use_colors=preset.use_colors
        preset_animation=preset.animation; preset_anim_tilt=preset.animation_tilt
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
    ignore_colors=getattr(a,'ignore_colors',False) or not preset_use_colors
    use_source_colors=bool(mesh.has_source_colors and not ignore_colors and requested_color is None)
    if requested_color is not None:
        color_value=requested_color
    elif ignore_colors:
        color_value='white'
    else:
        color_value=preset_color
    per_cell_colors=False
    if use_source_colors:
        effective_colors=set(mesh.source_colors)
        if not mesh.source_colors_cover_all_edges:
            effective_colors.add(c64_color_index(color_value))
        per_cell_colors=len(effective_colors)>1
        if not per_cell_colors:
            # A one-colour OBJ/SVG uses the original global hires foreground
            # byte: same result, no colour table or runtime update cost.
            color_value=next(iter(effective_colors))
    color_name=c64_color_name(c64_color_index(color_value))
    animation=getattr(a,'animation',None) or preset_animation
    anim_tilt=getattr(a,'animation_tilt',None); anim_tilt=preset_anim_tilt if anim_tilt is None else anim_tilt
    anim_travel=getattr(a,'animation_travel',None); anim_travel=preset_anim_travel if anim_travel is None else anim_travel
    anim_rise=getattr(a,'animation_rise',None); anim_rise=preset_anim_rise if anim_rise is None else anim_rise
    return mesh,label,(a.spin_axis or spin_axis),visibility,float(ztol),float(feature_angle),color_name,use_source_colors,per_cell_colors,animation,float(anim_tilt),float(anim_travel),float(anim_rise)


def prepare_asm(renderer:str,frames:int,color_index:int=1,colors_enabled:bool=False, *,
                text_overlay:bool=True,rastertime_profiler:bool=False) -> Path:
    if rastertime_profiler:
        if renderer not in RASTERTIME_RENDERERS:
            raise ValueError(
                f'raster-time profiler is currently available only for '
                f'{", ".join(RASTERTIME_RENDERERS)}'
            )
        source=RASTERTIME_RENDERERS[renderer]
    elif not text_overlay:
        source=NO_OVERLAY_RENDERERS[renderer]
    else:
        source=RENDERERS[renderer]
    src=(C64/source).read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {frames}',1)
    src=src.replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${color_index:X}0',1)
    src=src.replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(colors_enabled)}',1)
    src=src.replace('.include "generated/hud.inc"', '.include "../generated/hud.inc"')
    src=src.replace('.include "generated/tables.inc"', '.include "../generated/tables.inc"')
    out=BUILD/'main.asm'; out.write_text(src)
    return out


def default_output_basename(label:str,renderer:str,use_source_colors:bool, *,
                            text_overlay:bool=True,rastertime_profiler:bool=False) -> str:
    slug=label.lower().replace(' ','_')
    name=f'{slug}{"_color" if use_source_colors else ""}-{renderer}'
    if rastertime_profiler:
        return name+'_rastertime_profiler'
    if not text_overlay:
        return name+'_no_overlay'
    return name


def _viewport_height(a) -> int:
    explicit=getattr(a,'viewport_height',None)
    if explicit is not None:
        return int(explicit)
    return 200 if not getattr(a,'text_overlay',True) else 192


def _display_path(path:Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _check_overwrite(paths,policy:str) -> bool:
    existing=[Path(path) for path in paths if Path(path).exists()]
    if not existing or policy=='allow':
        return True
    listing=', '.join(_display_path(path) for path in existing)
    if policy=='error':
        print(f'error: refusing to overwrite existing output(s): {listing}',file=sys.stderr)
        return False
    print(f'warning: overwriting existing output(s): {listing}',file=sys.stderr)
    return True


def _selected_source_path(a) -> Path | None:
    if getattr(a,'svg',None):
        return Path(a.svg)
    if getattr(a,'obj',None):
        return Path(a.obj)
    slug=getattr(a,'object',None) or ('horse_head' if getattr(a,'shape',None)=='horse_head' else None)
    if slug:
        return load_object_preset(OBJECTS,slug).obj_path
    return None


def color_build_notice(mesh:Mesh,source:Path|None,color_name:str,use_source_colors:bool,
                       per_cell_colors:bool,*,forced:bool=False,disabled:bool=False) -> str | None:
    """Describe the selected colour path before expensive frame generation."""
    if source is None:
        return None
    if forced:
        return f'color: forced C64 {color_name}; using single-color pipeline'
    if not mesh.has_source_colors:
        if source.suffix.lower()=='.obj':
            layer='MTL color layer'
            where=f'for {source.name}'
        else:
            layer='SVG stroke/fill color layer'
            where=f'in {source.name}'
        default='monochrome default' if color_name=='white' else 'single-color'
        return f'color: no usable {layer} found {where}; using {color_name} {default} pipeline'
    if disabled:
        return f'color: source colors disabled for {source.name}; using {color_name} monochrome pipeline'
    palette=', '.join(c64_color_name(index) for index in mesh.source_colors)
    if per_cell_colors:
        return f'color: source color layer found in {source.name}; mapping {palette} to VIC-II hires cells'
    return f'color: source color layer found in {source.name}; using {color_name} single-color fast path'


def print_stats(mesh:Mesh,label:str,renderer:str,scale:float,stats:dict,hud:str,spin_axis:str,visibility:str,z_tolerance:float,feature_angle:float,color_name:str,use_source_colors:bool,animation:str):
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
    if use_source_colors:
        palette=', '.join(c64_color_name(index) for index in mesh.source_colors)
        mode='per-cell VIC-II hires spans' if stats.get('colors_enabled') else 'global hires foreground'
        print(f'colors:     source -> {palette} ({mode})')
    else:
        print(f'color:      {color_name} (monochrome)')
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
    if stats.get('colors_enabled'):
        print(f'color map:  {stats["color_spans_min"]}..{stats["color_spans_max"]} spans/frame; {stats["color_table_bytes"]} table bytes')
        print(f'cell mixes: {stats["color_conflicts_min"]}..{stats["color_conflicts_max"]} cells/frame resolved by dominant visible colour')
    print(f'HUD:        {hud}')


def cmd_build(a):
    if a.renderer in ("yunroll-cart-v2", "yunroll-cart-v3", "yunroll-cart-v4"):
        from .cartstream import cmd_build_cart_v2
        return cmd_build_cart_v2(a)
    if getattr(a,'blend',None) or getattr(a,'scene',None):
        return cmd_build_scene(a)
    if getattr(a,'rastertime_profiler',False) and not getattr(a,'text_overlay',True):
        print('error: --rastertime-profiler and --no-text-overlay are separate ASM variants; select one',file=sys.stderr)
        return 2
    if getattr(a,'rastertime_profiler',False) and a.renderer not in RASTERTIME_RENDERERS:
        print(f'error: raster-time profiler is currently available only for {", ".join(RASTERTIME_RENDERERS)}',file=sys.stderr)
        return 2
    ok,tass_found,vice_found=preflight(tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,need_assemble=not a.no_assemble,need_run=a.run,verbose=True)
    if not ok: return 2
    GENERATED.mkdir(exist_ok=True); BUILD.mkdir(exist_ok=True); OBJECTS.mkdir(exist_ok=True)
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle,color_name,use_source_colors,per_cell_colors,animation,anim_tilt,anim_travel,anim_rise=build_mesh(a)
    source=_selected_source_path(a)
    notice=color_build_notice(
        mesh,source,color_name,use_source_colors,per_cell_colors,
        forced=getattr(a,'color',None) is not None,
        disabled=bool(getattr(a,'ignore_colors',False) or (mesh.has_source_colors and not use_source_colors)),
    )
    if notice:
        print(notice,flush=True)
    viewport_height=_viewport_height(a)
    cam=Camera(distance=a.camera,focal=a.focal,cx=128.0,cy=viewport_height/2.0)
    requested_frames=a.frames if a.frames is not None else 48
    fitted=fit_scale(mesh,requested_frames,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=spin_axis,animation=animation,animation_tilt=anim_tilt,animation_travel=anim_travel,animation_rise=anim_rise,height=viewport_height) if not a.no_auto_fit else 1.0
    mesh=transform_mesh(mesh,scale=fitted)

    frame_candidates=[requested_frames]
    if not a.strict_frames:
        for n in (40,36,32,28,24,20,16,12,8):
            if n<requested_frames and n not in frame_candidates: frame_candidates.append(n)
    last_error=None
    for actual_frames in frame_candidates:
        frames,candidate_edges=build_frames(mesh,actual_frames,cam,spin_axis=spin_axis,visibility_mode=visibility,z_tolerance=z_tolerance,feature_angle=feature_angle,animation=animation,animation_tilt=anim_tilt,animation_travel=anim_travel,animation_rise=anim_rise,enable_source_colors=per_cell_colors,fallback_color=c64_color_index(color_name),height=viewport_height)
        try:
            stats=emit_tables(GENERATED/'tables.inc',frames,a.renderer,candidate_edges)
            break
        except RuntimeError as e:
            if not any(k in str(e) for k in ('line tables reach','line tables need','clear tables reach','clear/colour tables reach','frame pointer tables reach')): raise
            last_error=e
            if a.strict_frames: raise
            print(f'note: table RAM: {actual_frames} orientations do not fit ({e}); trying fewer orientations; mesh detail unchanged')
    else:
        raise RuntimeError(f'could not fit generated tables: {last_error}')
    if actual_frames != requested_frames:
        print(f'table RAM auto-fit: orientations {requested_frames} -> {actual_frames}; mesh vertices/edges/faces preserved')
    hud=emit_hud(GENERATED/'hud.inc',label,len(mesh.vertices),len(mesh.edges)) if a.text_overlay else 'disabled'
    asm=prepare_asm(
        a.renderer,actual_frames,c64_color_index(color_name),stats['colors_enabled'],
        text_overlay=a.text_overlay,rastertime_profiler=a.rastertime_profiler,
    )
    subprocess.run([sys.executable,str(ROOT/'tools'/'asm_sanity.py'),str(asm)],cwd=ROOT,check=True)
    print_stats(mesh,label,a.renderer,fitted,stats,hud,spin_axis,visibility,z_tolerance,feature_angle,color_name,use_source_colors,animation)
    print(f'viewport:   256x{viewport_height} ({"text overlay" if a.text_overlay else "no text overlay; full bitmap height"})')
    if a.rastertime_profiler:
        print('profiler:   raster-time border profiler (debug ASM variant)')
    outname=a.output or default_output_basename(
        label,a.renderer,use_source_colors,
        text_overlay=a.text_overlay,rastertime_profiler=a.rastertime_profiler,
    )
    outdir=Path(a.output_dir).resolve() if getattr(a,'output_dir',None) else BUILD
    outdir.mkdir(parents=True,exist_ok=True)
    prg=outdir/f'{outname}.prg'; lbl=outdir/f'{outname}.lbl'; lst=outdir/f'{outname}.lst'
    if a.no_assemble:
        print(f'generated assembler: {asm}')
        return 0
    if not _check_overwrite((prg,lbl,lst),a.overwrite_policy):
        return 2
    tass=tass_found or resolve_executable(a.tass,'tass')
    cmd=tool_command(tass,a.tass_args,['--cbm-prg','--vice-labels','-l',str(lbl),'-L',str(lst),'-o',str(prg),str(asm)])
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
    print(f'built {_display_path(prg)}')
    if a.run:
        vice=vice_found or resolve_executable(a.vice,'vice')
        subprocess.run(tool_command(vice,a.vice_args,[str(prg)]),cwd=ROOT,check=False)
    return 0


def _scene_color_policy(mesh:Mesh,a):
    requested=getattr(a,'color',None)
    disabled=bool(getattr(a,'ignore_colors',False))
    use_source_colors=bool(mesh.has_source_colors and not disabled and requested is None)
    if requested is not None:
        color_name=c64_color_name(c64_color_index(requested))
    elif disabled or not mesh.has_source_colors:
        color_name='white'
    else:
        palette=mesh.source_colors
        color_name=c64_color_name(palette[0])
    per_cell_colors=use_source_colors and len(mesh.source_colors)>1
    return color_name,use_source_colors,per_cell_colors


def cmd_build_scene(a):
    if getattr(a,'rastertime_profiler',False) and not getattr(a,'text_overlay',True):
        print('error: --rastertime-profiler and --no-text-overlay are separate ASM variants; select one',file=sys.stderr)
        return 2
    if getattr(a,'rastertime_profiler',False) and a.renderer not in RASTERTIME_RENDERERS:
        print(f'error: raster-time profiler is currently available only for {", ".join(RASTERTIME_RENDERERS)}',file=sys.stderr)
        return 2
    viewport_height=_viewport_height(a)
    selected=sum(bool(x) for x in (a.blend,a.scene,a.obj,a.svg,a.object))
    if selected>1:
        print('error: --blend/--scene cannot be combined with --object, --obj, or --svg',file=sys.stderr)
        return 2
    if a.frames is not None:
        print('error: --frames is for generated legacy animations; use --frame-start/--frame-end/--sample-step with --blend',file=sys.stderr)
        return 2
    if not a.scene:
        try:
            blender_found,blender_version=require_blender(a.blender,system=getattr(a,'_tool_platform',None))
        except RuntimeError as e:
            print(str(e),file=sys.stderr)
            return 2
        print(f'preflight: Blender = {blender_found} ({blender_version}; bpy OK)')
    else:
        blender_found=None
    ok,tass_found,vice_found=preflight(
        tass_name=a.tass,vice_name=a.vice,tass_args=a.tass_args,vice_args=a.vice_args,
        need_assemble=not a.no_assemble,need_run=a.run,verbose=True,
    )
    if not ok:
        return 2
    GENERATED.mkdir(exist_ok=True); BUILD.mkdir(exist_ok=True)
    try:
        if a.scene:
            scene=load_scene(a.scene)
        else:
            with tempfile.TemporaryDirectory(prefix='c643d-blender-') as td:
                exported=Path(td)/'scene.c643dscene'
                export_blend_scene(
                    a.blend,exported,blender=blender_found,
                    frame_start=a.frame_start,frame_end=a.frame_end,
                    sample_step=a.sample_step,system=getattr(a,'_tool_platform',None),root=ROOT,
                    blender_is_verified=True,viewport_height=viewport_height,
                )
                scene=load_scene(exported)
    except (OSError,ValueError,RuntimeError) as e:
        print(f'error: {e}',file=sys.stderr)
        return 2
    if len(scene.frames)>255:
        print(f'error: scene has {len(scene.frames)} frames; maximum is 255',file=sys.stderr)
        return 2
    mesh=scene.mesh
    if a.name:
        mesh.name=a.name.upper()
    label=mesh.name
    visibility='surface' if a.visibility=='auto' else a.visibility
    z_tolerance=0.0008 if a.z_tolerance is None else float(a.z_tolerance)
    feature_angle=40.0 if a.feature_angle is None else float(a.feature_angle)
    color_name,use_source_colors,per_cell_colors=_scene_color_policy(mesh,a)
    palette=', '.join(c64_color_name(index) for index in mesh.source_colors) or '(none)'
    print(f'scene:      {Path(a.blend or a.scene).name}')
    print(f'sampling:   {len(scene.frames)} authored frames; source frames {scene.frames[0].source_frame}..{scene.frames[-1].source_frame}; step {scene.sample_step}')
    print(f'materials:  {palette}; {"source colours enabled" if use_source_colors else color_name+" monochrome"}',flush=True)
    try:
        frames,candidate_edges=build_scene_frames(
            scene,visibility_mode=visibility,z_tolerance=z_tolerance,
            feature_angle=feature_angle,enable_source_colors=per_cell_colors,
            fallback_color=c64_color_index(color_name),height=viewport_height,
        )
        stats=emit_tables(GENERATED/'tables.inc',frames,a.renderer,candidate_edges)
    except RuntimeError as e:
        message=str(e)
        if any(k in message for k in ('line tables reach','line tables need','clear tables reach','clear/colour tables reach','frame pointer tables reach')):
            print('error: Blender animation exceeds the safe C64 table-RAM area.',file=sys.stderr)
            print('',file=sys.stderr)
            print(f'  scene:       {Path(a.blend or a.scene).name}',file=sys.stderr)
            print(f'  samples:     {len(scene.frames)} frames (step {scene.sample_step})',file=sys.stderr)
            print(f'  viewport:    256x{viewport_height}',file=sys.stderr)
            print(f'  renderer:    {a.renderer}',file=sys.stderr)
            print(f'  colour:      {"source colours" if use_source_colors else color_name+" monochrome"}',file=sys.stderr)
            reach=re.search(r'tables reach \$(?P<end>[0-9a-fA-F]+), limit \$(?P<limit>[0-9a-fA-F]+)',message)
            need=re.search(r'line tables need (?P<need>\d+) bytes; available (?P<avail>\d+) bytes',message)
            if reach:
                end=int(reach.group('end'),16); limit=int(reach.group('limit'),16)
                print(f'  table end:   ${end:04x}',file=sys.stderr)
                print(f'  safe limit:  ${limit:04x}',file=sys.stderr)
                print(f'  overflow:    {end-limit} bytes',file=sys.stderr)
            elif need:
                required=int(need.group('need')); available=int(need.group('avail'))
                print(f'  required:    {required} bytes',file=sys.stderr)
                print(f'  available:   {available} bytes',file=sys.stderr)
                print(f'  overflow:    {required-available} bytes',file=sys.stderr)
            print('',file=sys.stderr)
            print(f'  detail:      {message}',file=sys.stderr)
            print('',file=sys.stderr)
            print('Nothing was assembled or overwritten.',file=sys.stderr)
            print('This is a Commodore 64 memory-layout limit, not a shortage of host RAM.',file=sys.stderr)
            next_step=max(2,int(scene.sample_step)+1)
            print('',file=sys.stderr)
            print('Try one or more of:',file=sys.stderr)
            print(f'  - increase --sample-step (for example {scene.sample_step} -> {next_step})',file=sys.stderr)
            print('  - shorten the animation with --frame-end',file=sys.stderr)
            print('  - reduce drawable scene geometry',file=sys.stderr)
            print('  - use a smaller --viewport-height',file=sys.stderr)
            print('Authored Blender frames are never silently discarded.',file=sys.stderr)
            return 2
        print(f'error: {message}',file=sys.stderr)
        return 2
    hud=emit_hud(GENERATED/'hud.inc',label,len(mesh.vertices),len(mesh.edges)) if a.text_overlay else 'disabled'
    asm=prepare_asm(
        a.renderer,len(frames),c64_color_index(color_name),stats['colors_enabled'],
        text_overlay=a.text_overlay,rastertime_profiler=a.rastertime_profiler,
    )
    subprocess.run([sys.executable,str(ROOT/'tools'/'asm_sanity.py'),str(asm)],cwd=ROOT,check=True)
    print_stats(
        mesh,label,a.renderer,1.0,stats,hud,'authored',visibility,z_tolerance,
        feature_angle,color_name,use_source_colors,'Blender scene',
    )
    print(f'viewport:   256x{viewport_height} ({"text overlay" if a.text_overlay else "no text overlay; full bitmap height"})')
    if a.rastertime_profiler:
        print('profiler:   raster-time border profiler (debug ASM variant)')
    outname=a.output or default_output_basename(
        label,a.renderer,use_source_colors,
        text_overlay=a.text_overlay,rastertime_profiler=a.rastertime_profiler,
    )
    outdir=Path(a.output_dir).resolve() if a.output_dir else BUILD
    outdir.mkdir(parents=True,exist_ok=True)
    prg=outdir/f'{outname}.prg'; lbl=outdir/f'{outname}.lbl'; lst=outdir/f'{outname}.lst'
    if a.no_assemble:
        print(f'generated assembler: {asm}')
        return 0
    if not _check_overwrite((prg,lbl,lst),a.overwrite_policy):
        return 2
    tass=tass_found or resolve_executable(a.tass,'tass')
    cmd=tool_command(tass,a.tass_args,['--cbm-prg','--vice-labels','-l',str(lbl),'-L',str(lst),'-o',str(prg),str(asm)])
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
    print(f'built {_display_path(prg)}')
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
    mesh,label,spin_axis,visibility,z_tolerance,feature_angle,color_name,use_source_colors,per_cell_colors,animation,anim_tilt,anim_travel,anim_rise=build_mesh(a)
    _print_mesh_report(label,mesh)
    print(f'spin axis: {spin_axis}')
    print(f'animation: {animation}; tilt={anim_tilt:g} travel={anim_travel:g} rise={anim_rise:g}')
    source_palette=', '.join(c64_color_name(index) for index in mesh.source_colors) or '(none)'
    print(f'source colors: {source_palette}')
    if use_source_colors:
        mode='per-cell source mapping' if per_cell_colors else f'{color_name} global source colour'
    else:
        mode=f'{color_name} monochrome'
    print(f'render colors: {mode}')
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
        scale=a.scale,use_colors=not a.ignore_colors,overwrite=a.overwrite,
    )
    print(f'imported:   {preset.obj_path.relative_to(ROOT)}')
    if preset.materials:
        print(f'materials:  {", ".join(preset.materials)}')
    palette=', '.join(c64_color_name(index) for index in mesh.source_colors) or '(none detected)'
    print(f'colors:     {palette}; {"ignored by preset" if a.ignore_colors else "enabled"}')
    print(f'metadata:   {(OBJECTS/(preset.slug+".json")).relative_to(ROOT)}')
    print(f'build with: ./build.sh --object {preset.slug} --run')
    return 0


def cmd_import_svg(a):
    source=Path(a.file)
    info=load_svg(source,a.name or source.stem,tolerance=a.svg_tolerance,curve_step=a.svg_curve_step,depth=a.svg_depth,connector_stride=a.svg_connector_stride)
    _print_mesh_report((a.name or source.stem).upper(),info.mesh)
    print(f'svg:        contours {info.contours}; points {info.source_points} -> {info.simplified_points}')
    pairs=', '.join(f'{source} -> {mapped}' for source,mapped in zip(info.source_colors,info.c64_colors))
    print(f'colors:     {pairs or "unknown -> C64 white"}')
    preset=import_svg_asset(
        source,OBJECTS,slug=a.as_name,display_name=a.name,spin_axis=a.spin_axis,
        rotate=(a.rotate_x,a.rotate_y,a.rotate_z),scale=a.scale,color=a.color,
        animation=a.animation,animation_tilt=a.animation_tilt,animation_travel=a.animation_travel,
        animation_rise=a.animation_rise,svg_tolerance=a.svg_tolerance,svg_curve_step=a.svg_curve_step,
        svg_depth=a.svg_depth,svg_connector_stride=a.svg_connector_stride,
        use_colors=not a.ignore_colors,overwrite=a.overwrite,
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
        color_mode='source' if p.use_colors else 'off'
        print(f'{p.slug:20} {p.name:20} spin={p.spin_axis} anim={p.animation} colors={color_mode} fallback={p.color} file={p.obj_path.name}{mtl}')
    return 0


def cmd_cartridge_smoke(a):
    """Build the deliberately small/measurable EasyFlash bank smoke test."""
    tass=resolve_executable(a.tass,'tass')
    if not tass:
        print(f'error: 64tass not found as {a.tass!r}; install 64tass, configure config/c643d.ini, or pass --tass PATH.',file=sys.stderr)
        return 2
    cartconv=require_cartconv(a.cartconv,verbose=True)
    if not cartconv:
        return 2
    vice=None
    if a.run:
        vice=resolve_executable(a.vice,'vice')
        if not vice:
            print(f'error: VICE C64 emulator not found as {a.vice!r}; install VICE, configure config/c643d.ini, or pass --vice PATH.',file=sys.stderr)
            return 2
    version=_executable_version(tass)
    print(f'preflight: 64tass = {tass}{f" ({version})" if version else " (version unavailable)"}')
    outdir=Path(a.output_dir).resolve() if a.output_dir else BUILD
    outdir.mkdir(parents=True,exist_ok=True)
    stem=a.output or 'easyflash-smoke'
    boot=outdir/f'{stem}-romh0.bin'
    raw=outdir/f'{stem}.bin'
    crt=outdir/f'{stem}.crt'
    labels=outdir/f'{stem}.lbl'
    listing=outdir/f'{stem}.lst'
    map_txt=outdir/f'{stem}-cart-map.txt'
    manifest_json=outdir/f'{stem}-cart-manifest.json'
    paths=(boot,raw,crt,labels,listing,map_txt,manifest_json)
    if not _check_overwrite(paths,a.overwrite_policy):
        return 2
    try:
        assemble_smoke_bootstrap(
            tass=tass,tass_args=a.tass_args,source=CART/'easyflash-smoke.asm',
            output=boot,labels=labels,listing=listing,cwd=ROOT,
        )
        raw_bytes,manifest=build_smoke_raw(boot.read_bytes())
        raw.write_bytes(raw_bytes)
        write_smoke_map(map_txt,manifest)
        write_manifest(manifest_json,manifest)
        convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name='C643D EF SMOKE',cwd=ROOT)
        check_output=check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=ROOT)
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as e:
        print(f'error: EasyFlash smoke build failed: {e}',file=sys.stderr)
        return 2
    print(f'built {_display_path(crt)}')
    print(f'raw:        {_display_path(raw)} (1 MiB EasyFlash interleaved image)')
    print(f'bank map:   {_display_path(map_txt)}')
    print(f'manifest:   {_display_path(manifest_json)}')
    if check_output:
        print(f'cartconv:   {check_output.splitlines()[-1]}')
    print('expected:   three lines: C643D EASYFLASH BANK 1/2/3 OK')
    if a.run:
        cmd=tool_command(vice,a.vice_args,['-cartcrt',str(crt)])
        print('+',' '.join(cmd))
        subprocess.run(cmd,cwd=ROOT,check=False)
    return 0



def cmd_cart_demos(a):
    from .cartuniform import build
    return build(a)

def cmd_cart_demos_legacy(a):
    """Build a menu-driven EasyFlash cartridge from the canonical example PRGs."""
    tass=resolve_executable(a.tass,'tass')
    if not tass:
        print(f'error: 64tass not found as {a.tass!r}; install 64tass, configure config/c643d.ini, or pass --tass PATH.',file=sys.stderr)
        return 2
    cartconv=require_cartconv(a.cartconv,verbose=True)
    if not cartconv:
        return 2
    vice=None
    if a.run:
        vice=resolve_executable(a.vice,'vice')
        if not vice:
            print(f'error: VICE C64 emulator not found as {a.vice!r}; install VICE, configure config/c643d.ini, or pass --vice PATH.',file=sys.stderr)
            return 2
    missing=[path for _,path in CARTRIDGE_DEMO_ENTRIES if not path.is_file()]
    if missing:
        print('error: cartridge demo requires the canonical example PRGs; missing:',file=sys.stderr)
        for path in missing:
            print(f'  {_display_path(path)}',file=sys.stderr)
        print('Run ./build.sh --generate-examples (and the Blender example build if needed), then retry.',file=sys.stderr)
        return 2
    version=_executable_version(tass)
    print(f'preflight: 64tass = {tass}{f" ({version})" if version else " (version unavailable)"}')

    outdir=Path(a.output_dir).resolve() if a.output_dir else CART_DEMOS
    outdir.mkdir(parents=True,exist_ok=True)
    stem=a.output or ('c643d-demo' if a.stream_renderer=='yunroll-cart-v2' else f'c643d-demo-v{__version__}-yunroll-cart-v3')
    workdir=BUILD/f'{stem}-cartridge-demo'
    workdir.mkdir(parents=True,exist_ok=True)
    include_dir=workdir/'generated'
    include_dir.mkdir(parents=True,exist_ok=True)
    include_path=include_dir/'cart-demo-data.inc'
    runtime=workdir/f'{stem}-runtime.bin'
    runtime_style_files={style:workdir/f'{stem}-runtime-{style}.bin' for style in DEMO_MENU_STYLE_ORDER}
    runtime_style_labels={style:workdir/f'{stem}-runtime-{style}.lbl' for style in DEMO_MENU_STYLE_ORDER}
    runtime_style_listings={style:workdir/f'{stem}-runtime-{style}.lst' for style in DEMO_MENU_STYLE_ORDER}
    control=workdir/f'{stem}-control.bin'
    control_lbl=workdir/f'{stem}-control.lbl'
    control_lst=workdir/f'{stem}-control.lst'
    menu_font=workdir/f'{stem}-menu-font.bin'
    boot=workdir/f'{stem}-romh0.bin'
    boot_lbl=workdir/f'{stem}-boot.lbl'
    boot_lst=workdir/f'{stem}-boot.lst'
    raw=workdir/f'{stem}.bin'
    crt=outdir/f'{stem}.crt'
    map_txt=outdir/f'{stem}-cart-map.txt'
    manifest_json=outdir/f'{stem}-cart-manifest.json'
    paths=(runtime,*runtime_style_files.values(),*runtime_style_labels.values(),*runtime_style_listings.values(),
           control,control_lbl,control_lst,menu_font,boot,boot_lbl,boot_lst,raw,crt,map_txt,manifest_json,include_path)
    if not a.output and a.stream_renderer=='yunroll-cart-v2':
        paths += tuple(outdir/f'c643d-demo-v{__version__}{suffix}' for suffix in ('.crt','-cart-manifest.json','-cart-map.txt'))
    if not _check_overwrite(paths,a.overwrite_policy):
        return 2
    try:
        from .cartstream import prepare_menu_streams
        stream_entries,stream_image,stream_info=prepare_menu_streams(ROOT,tass=tass,cartconv=cartconv,tass_args=a.tass_args,renderer=a.stream_renderer)
        image,plans,manifest=pack_demo_prgs((*CARTRIDGE_DEMO_ENTRIES,*stream_entries),source_root=ROOT)
        for bank in range(2,64):
            off=bank*16384+8192
            image[off:off+8192]=stream_image[off:off+8192]
        manifest['version']=__version__
        manifest['streamed_entries']=stream_info
        manifest['note']=f'Ten legacy PRGs plus two {a.stream_renderer.rsplit("-",1)[1].upper()} frame-streamed HiFi animations. PRG payloads use ROML; streamed frame blocks use ROMH.'
        if a.stream_renderer!='yunroll-cart-v2':manifest['stream_renderer']=a.stream_renderer
        manifest['menu_style']=a.menu_style
        manifest['menu_styles']=list(DEMO_MENU_STYLE_ORDER)
        manifest['menu_style_cycle_key']='F1'
        menu_font.write_bytes(build_menu_charset())
        write_demo_include(include_path,plans)
        for style in DEMO_MENU_STYLE_ORDER:
            assemble_demo_runtime(
                tass=tass,tass_args=a.tass_args,source=CART/'easyflash-demo-runtime.asm',
                include_dir=include_dir,output=runtime_style_files[style],
                labels=runtime_style_labels[style],listing=runtime_style_listings[style],cwd=ROOT,
                menu_style=style,
            )
        runtime.write_bytes(runtime_style_files[a.menu_style].read_bytes())
        assemble_demo_control(
            tass=tass,tass_args=a.tass_args,source=CART/'easyflash-demo-control.asm',
            output=control,labels=control_lbl,listing=control_lst,cwd=ROOT,
        )
        assemble_demo_boot(
            tass=tass,tass_args=a.tass_args,source=CART/'easyflash-demo-boot.asm',
            output=boot,labels=boot_lbl,listing=boot_lst,cwd=ROOT,
        )
        install_demo_boot(
            image,boot.read_bytes(),runtime.read_bytes(),control.read_bytes(),menu_font.read_bytes(),
            [runtime_style_files[style].read_bytes() for style in DEMO_MENU_STYLE_ORDER],
        )
        raw.write_bytes(bytes(image))
        write_demo_map(map_txt,manifest)
        with map_txt.open('a') as stream_map:
            for entry in stream_info:
                stream_map.write(f"\n{entry['name']}: {entry['frames']} streamed frames, ROMH banks {entry['first_bank']}..{entry['last_bank']}, {entry['rom_frame_bytes']} frame bytes\n")
        write_manifest(manifest_json,manifest)
        convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name=f'C643D {__version__} DEMO',cwd=ROOT)
        check_output=check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=ROOT)
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as e:
        print(f'error: EasyFlash demo build failed: {e}',file=sys.stderr)
        return 2

    if not a.output and a.stream_renderer=='yunroll-cart-v2':
        for original,suffix in ((crt,'.crt'),(manifest_json,'-cart-manifest.json'),(map_txt,'-cart-map.txt')):
            shutil.copyfile(original,outdir/f'c643d-demo-v{__version__}{suffix}')
    total=sum(p.length for p in plans)
    print(f'built {_display_path(crt)}')
    print(f'entries:     {len(plans)} animations (10 legacy + 2 streamed HiFi) / {total} boot payload bytes')
    print(f'start style: {a.menu_style}')
    print('menu styles: default -> decorative -> demoscene -> default (F1)')
    print(f'banks used:  {manifest["highest_bank_used"]+1} / 64 (bank 0 boot + {manifest["data_banks_used"]} ROML data banks)')
    print(f'raw:         {_display_path(raw)} (1 MiB EasyFlash image)')
    print(f'bank map:    {_display_path(map_txt)}')
    print(f'manifest:    {_display_path(manifest_json)}')
    if check_output:
        print(f'cartconv:    {check_output.splitlines()[-1]}')
    print('controls:    menu F1 cycles style; cursors select; RETURN plays')
    print('             in demo F1/RUN-STOP = menu, SPACE = next')
    print('streaming:   two HiFi demos use 128 orientations each from ROMH; original ten PRGs preserved')
    if a.run:
        cmd=tool_command(vice,a.vice_args,['-cartcrt',str(crt)])
        print('+',' '.join(cmd))
        subprocess.run(cmd,cwd=ROOT,check=False)
    return 0

def _viewport_height_arg(value):
    height=int(value)
    if height<8 or height>200 or height%8:
        raise argparse.ArgumentTypeError('viewport height must be a multiple of 8 from 8..200')
    return height


def _add_config_args(q):
    q.add_argument('--config',help='toolchain config file (default: config/c643d.ini; env: C643D_CONFIG)')
    q.add_argument('--no-config',action='store_true',help='ignore config files and use built-in/CLI toolchain settings')


def _add_toolchain_args(q,settings):
    _add_config_args(q)
    q.add_argument('--tass',default=settings.tass,help='64tass executable name, path, or containing directory')
    q.add_argument('--vice',default=settings.vice,help='x64sc executable name/path, VICE directory, or macOS .app bundle')
    q.add_argument('--blender',default=settings.blender,help='Blender executable name/path, installation directory, or macOS .app bundle')
    q.add_argument('--cartconv',default=settings.cartconv,help='cartconv executable name, path, or containing VICE directory (required only for cartridge/.crt builds)')
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
        q.add_argument('--color',help='force one C64 foreground colour name/index 0..15 instead of source colours')
        q.add_argument('--no-color','--no-colors','--ignore-colors',dest='ignore_colors',action='store_true',help='ignore OBJ/MTL or SVG source colours and render classic white-on-black wireframe')
        q.add_argument('--keep-winding',action='store_true',help='do not best-effort reorient mesh face winding')
        q.add_argument('--visibility',choices=('auto','surface_features','surface_creases','surface','frontface'),default='auto',help='hidden-line surface mode; auto uses robust surface Z-buffer for OBJ and front-face mode for procedural closed meshes')
        q.add_argument('--z-tolerance',type=float,help='reciprocal-depth tolerance for visible wire edges; object presets may provide a default')
        q.add_argument('--feature-angle',type=float,help='surface_creases threshold in degrees; sharp manifold edges at/above this angle are preserved')
    b=sub.add_parser('build',help='generate tables, assemble PRG, optionally run VICE'); common(b)
    b.add_argument('--renderer',choices=(*RENDERERS, 'yunroll-cart-v2', 'yunroll-cart-v3', 'yunroll-cart-v4'),default='yunroll',help='step/bytechunk/yunroll=PRG; yunroll-cart-v2/v3=streamed EasyFlash CRT')
    b.add_argument('--frames',type=int,help='precomputed legacy animation frames/orientations (default 48; not used by --blend)')
    b.add_argument('--strict-frames',action='store_true',help='fail instead of reducing orientation count when table RAM overflows')
    b.add_argument('--camera',type=float,default=110.0)
    b.add_argument('--focal',type=float,default=180.0)
    b.add_argument('--margin',type=int,default=4)
    b.add_argument('--max-fit-scale',type=float,default=1.4)
    b.add_argument('--no-auto-fit',action='store_true')
    b.add_argument('--blend',help='evaluate an animated .blend scene through headless Blender')
    b.add_argument('--scene',help='compile an already exported .c643dscene file without launching Blender')
    b.add_argument('--frame-start',type=int,help='first Blender source frame (default: scene start)')
    b.add_argument('--frame-end',type=int,help='last Blender source frame, inclusive (default: scene end)')
    b.add_argument('--sample-step',type=int,default=1,help='sample every Nth Blender frame (default 1)')
    b.add_argument('--output',help='output basename')
    b.add_argument('--output-dir',help='directory for PRG/LBL/LST outputs (default: build/)')
    overlay=b.add_mutually_exclusive_group()
    overlay.add_argument('--text-overlay',dest='text_overlay',action='store_true',help='show object HUD and FPS counter')
    overlay.add_argument('--no-text-overlay',dest='text_overlay',action='store_false',help='use separate no-overlay ASM and the full 200-line bitmap by default')
    b.set_defaults(text_overlay=settings.text_overlay)
    profiler=b.add_mutually_exclusive_group()
    profiler.add_argument('--rastertime-profiler',dest='rastertime_profiler',action='store_true',help='use derivative yunroll debug ASM that marks render CPU time in the border')
    profiler.add_argument('--no-rastertime-profiler',dest='rastertime_profiler',action='store_false',help=argparse.SUPPRESS)
    b.set_defaults(rastertime_profiler=settings.rastertime_profiler)
    b.add_argument('--viewport-height',type=_viewport_height_arg,default=settings.viewport_height,metavar='LINES',help='drawable height, multiple of 8 from 8..200; default auto=192 with overlay, 200 without')
    b.add_argument('--overwrite-policy',choices=('allow','warn','error'),default=settings.overwrite_policy,help='existing output handling (built-in default: warn)')
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
    imp.add_argument('--no-color','--no-colors','--ignore-colors',dest='ignore_colors',action='store_true',help='create a preset that ignores source MTL colours')
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
    isvg.add_argument('--no-color','--no-colors','--ignore-colors',dest='ignore_colors',action='store_true',help='create a preset that ignores SVG stroke/fill colours')
    isvg.add_argument('--overwrite',action='store_true')
    ge=sub.add_parser('generate-examples',help='compile bundled reference PRGs into examples/')
    _add_toolchain_args(ge,settings)
    ge.add_argument('--only',metavar='NAME',help='build only one named entry from the selected example manifest')
    ge.add_argument('--blender-only',action='store_true',help='build only canonical Blender-backed examples from examples/blender_falling_cubes/examples.json')
    ge.add_argument('--variants',choices=('normal','legacy144','no-overlay','rastertime-profiler','all'),default='all',help='which PRG variants to generate (default: all)')
    ge.add_argument('--reference-set',help='checksum reference set from tests/data/golden_prg_checksums.json (default: manifest default)')
    te=sub.add_parser('test-examples',help='rebuild examples into a temporary directory and compare PRG checksums')
    _add_toolchain_args(te,settings)
    te.add_argument('--only',metavar='NAME',help='test only one named entry from the selected example manifest')
    te.add_argument('--blender-only',action='store_true',help='rebuild only canonical Blender-backed examples from examples/blender_falling_cubes/examples.json')
    te.add_argument('--variants',choices=('normal','legacy144','no-overlay','rastertime-profiler','all'),default='all',help='which PRG variants to test (default: all)')
    te.add_argument('--reference-set',help='checksum reference set from tests/data/golden_prg_checksums.json (default: manifest default)')
    te.add_argument('--reproduce-reference',action='store_true',help='apply the selected reference set build_overrides (for example the legacy 144-line viewport); requires --variants normal')
    cs=sub.add_parser('cartridge-smoke',help='build a minimal EasyFlash bank-switch .crt diagnostic')
    _add_toolchain_args(cs,settings)
    cs.add_argument('--output',help='output basename (default: easyflash-smoke)')
    cs.add_argument('--output-dir',help='output directory (default: build/)')
    cs.add_argument('--overwrite-policy',choices=('allow','warn','error'),default=settings.overwrite_policy,help='existing output handling (built-in default: warn)')
    cs.add_argument('--run',action='store_true',help='attach the generated CRT directly with VICE -cartcrt')
    cd=sub.add_parser('cart-demos',help='build shipped EasyFlash demo CRT(s) into examples/cart_demos/')
    _add_toolchain_args(cd,settings)
    cd.add_argument('--output',help='output basename (default: version and renderer-labelled cart name)')
    cd.add_argument('--output-dir',help='final demo output directory (default: examples/cart_demos/; intermediates stay in build/)')
    cd.add_argument('--overwrite-policy',choices=('allow','warn','error'),default=settings.overwrite_policy,help='existing output handling (built-in default: warn)')
    cd.add_argument('--menu-style',choices=('default','decorative','demoscene'),default='default',help='initial cartridge menu presentation; F1 cycles all styles at runtime (default: default)')
    cd.add_argument('--run',action='store_true',help='attach the generated demo CRT directly with VICE -cartcrt')
    cd.add_argument('--stream-renderer',choices=('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4'),default='yunroll-cart-v4',help='one renderer for every demo; writes a separate version-labelled comparison cart')
    cda=sub.add_parser('cartridge-demo',help=argparse.SUPPRESS)
    _add_toolchain_args(cda,settings)
    cda.add_argument('--output',help='output basename (default: version and renderer-labelled cart name)')
    cda.add_argument('--output-dir',help='final demo output directory (default: examples/cart_demos/; intermediates stay in build/)')
    cda.add_argument('--overwrite-policy',choices=('allow','warn','error'),default=settings.overwrite_policy,help='existing output handling (built-in default: warn)')
    cda.add_argument('--menu-style',choices=('default','decorative','demoscene'),default='default',help='initial cartridge menu presentation; F1 cycles all styles at runtime (default: default)')
    cda.add_argument('--run',action='store_true',help='attach the generated demo CRT directly with VICE -cartcrt')
    cda.add_argument('--stream-renderer',choices=('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4'),default='yunroll-cart-v4',help='one renderer for every demo; writes a separate version-labelled comparison cart')
    sub.add_parser('cart-stream',help='build an experimental yunroll-cart-v2 streamed EasyFlash CRT (same source flags as build)')
    doc=sub.add_parser('doctor',help='check local 64tass/VICE and optional Blender/cartconv availability')
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
    if argv and argv[0]=='cart-stream':
        argv=['build', '--renderer', 'yunroll-cart-v2']+argv[1:]
    if not argv:
        argv=['build']
    elif argv[0]=='--generate-examples':
        argv=['generate-examples']+argv[1:]
    elif argv[0]=='--generate-cart-demos':
        argv=['cart-demos']+argv[1:]
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
    if a.command=='test-examples': return cmd_test_examples(a)
    if a.command=='doctor': return cmd_doctor(a)
    if a.command=='cartridge-smoke': return cmd_cartridge_smoke(a)
    if a.command in ('cart-demos','cartridge-demo'): return cmd_cart_demos(a)
    if a.command=='list-objects': return cmd_list_objects()
    if a.command=='import-obj': return cmd_import_obj(a)
    if a.command=='import-svg': return cmd_import_svg(a)
    if a.command=='inspect': return cmd_inspect(a)
    return cmd_build(a)
