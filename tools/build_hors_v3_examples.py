#!/usr/bin/env python3
"""Rebuild the opt-in HORS-V3 surface preview and its V2 reference cartridges."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / 'examples/hors_v3_preview'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tass', default='64tass')
    parser.add_argument('--cartconv', default='cartconv')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/hors-v3-preview')
    parser.add_argument('--variants', nargs='+', help='Variant IDs from recipe.json; default all')
    args = parser.parse_args()
    rows = json.loads((EXAMPLES / 'recipe.json').read_text())['variants']
    known = {row['id'] for row in rows}
    if args.variants and set(args.variants) - known:
        parser.error('Unknown variants: ' + ', '.join(sorted(set(args.variants) - known)))
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if args.variants and row['id'] not in args.variants:
            continue
        stem = row['stem']
        if row['id'] == 'v2-metallic-reference':
            # Test harness only: replay the saved V3 host picture oracle through
            # the unmodified V2 assembler. V2 gets no new user-facing fill flag.
            from c643d.hors_v2_stable import assemble_cartridge
            from c643d.pipeline import FrameBuild
            from c643d.objio import load_obj
            source = ROOT / row['oracle']
            frames = [FrameBuild(**f) for f in json.loads(source.read_text())]
            mesh = load_obj(ROOT / 'examples/demos_sande/sande_pretzel.obj', 'SANDE PRETZEL')
            assemble_cartridge(ROOT, frames, mesh, tass=args.tass, cartconv=args.cartconv,
                               outdir=out, stem=stem, colors=True, optimize=False, prefer='fps')
            shutil.copy2(source, out / (stem + '-oracle.json'))
            continue
        command = [sys.executable, str(ROOT / 'c643d.py'), 'build',
                   '--renderer', row['renderer'], '--name', 'SANDE PRETZEL',
                   '--obj', str(ROOT / row['obj']), '--obj-up', 'y', '--spin-axis', 'y',
                   '--frames', str(row['frames']), '--camera', '110', '--focal', '180',
                   '--margin', '4', '--max-fit-scale', '1.4', '--prefer', 'fps',
                   '--output-dir', str(out), '--output', stem,
                   '--tass', args.tass, '--cartconv', args.cartconv, *row['arguments']]
        subprocess.run(command, cwd=ROOT, check=True)
        oracle = out / (stem + '-oracle.json')
        if not oracle.exists():
            manifest = json.loads((out / (stem + '-manifest.json')).read_text())
            shutil.copy2(ROOT / manifest['runtime_work'] / 'oracle.json', oracle)
    print(f'Built cartridges and independent picture oracles: {out}')


if __name__ == '__main__':
    main()
