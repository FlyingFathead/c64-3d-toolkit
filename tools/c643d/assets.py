from __future__ import annotations
from dataclasses import dataclass
import json, re, shutil, shlex
from pathlib import Path

@dataclass
class ObjectPreset:
    slug: str
    name: str
    obj_path: Path
    up_axis: str = 'y'
    spin_axis: str = 'y'
    rotate: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    notes: str = ''
    visibility: str = 'auto'
    z_tolerance: float = 0.0008
    feature_angle: float = 40.0
    materials: tuple[str, ...] = ()
    color: str = 'white'
    animation: str = 'spin'
    animation_tilt: float = 62.0
    animation_travel: float = 120.0
    animation_rise: float = 54.0
    svg_tolerance: float = 3.0
    svg_curve_step: float = 12.0
    svg_depth: float = 5.0
    svg_connector_stride: int = 4


def slugify(value: str) -> str:
    value=value.strip().lower().replace(' ','_')
    value=re.sub(r'[^a-z0-9_.-]+','_',value)
    value=re.sub(r'_+','_',value).strip('._-')
    if not value:
        raise ValueError('object name produced an empty slug')
    return value


def _metadata_path(objects_dir: Path, slug: str) -> Path:
    return objects_dir/f'{slug}.json'


def load_object_preset(objects_dir: Path, name: str) -> ObjectPreset:
    slug=slugify(name)
    meta_path=_metadata_path(objects_dir,slug)
    data={}
    if meta_path.exists():
        data=json.loads(meta_path.read_text(encoding='utf-8'))
    if 'file' in data:
        obj_name=data['file']
    elif (objects_dir/f'{slug}.obj').exists():
        obj_name=f'{slug}.obj'
    elif (objects_dir/f'{slug}.svg').exists():
        obj_name=f'{slug}.svg'
    else:
        obj_name=f'{slug}.obj'
    obj_path=objects_dir/obj_name
    if not obj_path.exists():
        raise FileNotFoundError(f'object preset {slug!r} points to missing asset: {obj_path}')
    up=data.get('up_axis','y')
    spin=data.get('spin_axis','y')
    if up not in ('y','z'):
        raise ValueError(f'{meta_path}: up_axis must be y or z')
    if spin not in ('x','y','z'):
        raise ValueError(f'{meta_path}: spin_axis must be x, y or z')
    animation=str(data.get('animation','spin'))
    if animation not in ('spin','recede','crawl'):
        raise ValueError(f'{meta_path}: animation must be spin, recede or crawl')
    rot=data.get('rotate',[0.0,0.0,0.0])
    if len(rot)!=3:
        raise ValueError(f'{meta_path}: rotate must contain three degree values')
    return ObjectPreset(
        slug=slug,
        name=str(data.get('name',slug.replace('_',' ').upper())),
        obj_path=obj_path,
        up_axis=up,
        spin_axis=spin,
        rotate=(float(rot[0]),float(rot[1]),float(rot[2])),
        scale=float(data.get('scale',1.0)),
        notes=str(data.get('notes','')),
        visibility=str(data.get('visibility','auto')),
        z_tolerance=float(data.get('z_tolerance',0.0008)),
        feature_angle=float(data.get('feature_angle',40.0)),
        materials=tuple(str(x) for x in data.get('materials',[])),
        color=str(data.get('color','white')),
        animation=animation,
        animation_tilt=float(data.get('animation_tilt',62.0)),
        animation_travel=float(data.get('animation_travel',120.0)),
        animation_rise=float(data.get('animation_rise',54.0)),
        svg_tolerance=float(data.get('svg_tolerance',3.0)),
        svg_curve_step=float(data.get('svg_curve_step',12.0)),
        svg_depth=float(data.get('svg_depth',5.0)),
        svg_connector_stride=int(data.get('svg_connector_stride',4)),
    )


def list_object_presets(objects_dir: Path) -> list[ObjectPreset]:
    seen=set(); out=[]
    for p in sorted(objects_dir.glob('*.json')):
        slug=p.stem
        try:
            preset=load_object_preset(objects_dir,slug)
        except (OSError,ValueError,json.JSONDecodeError):
            continue
        seen.add(slug); out.append(preset)
    for p in sorted(list(objects_dir.glob('*.obj'))+list(objects_dir.glob('*.svg'))):
        if p.stem.endswith('_fallback') or p.stem in seen:
            continue
        try: out.append(load_object_preset(objects_dir,p.stem))
        except (OSError,ValueError,json.JSONDecodeError): pass
    return out


