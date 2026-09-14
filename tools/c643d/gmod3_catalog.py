"""Inventory released pictures for the GMod3 collection without changing sources.

Read-only decoding of the existing V2 CRTs and independent V3 picture oracles.
Equivalent picture sequences share one entry; every source is accounted for.
"""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from .pipeline import FrameBuild
from .optimize import picture_bytes
from .released_examples import frame_from_bitmap


def read_json(path):
    blob = Path(path).read_bytes()
    return json.loads(gzip.decompress(blob) if str(path).endswith('.gz') else blob)


def chips(path):
    blob = Path(path).read_bytes()
    if blob[:16] != b'C64 CARTRIDGE   ': raise ValueError('Invalid source CRT')
    pos = int.from_bytes(blob[16:20], 'big'); out = {}
    while pos < len(blob):
        magic, length, kind, bank, address, size = struct.unpack_from('>4sIHHHH', blob, pos)
        if magic != b'CHIP' or length != size+16: raise ValueError('Invalid source CHIP')
        out[bank, address] = blob[pos+16:pos+length]; pos += length
    return out


def decode_v2(crt, manifest):
    rom = chips(crt); frames=[]
    for d in manifest['frame_data']:
        address=d['address']; window=0xa000 if d.get('chip')=='romh' else 0x8000
        payload=rom[d['bank'],window][address-window:address-window+d['bytes']]
        if hashlib.sha256(payload).hexdigest()!=d['sha256']: raise ValueError('Source frame hash mismatch')
        p=1+3*payload[0]; colors=[]
        if manifest['colors']:
            count=payload[p];p+=1
            colors=[tuple(payload[p+4*i:p+4*i+4]) for i in range(count)];p+=count*4
        if p!=d['metadata_bytes']:raise ValueError('Unsupported V2 metadata')
        count=int.from_bytes(payload[p:p+2],'little');p+=2
        if not count&0x8000:raise ValueError('Expected literal V2 bitmap')
        bitmap=bytearray(7680)
        for _ in range(count&0x7fff):
            lo,hi,n=payload[p:p+3];p+=3; offset=lo+256*(hi&127)
            if offset+n>7680:raise ValueError('Source span outside model viewport')
            bitmap[offset:offset+n]=payload[p:p+n];p+=n
        if p!=len(payload):raise ValueError('Source payload tail mismatch')
        frames.append(frame_from_bitmap(bytes(bitmap),colors))
    return frames


def inventory(root, cache=None):
    root=Path(root); cache=Path(cache or root/'build/gmod3-catalog')
    cache.mkdir(parents=True,exist_ok=True)
    paths=[root/x['path'] for x in read_json(root/'examples/release-index.json')['files'] if x['path'].endswith('-manifest.json')]
    # SAKU was added after the release index. Include all three current carts.
    paths += sorted((root/'examples/saku_2026/cartridges').glob('*-manifest.json'))
    result=[]; seen={}; sources=[]
    for path in sorted(set(paths)):
        meta=read_json(path)
        stem=path.name.removesuffix('-cart-manifest.json').removesuffix('-manifest.json')
        parent=path.parent.parent if path.parent.name=='metadata' else path.parent
        crt=parent/(stem+'.crt')
        if not crt.exists(): raise ValueError('Missing catalog cartridge '+str(crt))
        for part,m in enumerate(meta.get('streamed_entries',[meta])):
            if 'frame_data' not in m:raise ValueError('Missing source directory '+str(path))
            oracle=parent/(stem+'-oracle.json.gz')
            if not oracle.exists():oracle=parent/(stem+'-oracle.json')
            if oracle.exists() and 'streamed_entries' not in meta:
                frames=[FrameBuild(**f) for f in read_json(oracle)]
            else: frames=decode_v2(crt,m)
            if len(frames)!=m['frames']:raise ValueError('Incomplete source picture set')
            screen=m.get('screen_color',16);digest=hashlib.sha256()
            for f in frames:digest.update(picture_bytes(f,screen))
            modes=30 if 'saku_2026-interactive' in stem else 0
            identity=(digest.hexdigest(),m.get('output_fps',m.get('frame_ticks',1)),bool(modes))
            origin=dict(cartridge=crt.relative_to(root).as_posix(),manifest=path.relative_to(root).as_posix(),
                entry=part,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),frames=len(frames))
            if identity in seen:
                seen[identity]['sources'].append(origin);continue
            name=m.get('name',stem).upper().replace('_',' ')
            if 'stanford_dragon-' in stem:name='DRAGON '+stem.split('stanford_dragon-')[1].split('-')[0].upper()
            elif 'sande_pretzel-' in stem:
                tail=stem.split('sande_pretzel-')[1].replace('hors-render-v2','WIRE').replace('surface-','').split('-128')[0].split('-192')[0]
                name='PRETZEL '+tail.upper()
            elif 'sande_tac2-' in stem:name='TAC-2 '+('COLOUR' if '-color' in stem else 'WIRE')
            elif '/torus_dense/' in str(path):name='DENSE TORUS'
            elif '/color_combo_test/' in str(path):name=m['name']
            if modes:name='SAKU 2026 INTERACTIVE'
            elif 'saku_2026-' in stem:name='SAKU '+stem.split('saku_2026-')[1].upper()
            row=dict(id=len(result),name=name,frames=len(frames),colors=m['colors'],screen_color=screen,
                border_color=m.get('border_color',0),vertices=m.get('vertices') or 0,edges=m.get('edges') or 0,
                sources=[origin],picture_sha256=digest.hexdigest(),mode_frames=modes,
                variants=['card','outline'] if modes else [],
                occlusion_bounds=m.get('background_effect',{}).get('opaque_bounds') if modes else None,
                target_fps=m.get('output_fps') or (50/m['frame_ticks'] if m.get('frame_ticks',1)>1 else None),
                original_intro=m.get('intro',False),original_ending=m.get('ending',False))
            row['oracle']=f'{row["id"]:02d}.json.gz'
            (cache/row['oracle']).write_bytes(gzip.compress(json.dumps([asdict(f) for f in frames],separators=(',',':')).encode(),mtime=0))
            result.append(row);seen[identity]=row
            print(f'Inventory {row["id"]:02d}: {name}, {len(frames)} pictures',flush=True)
    (cache/'catalog.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def frames_for(cache,row):
    return [FrameBuild(**f) for f in read_json(Path(cache)/row['oracle'])]


def mesh_for(row):
    return SimpleNamespace(name=row['name'],vertices=[None]*row['vertices'],edges=[None]*row['edges'])
