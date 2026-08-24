from __future__ import annotations
from pathlib import Path
from .mesh import Mesh


def load_obj(path: str | Path, name: str | None=None) -> Mesh:
    path=Path(path)
    verts=[]; faces=[]
    for lineno,raw in enumerate(path.read_text(encoding='utf-8',errors='replace').splitlines(),1):
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        parts=line.split()
        if parts[0]=='v' and len(parts)>=4:
            verts.append((float(parts[1]),float(parts[2]),float(parts[3])))
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
            if len(set(compact))>=3: faces.append(tuple(compact))
    if not verts: raise ValueError(f'{path}: no vertices')
    if not faces: raise ValueError(f'{path}: no polygon faces')
    return Mesh(name or path.stem.upper(),verts,faces)
