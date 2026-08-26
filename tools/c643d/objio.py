from __future__ import annotations
import shlex
from pathlib import Path
from .mesh import Mesh
from .colors import nearest_c64_color_index


def _words(value: str) -> list[str]:
    try:
        return shlex.split(value,comments=False,posix=True)
    except ValueError:
        return value.split()


def load_mtl(path: str | Path) -> dict[str,int]:
    """Load diffuse MTL colours as native 0..15 VIC-II palette indices."""
    path=Path(path)
    colors: dict[str,int]={}
    current: str | None=None
    for lineno,raw in enumerate(path.read_text(encoding='utf-8',errors='replace').splitlines(),1):
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        words=line.split(None,1); head=words[0]; rest=words[1] if len(words)>1 else ''
        key=head.lower(); rest=rest.strip()
        if key=='newmtl':
            current=rest or None
        elif key=='kd' and current:
            parts=rest.split()
            if len(parts)<3:
                continue
            try:
                rgb=tuple(round(max(0.0,min(1.0,float(v)))*255.0) for v in parts[:3])
            except ValueError as exc:
                raise ValueError(f'{path}:{lineno}: invalid Kd colour') from exc
            colors[current]=nearest_c64_color_index(rgb)
    return colors


def load_obj(path: str | Path, name: str | None=None) -> Mesh:
    path=Path(path)
    lines=path.read_text(encoding='utf-8',errors='replace').splitlines()
    materials: dict[str,int]={}
    for raw in lines:
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        words=line.split(None,1); head=words[0]; rest=words[1] if len(words)>1 else ''
        if head.lower()!='mtllib':
            continue
        for ref in _words(rest.strip()):
            mtl_path=path.parent/ref
            if mtl_path.is_file():
                materials.update(load_mtl(mtl_path))

    verts=[]; faces=[]; face_colors=[]; active_material: str | None=None
    for lineno,raw in enumerate(lines,1):
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        parts=line.split()
        if parts[0]=='v' and len(parts)>=4:
            verts.append((float(parts[1]),float(parts[2]),float(parts[3])))
        elif parts[0]=='usemtl':
            active_material=line[len(parts[0]):].strip() or None
        elif parts[0]=='f' and len(parts)>=4:
            face=[]
            for tok in parts[1:]:
                idxs=tok.split('/')[0]
                if not idxs: continue
                idx=int(idxs)
                if idx<0: idx=len(verts)+idx
                else: idx-=1
                if idx<0 or idx>=len(verts):
                    raise ValueError(f'{path}:{lineno}: vertex index out of range: {tok}')
                face.append(idx)
            # Drop consecutive duplicate indices and degenerate faces.
            compact=[]
            for i in face:
                if not compact or compact[-1]!=i: compact.append(i)
            if len(compact)>=3 and compact[0]==compact[-1]: compact.pop()
            if len(set(compact))>=3:
                faces.append(tuple(compact))
                face_colors.append(materials.get(active_material) if active_material else None)
    if not verts: raise ValueError(f'{path}: no vertices')
    if not faces: raise ValueError(f'{path}: no polygon faces')
    return Mesh(name or path.stem.upper(),verts,faces,[],face_colors,[])
