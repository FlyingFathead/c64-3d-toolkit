"""Frozen shipped pictures for exact example migration without a Blender rebake.

This is host input data, not a runnable legacy cartridge. It retains all source
samples, bitmap pixels, resolved colours, HUD bytes and presentation settings.
"""
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from .pipeline import FrameBuild
from .optimize import picture_bytes


def frame_from_bitmap(bitmap, colors):
    records=[]
    for y in range(192):
        xs=[x for x in range(320) if bitmap[(y//8)*320+(x//8)*8+(y&7)] & (128>>(x&7))]
        i=0
        while i<len(xs):
            x=xs[i];j=i+1
            while j<len(xs) and xs[j]==xs[j-1]+1 and j-i<127: j+=1
            n=j-i;offset=(y//8)*320+(x//8)*8
            records.append((offset&255,offset>>8,n,(x&7)|((y&7)<<3),*([0]*((x%8+n+7)//8))))
            i=j
    cells=[i for i in range(960) if any(bitmap[i*8:i*8+8])]
    clears=[];i=0
    while i<len(cells):
        j=i+1
        while j<len(cells) and cells[j]==cells[j-1]+1 and j-i<32: j+=1
        offset=cells[i]*8;clears.append((offset&255,offset>>8,j-i));i=j
    frame=FrameBuild(records,clears,sum(r[2] for r in records),sum(b.bit_count() for b in bitmap),[],colors)
    if picture_bytes(frame)[:7680]!=bitmap: raise ValueError('Frozen example bitmap reconstruction failed')
    return frame


def load(root):
    path=Path(root)/'assets/released-example-pictures-v1.json.gz'
    data=json.loads(gzip.decompress(path.read_bytes()))
    if data['format']!='c643d-released-example-pictures-v1': raise ValueError('Unknown example reference')
    return data['examples']


def decode(row):
    frames=[]
    for frame in row['pictures']:
        bitmap=bytes.fromhex(frame['bitmap'])
        if len(bitmap)!=7680: raise ValueError('Bad example bitmap length')
        decoded=frame_from_bitmap(bitmap,frame['colors'])
        if hashlib.sha256(picture_bytes(decoded,row['settings']['screen_color'])).hexdigest()!=frame['sha256']:
            raise ValueError('Frozen example picture or colour hash differs')
        frames.append(decoded)
    settings=row['settings']
    mesh=SimpleNamespace(name=settings['name'],vertices=[None]*(settings['vertices'] or 0),
        edges=[None]*(settings['edges'] or 0),faces=[None]*(settings['faces'] or 0))
    scene=SimpleNamespace(name=mesh.name,mesh=mesh,source_fps=settings.get('source_fps',50),
        sample_step=settings.get('sample_step',1),
        frames=[SimpleNamespace(source_frame=i) for i in settings.get('source_frames',range(len(frames)))])
    return frames,mesh,scene


def is_current_v2_example(path, version):
    """Select stable examples without treating an old versioned menu as current."""
    import re
    name=path.name
    if not ('hors-render-v2' in name or 'hors-v2' in name) or 'beta' in name:
        return False
    match=re.search(r'-v(\d+\.\d+\.\d+)-',name)
    return match is None or match.group(1)==version
