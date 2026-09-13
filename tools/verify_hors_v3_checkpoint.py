#!/usr/bin/env python3
"""Reproduce V3 default, texture, gradient and fragmented-metadata checks in VICE."""
import argparse
import json
import math
from pathlib import Path
from c643d import cli
from c643d.hors_v3 import assemble_cartridge
from c643d.hors_v2_stable import encoder as v2_encoder
from c643d.mesh import Mesh
from c643d.surface_fill import frame_from_pixels
from verify_cart_stream import verify
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def deform_scene(path):
    frames = []
    for i in range(180):
        t = i * math.tau / 180
        vertices = [[x+4*math.sin(t+j), y+3*math.cos(t+j), 40+z+2*math.sin(t*2+j)]
                    for j, (x,y,z) in enumerate([(-10,-8,0),(10,-8,0),(0,10,0),(-8,-6,-2),(8,-6,-2),(0,8,-2)])]
        frames.append(dict(source_frame=i+1, vertices=vertices,
                           projection=dict(fx=180,fy=180,cx=128,cy=96)))
    path.write_text(json.dumps(dict(format='c643dscene',version=1,name='DEFORM 180',
        source=dict(fps=25,sample_step=1),topology=dict(faces=[[0,2,1],[3,5,4]],face_colors=[2,5]),frames=frames)))


def fragmented_frames():
    frames = []
    for phase in range(4):
        bits = np.zeros((192,320), dtype=bool)
        screen = np.full((24,40), 0x10, dtype=np.uint8)
        for cy in range(24):
            for cx in range(phase % 2,32,2):
                bits[cy*8+phase,cx*8+phase] = True
                screen[cy,cx] = (2 if (cx+cy+phase)%3 else 5) << 4
        frames.append(frame_from_pixels(bits, screen))
    return frames


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data')
    a = p.parse_args()
    out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    scene = out/'deform-180.c643dscene'; deform_scene(scene)
    cases = [
        ('default-cube', ['--shape','cube','--frames','8']),
        ('deform-180', ['--scene',str(scene)]),
        ('textured', ['--obj',str(ROOT/'examples/hors_v3_preview/texture-demo/pretzel-test-texture.obj'), '--surface-fill','textured','--frames','4']),
        ('custom-gradient', ['--shape','torus','--surface-fill','metallic','--surface-ramp','brown,orange,yellow,white','--interactive-cart','--frames','8']),
        ('purple-indexed', ['--shape','torus','--surface-fill','metallic','--surface-palette','purple','--compact-color-dictionary','--frames','4']),
    ]
    results = {}
    for name, flags in cases:
        code = cli.main(['build', *flags, '--output',name,'--output-dir',str(out),
            '--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow'])
        if code: raise RuntimeError(f'{name}: build failed ({code})')
        manifest = json.loads((out/(name+'-manifest.json')).read_text())
        assert manifest['renderer'] == 'hors-renderer-v3'
        if name == 'deform-180': assert manifest['source_frames'] == list(range(1,181))
        results[name] = verify(out/(name+'.crt'),a.vice,a.vice_data,cycles=1)
    frames = fragmented_frames()
    try:
        v2_encoder()(frames[0])
    except ValueError as exc:
        assert '384 clear spans' in str(exc), str(exc)
        v2_error = str(exc)
    else:
        raise AssertionError('Fragmentation fixture no longer reproduces the V2 failure')
    crt, manifest = assemble_cartridge(ROOT,frames,Mesh('FRAGMENTED',[(0,0,0)],[]),
        tass=a.tass,cartconv=a.cartconv,outdir=out,stem='fragmented',colors=True)
    assert manifest['color_policy']['clear_metadata_compacted_frames'] == 4
    results['fragmented'] = verify(crt,a.vice,a.vice_data,cycles=2)
    results['fragmented']['v2_error'] = v2_error
    # Interactive controls must preserve all nonblack shades on arbitrary ramps.
    from verify_hors_v3_background import verify_keys, verify_palette
    interactive = out/'custom-gradient.crt'
    oracle = out/'custom-gradient-oracle.json'
    results['custom-gradient-keys'] = verify_keys(interactive,oracle,a.vice,a.vice_data)
    results['custom-gradient-backgrounds'] = verify_palette(interactive,oracle,a.vice,a.vice_data)
    report = dict(passed=True, results=results)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
