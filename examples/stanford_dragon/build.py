#!/usr/bin/env python3
"""Build all six Stanford Dragon examples with the current HORS-V3 pipeline."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tass', default='64tass')
    parser.add_argument('--cartconv', default='cartconv')
    parser.add_argument('--variants', nargs='+', choices=('wireframe', 'metallic', 'blue', 'red', 'green', 'golden'))
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/stanford-dragon')
    args = parser.parse_args()
    recipe = json.loads((HERE / 'recipe.json').read_text())
    out = args.output_dir.resolve()
    for row in recipe['variants']:
        if args.variants and row['id'] not in args.variants:
            continue
        print('Building ' + row['id'] + '...', flush=True)
        command = [sys.executable, str(ROOT / 'c643d.py'), 'build',
                   '--renderer', recipe['renderer'], '--obj', str(HERE / recipe['obj']),
                   '--name', recipe['name'], *recipe['common_arguments'], *row['arguments'],
                   '--output-dir', str(out), '--output', row['stem'],
                   '--tass', args.tass, '--cartconv', args.cartconv,
                   '--overwrite-policy', 'allow']
        subprocess.run(command, cwd=ROOT, check=True)
        manifest = json.loads((out / (row['stem'] + '-manifest.json')).read_text())
        if manifest['renderer'] != recipe['renderer'] or manifest['frames'] != 128:
            raise RuntimeError('Build did not retain the requested HORS-V3 renderer and orientations')
        if (manifest['vertices'], manifest['edges'], manifest['faces']) != (5205, 15796, 11102):
            raise RuntimeError('Build changed the Stanford Dragon geometry counts')
        # Keep the independent host oracle compact without changing any pictures.
        oracle = out / (row['stem'] + '-oracle.json')
        if not oracle.exists():
            # The standalone wireframe pipeline keeps its oracle beside the
            # staged runtime; surface builds already export it to output-dir.
            oracle.write_bytes((ROOT / manifest['runtime_work'] / 'oracle.json').read_bytes())
        with oracle.with_suffix('.json.gz').open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
                zipped.write(oracle.read_bytes())
        oracle.unlink()
    print('Cartridges, symbols, manifests and host oracles: ' + str(out))


if __name__ == '__main__':
    main()
