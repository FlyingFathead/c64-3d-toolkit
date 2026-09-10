#!/usr/bin/env python3
"""Build current standalone hors-render-v1 examples without Blender."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from c643d.cartframes import load_menu_reference
from c643d.cartstream import assemble_cartridge

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    a = p.parse_args()
    for row in json.loads((ROOT/'examples/examples.json').read_text()):
        args = list(row['args'])
        args[args.index('--renderer')+1] = 'hors-render-v1'
        subprocess.run([sys.executable, str(ROOT/'c643d.py'), 'build', *args,
                        '--output', row['name']+'-hors-render-v1', '--output-dir',
                        str(ROOT/'examples'/row['directory']), '--no-config',
                        '--tass', a.tass, '--cartconv', a.cartconv,
                        '--overwrite-policy', 'allow'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT/'c643d.py'), 'build', '--object',
                    'horse_head_hifi', '--renderer', 'hors-render-v1', '--frames', '192',
                    '--strict-frames', '--viewport-height', '192', '--text-overlay',
                    '--output', 'horse_head_hifi-hors-render-v1', '--output-dir',
                    str(ROOT/'examples/hifi_showcase'), '--no-config', '--tass', a.tass,
                    '--cartconv', a.cartconv, '--overwrite-policy', 'allow'], cwd=ROOT, check=True)
    # Reuse the checked-in vector samples, avoiding a Blender physics rebake.
    d = next(d for d in load_menu_reference(ROOT) if d.name == 'FALLING CUBES')
    mesh = SimpleNamespace(name=d.name, vertices=[], edges=[], faces=[])
    for colors, stem in ((True, 'falling_cubes_c64_color-hors-render-v1'),
                         (False, 'falling_cubes_c64-hors-render-v1')):
        from dataclasses import replace
        frames = d.frames if colors else [replace(f, color_spans=[]) for f in d.frames]
        crt, manifest = assemble_cartridge(ROOT, frames, mesh, tass=a.tass, cartconv=a.cartconv,
            outdir=ROOT/'examples/blender_falling_cubes', stem=stem,
            colors=colors, color_index=d.screen>>4, renderer='hors-render-v1', hud=d.hud)
        for field in ('vertices', 'edges', 'faces'):
            manifest[field] = None  # Geometry counts unavailable in this vector-only reference.
        manifest['source'] = 'assets/v4-menu-vector-reference.json.gz'
        manifest['source_note'] = 'Preserved 18 vector samples, rendered by hors-render-v1; no Blender rebake.'
        crt.with_name(crt.stem+'-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')

if __name__ == '__main__':
    main()
