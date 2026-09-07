#!/usr/bin/env python3
"""Build the separate horse_and_sunflower V7 test cartridge from its .blend.

FPS preferred by default. Does not change the twelve-demo cartridge directory.
Use --regenerate to recreate the authored scene from the original HiFi assets.
"""
import argparse
from pathlib import Path
import subprocess
import sys

from c643d import cli
from c643d.blender import require_blender


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default='blender')
    parser.add_argument('--tass', default='64tass')
    parser.add_argument('--cartconv', default='cartconv')
    parser.add_argument('--sample-step', type=int, default=3)
    parser.add_argument('--frame-ticks', type=int, default=6)
    parser.add_argument('--prefer', choices=('fps', 'ram'), default='fps')
    parser.add_argument('--regenerate', action='store_true')
    args = parser.parse_args()
    blender, version = require_blender(args.blender)
    print('Blender', version, flush=True)
    scene = root / 'examples/blender_horse_and_sunflower/horse_and_sunflower.blend'
    if args.regenerate or not scene.is_file():
        subprocess.run([blender, '--background', '--python-exit-code', '1', '--python',
                        str(scene.with_suffix('.py'))], cwd=root, check=True)
    stem = 'horse_and_sunflower-yunroll-cart-v7-scene' + ('-ram' if args.prefer == 'ram' else '')
    command = ['cart-stream', '--renderer', 'yunroll-cart-v7-scene', '--blend', str(scene),
               '--blender', blender, '--sample-step', str(args.sample_step),
               '--frame-ticks', str(args.frame_ticks), '--viewport-height', '192',
               '--visibility', 'surface_features', '--z-tolerance', '0.00008',
               '--prefer', args.prefer, '--no-text-overlay', '--tass', args.tass,
               '--cartconv', args.cartconv, '--output', stem,
               '--output-dir', str(root / 'examples/cart_horse_and_sunflower'),
               '--overwrite-policy', 'allow']
    return cli.main(command)


if __name__ == '__main__':
    sys.exit(main())
