#!/usr/bin/env python3
"""Convert Stanford's bundled ASCII PLY to OBJ without changing its geometry."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def convert():
    source = HERE / 'source/dragon_vrip_res4.ply.gz'
    data = gzip.decompress(source.read_bytes())
    header, body = data.decode('ascii').split('end_header\n', 1)
    if 'format ascii 1.0' not in header:
        raise ValueError('Expected the original Stanford ASCII PLY')
    counts = {line.split()[1]: int(line.split()[2])
              for line in header.splitlines() if line.startswith('element ')}
    rows = body.splitlines()
    vertices = [line.split()[:3] for line in rows[:counts['vertex']]]
    faces = []
    edges = set()
    for line in rows[counts['vertex']:]:
        values = list(map(int, line.split()))
        if values[0] != 3 or len(values) != 4:
            raise ValueError('Expected triangular faces')
        face = values[1:]
        if not all(0 <= v < len(vertices) for v in face):
            raise ValueError('Invalid vertex index')
        faces.append(face)
        edges.update(tuple(sorted((a, b))) for a, b in zip(face, face[1:] + face[:1]))
    if (len(vertices), len(faces)) != (5205, 11102):
        raise ValueError('Unexpected Stanford res4 geometry')
    lines = [
        '# Stanford Dragon, official dragon_vrip_res4.ply converted to OBJ.',
        '# Source: Stanford University Computer Graphics Laboratory.',
        '# See SOURCE.md for attribution, provenance and usage terms.',
        '# Coordinates, vertex order, triangle indices and winding are preserved.',
        'o STANFORD_DRAGON',
        *('v ' + ' '.join(v) for v in vertices),
        *('f ' + ' '.join(str(i + 1) for i in f) for f in faces),
    ]
    output = HERE / 'stanford_dragon.obj'
    output.write_text('\n'.join(lines) + '\n', encoding='ascii')
    stats = dict(source_member='dragon_recon/dragon_vrip_res4.ply',
                 source_ply_sha256=hashlib.sha256(data).hexdigest(),
                 obj_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                 vertices=len(vertices), edges=len(edges), triangles=len(faces),
                 additional_decimation=False, coordinates_preserved=True,
                 face_order_and_winding_preserved=True)
    (HERE / 'model.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    convert()
