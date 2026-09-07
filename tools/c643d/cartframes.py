"""Read exact banked vector frames from a toolkit CRT and matching manifest.

Used to preserve a released rendering oracle and rebuild its same samples
without rerunning Blender physics, projection or visibility. Never reads bitmap
playback data: recovered records are drawn on the C64 by the selected renderer.
"""
import hashlib
import json
import struct
from pathlib import Path
from .pipeline import FrameBuild, decode_record_points
from .cartpaths import menu_manifest_path


def read_chips(path):
    blob = Path(path).read_bytes()
    if blob[:16] != b'C64 CARTRIDGE   ' or int.from_bytes(blob[22:24], 'big') != 32:
        raise ValueError('expected an EasyFlash CRT')
    pos = int.from_bytes(blob[16:20], 'big')
    chips = {}
    while pos < len(blob):
        if blob[pos:pos+4] != b'CHIP' or pos+16 > len(blob):
            raise ValueError('invalid CHIP packet')
        length, kind, bank, address, size = struct.unpack('>IHHHH', blob[pos+4:pos+16])
        if length != size+16 or size != 8192 or bank >= 64 or address not in (0x8000, 0xa000):
            raise ValueError('unsupported EasyFlash chip layout')
        key = (bank, address)
        if key in chips or pos+length > len(blob):
            raise ValueError('duplicate or truncated chip')
        chips[key] = blob[pos+16:pos+length]
        pos += length
    return chips


def extract_frames(chips, manifest):
    frames = []
    for index, d in enumerate(manifest['frame_data']):
        if d['frame'] != index:
            raise ValueError('nonsequential frame directory')
        base = d['address'] & 0xe000
        offset = d['address']-base
        data = chips[d['bank'], base][offset:offset+d['bytes']]
        if len(data) != d['bytes'] or hashlib.sha256(data).hexdigest() != d['sha256']:
            raise ValueError(f'frame {index} differs from manifest')
        p = 0
        def take(n):
            nonlocal p
            block = data[p:p+n]
            if len(block) != n:
                raise ValueError('truncated frame')
            p += n
            return block
        clear = [tuple(take(3)) for _ in range(take(1)[0])]
        colors = [tuple(take(4)) for _ in range(take(1)[0])] if manifest['colors'] else []
        if p != d['metadata_bytes']:
            raise ValueError('metadata length mismatch')
        count = int.from_bytes(take(2), 'little')
        records = []
        points = set()
        for _ in range(count):
            header = take(4)
            if not 2 <= header[2] <= 127:
                raise ValueError('invalid vector length')
            phase = (header[3] >> 3) & 7 if header[3] & 64 else header[3] & 7
            rec = tuple(header + take((phase+header[2]+7)//8))
            pts = decode_record_points(rec)
            if any(not (0 <= x < 256 and 0 <= y < 192) for x, y in pts):
                raise ValueError('vector outside viewport')
            records.append(rec)
            points.update(pts)
        if p != len(data) or count != d['runs']:
            raise ValueError('frame record length mismatch')
        touched = {(y//8)*320+(x//8)*8 for x, y in points}
        cleared = set()
        for lo, hi, n in clear:
            off = lo+(hi<<8)
            if n == 0 or off % 8 or off+n*8 > 7680:
                raise ValueError('invalid clear span')
            cleared.update(range(off, off+n*8, 8))
        if touched != cleared:
            raise ValueError('clear coverage mismatch')
        if any(not (1 <= n <= 255 and lo+(hi<<8)+n <= 960) for lo, hi, n, _ in colors):
            raise ValueError('invalid color span')
        frames.append(FrameBuild(records, clear, sum(r[2] for r in records), len(points), [], colors))
    if len(frames) != manifest['frames']:
        raise ValueError('frame count mismatch')
    return frames


def load_uniform_sources(root, crt):
    """Recover a uniform cart's original records and embedded static HUD bytes."""
    import re
    from .cartuniform import Demo
    crt=Path(crt)
    manifest=json.loads(menu_manifest_path(crt).read_text())
    if not manifest.get('uniform_renderer'):
        raise ValueError('reference cart must have one uniform stream renderer')
    chips=read_chips(crt);result=[]
    for entry, stream in zip(manifest['entries'],manifest['streamed_entries'],strict=True):
        if entry['name'] != stream['name']:
            raise ValueError('menu and stream directory order differ')
        frames=extract_frames(chips,stream)
        payload=b''.join(chips[entry['bank']+j,0x8000] for j in range(entry['banks']))[:entry['payload_bytes']]
        if sum(payload)&65535 != int(entry['checksum16'].lstrip('$'),16):
            raise ValueError('reference runtime checksum mismatch')
        load=int(entry['load_address'].lstrip('$'),16)
        signature=re.search(b'\xbd(..)\x9d\x00\x3e\x9d\x00\x7e\x9d\x00\xfe\xe8\xe0(.)',payload,re.S)
        if signature is None:
            raise ValueError('reference runtime lacks the standard HUD copy signature')
        off=int.from_bytes(signature[1],'little')-load
        length=signature[2][0]
        hud=payload[off:off+length]
        if not 0<=off<len(payload) or len(hud)!=length:
            raise ValueError('invalid reference HUD address')
        result.append(Demo(stream['name'],frames,stream['colors'],stream['screen_color'],hud,
                           stream['source'],stream['source_sha256']))
    return result


def load_menu_reference(root):
    """Original V4 vectors/HUD, compressed on the host to avoid retaining a CRT.

    These are exact decoded vector records, not bitmap playback data. Builders
    still generate banked streams which the 6510 draws at runtime.
    """
    import gzip
    from .cartuniform import Demo
    path = Path(root) / 'assets/v4-menu-vector-reference.json.gz'
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != MENU_REFERENCE_SHA256:
        raise ValueError('V4 menu vector reference differs from the frozen baseline')
    data = json.loads(gzip.decompress(content))
    if data['format'] != 'c643d-vector-reference-v1':
        raise ValueError('Unsupported vector reference format')
    result = []
    for row in data['demos']:
        entry = dict(row)
        entry['frames'] = [FrameBuild(**frame) for frame in entry['frames']]
        entry['hud'] = bytes.fromhex(entry['hud'])
        result.append(Demo(**entry))
    return result


MENU_REFERENCE_SHA256 = '86c048833599361f734d1a032b66559dd0be9cdfe6d5d76b1deb9c9bc695eda7'


def load_scene_source(crt):
    from types import SimpleNamespace
    crt=Path(crt)
    manifest=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    if manifest['format']!='c643d-easyflash-stream-scene':
        raise ValueError('reference must be a toolkit scene cart')
    frames=extract_frames(read_chips(crt),manifest)
    scene=SimpleNamespace(name=manifest['name'],
        mesh=SimpleNamespace(vertices=[None]*manifest['vertices'],edges=[None]*manifest['edges'],faces=[None]*manifest['faces']),
        source_fps=manifest['source_fps'],sample_step=manifest['sample_step'],
        frames=[SimpleNamespace(source_frame=f) for f in manifest['source_frames']])
    return frames,scene,manifest
