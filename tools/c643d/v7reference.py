"""Recover V7 scene vectors for V8 comparison without re-exporting Blender."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from .cartframes import read_chips
from .pipeline import FrameBuild, decode_record_points


def load_scene(crt):
    crt = Path(crt)
    manifest = json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    if manifest['renderer'] != 'yunroll-cart-v7-scene':
        raise ValueError('V7 reference scene required')
    chips = read_chips(crt)
    frames = []
    for i, entry in enumerate(manifest['frame_data']):
        base = entry['address'] & 0xe000
        offset = entry['address']-base
        data = chips[entry['bank'], base][offset:offset+entry['bytes']]
        if entry['frame'] != i or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('V7 reference directory/checksum mismatch')
        cursor = 0
        def take(n):
            nonlocal cursor
            result = data[cursor:cursor+n]
            if len(result) != n:
                raise ValueError('truncated V7 reference')
            cursor += n
            return result
        clear = [tuple(take(3)) for _ in range(take(1)[0])]
        colors = [tuple(take(4)) for _ in range(take(1)[0])] if manifest['colors'] else []
        if cursor != entry['metadata_bytes']:
            raise ValueError('V7 metadata size mismatch')
        count = int.from_bytes(take(2), 'little')
        records, points = [], set()
        for _ in range(count):
            header = take(4)
            if not 2 <= header[2] <= 127:
                raise ValueError('invalid V7 vector length')
            phase = (header[3] >> 3) & 7 if header[3] & 64 else header[3] & 7
            rec = tuple(header+take((phase+header[2]+7)//8))
            records.append(rec)
            points.update(decode_record_points(rec))
        if cursor != len(data) or count != entry['runs']:
            raise ValueError('V7 vector size mismatch')
        covered = set()
        for lo, hi, length in clear:
            start = lo+((hi & 31) << 8)
            n = (length or 256) if hi & 128 else length*8
            if start+n > 7680 or n == 0:
                raise ValueError('invalid V7 clear range')
            covered.update(range(start, start+n))
        dirty = {(y//8)*320+(x//8)*8+(y & 7) for x, y in points}
        if not dirty <= covered:
            raise ValueError('V7 dirty byte missing from clear metadata')
        # Rebuild ordinary cell spans so the V7/V8 optimizer can run again.
        cells = sorted({o//8 for o in dirty})
        spans = []
        for cell in cells:
            if spans and cell == spans[-1][0]+spans[-1][1] and cell//40 == spans[-1][0]//40 and spans[-1][1] < 32:
                spans[-1][1] += 1
            else:
                spans.append([cell, 1])
        frames.append(FrameBuild(records, [(c*8 & 255, c*8 >> 8, n) for c, n in spans],
                                 sum(r[2] for r in records), len(points), [], colors))
    if len(frames) != manifest['frames']:
        raise ValueError('V7 reference frame count mismatch')
    scene = SimpleNamespace(name=manifest['name'],
        mesh=SimpleNamespace(vertices=[None]*manifest['vertices'], edges=[None]*manifest['edges'], faces=[None]*manifest['faces']),
        source_fps=manifest['source_fps'], sample_step=manifest['sample_step'],
        frames=[SimpleNamespace(source_frame=n) for n in manifest['source_frames']])
    return frames, scene, manifest