def _copy_obj_with_materials(source: Path, dest: Path, *, overwrite: bool) -> list[str]:
    """Copy an OBJ and any directly referenced mtllib files next to it.

    Material data is currently preserved for interchange/future preview use; the
    C64 wireframe compiler itself does not consume MTL shading yet. References
    containing subdirectories are flattened to the destination directory and the
    copied OBJ's mtllib line is rewritten accordingly.
    """
    lines=source.read_text(encoding='utf-8',errors='replace').splitlines()
    materials=[]; rewritten=[]
    for line in lines:
        stripped=line.lstrip()
        if not stripped.startswith('mtllib '):
            rewritten.append(line); continue
        indent=line[:len(line)-len(stripped)]
        try:
            refs=shlex.split(stripped[len('mtllib '):])
        except ValueError:
            refs=stripped[len('mtllib '):].split()
        outrefs=[]
        for ref in refs:
            srcmat=(source.parent/ref).resolve()
            if not srcmat.exists():
                # Keep unresolved references intact; OBJ geometry is still usable.
                outrefs.append(ref); continue
            name=Path(ref).name
            dstmat=dest.parent/name
            if dstmat.exists() and srcmat!=dstmat.resolve() and not overwrite:
                raise FileExistsError(f'material destination already exists: {dstmat}; pass --overwrite')
            if srcmat!=dstmat.resolve():
                shutil.copy2(srcmat,dstmat)
            outrefs.append(name); materials.append(name)
        rewritten.append(indent+'mtllib '+' '.join(outrefs))
    dest.write_text('\n'.join(rewritten)+'\n',encoding='utf-8')
    return list(dict.fromkeys(materials))


def import_obj_asset(
    source: str | Path,
    objects_dir: Path,
    *,
    slug: str | None = None,
    display_name: str | None = None,
    up_axis: str = 'y',
    spin_axis: str = 'y',
    rotate: tuple[float,float,float] = (0.0,0.0,0.0),
    scale: float = 1.0,
    overwrite: bool = False,
) -> ObjectPreset:
    source=Path(source)
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower()!='.obj':
        raise ValueError('import-obj currently accepts Wavefront .obj files only')
    slug=slugify(slug or source.stem)
    if up_axis not in ('y','z'): raise ValueError('up axis must be y or z')
    if spin_axis not in ('x','y','z'): raise ValueError('spin axis must be x, y or z')
    objects_dir.mkdir(parents=True,exist_ok=True)
    dest=objects_dir/f'{slug}.obj'; meta=_metadata_path(objects_dir,slug)
    if (dest.exists() or meta.exists()) and not overwrite:
        raise FileExistsError(f'objects/{slug} already exists; pass --overwrite to replace it')
    materials=_copy_obj_with_materials(source,dest,overwrite=overwrite)
    payload={
        'name': display_name or slug.replace('_',' ').upper(),
        'file': dest.name,
        'materials': materials,
        'up_axis': up_axis,
        'spin_axis': spin_axis,
        'rotate': [float(x) for x in rotate],
        'scale': float(scale),
        'visibility': 'surface',
        'z_tolerance': 0.0012,
        'feature_angle': 40.0,
    }
    meta.write_text(json.dumps(payload,indent=2)+"\n",encoding='utf-8')
    return load_object_preset(objects_dir,slug)


def import_svg_asset(
    source: str | Path,
    objects_dir: Path,
    *,
    slug: str | None = None,
    display_name: str | None = None,
    spin_axis: str = 'y',
    rotate: tuple[float,float,float] = (0.0,0.0,0.0),
    scale: float = 1.0,
    color: str = 'auto',
    animation: str = 'spin',
    animation_tilt: float = 62.0,
    animation_travel: float = 120.0,
    animation_rise: float = 54.0,
    svg_tolerance: float = 3.0,
    svg_curve_step: float = 12.0,
    svg_depth: float = 5.0,
    svg_connector_stride: int = 4,
    overwrite: bool = False,
) -> ObjectPreset:
    """Copy an SVG into objects/ and create a wire-extrusion preset."""
    from .svgio import load_svg, c64_color_index, c64_color_name
    source=Path(source)
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower()!='.svg':
        raise ValueError('import-svg accepts .svg files only')
    if spin_axis not in ('x','y','z'):
        raise ValueError('spin axis must be x, y or z')
    if animation not in ('spin','recede','crawl'):
        raise ValueError('animation must be spin, recede or crawl')
    slug=slugify(slug or source.stem)
    objects_dir.mkdir(parents=True,exist_ok=True)
    dest=objects_dir/f'{slug}.svg'; meta=_metadata_path(objects_dir,slug)
    if (dest.exists() or meta.exists()) and not overwrite:
        raise FileExistsError(f'objects/{slug} already exists; pass --overwrite to replace it')
    info=load_svg(source,display_name or slug.replace('_',' ').upper(),tolerance=svg_tolerance,curve_step=svg_curve_step,depth=svg_depth,connector_stride=svg_connector_stride)
    chosen=info.c64_color if color=='auto' else c64_color_name(c64_color_index(color))
    if source.resolve()!=dest.resolve():
        shutil.copy2(source,dest)
    payload={
        'name': display_name or slug.replace('_',' ').upper(),
        'file': dest.name,
        'spin_axis': spin_axis,
        'rotate': [float(x) for x in rotate],
        'scale': float(scale),
        'visibility': 'surface',
        'z_tolerance': 0.0012,
        'color': chosen,
        'animation': animation,
        'animation_tilt': float(animation_tilt),
        'animation_travel': float(animation_travel),
        'animation_rise': float(animation_rise),
        'svg_tolerance': float(svg_tolerance),
        'svg_curve_step': float(svg_curve_step),
        'svg_depth': float(svg_depth),
        'svg_connector_stride': int(svg_connector_stride),
        'notes': f'SVG wire extrusion; source colour {info.source_color or "unknown"} mapped to C64 {chosen}.',
    }
    meta.write_text(json.dumps(payload,indent=2)+"\n",encoding='utf-8')
    return load_object_preset(objects_dir,slug)
