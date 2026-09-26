#!/usr/bin/env python3
"""Build a private V4/V5 EasyFlash scene pair and measure it outside the checkout."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

from c643d import cli, pipeline
from compare_cart_stream import compare, load_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene', type=Path, help='exported .c643dscene input')
    parser.add_argument('--out', type=Path, required=True, help='new private work/evidence directory outside the checkout')
    parser.add_argument('--name', default='Nightdrive Test', help='report title; does not change the source')
    parser.add_argument('--tass', default='64tass')
    parser.add_argument('--cartconv', default='cartconv')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data')
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    root, out, scene = cli.ROOT.resolve(), args.out.expanduser().resolve(), args.scene.expanduser().resolve()
    if out == root or root in out.parents:
        parser.error('--out must be outside the checkout to keep private assets out')
    if scene.suffix.lower() != '.c643dscene' or not scene.is_file():
        parser.error('scene must be an existing .c643dscene export')
    if out.exists():
        parser.error('--out must be a new directory; prior evidence is preserved')
    executables = {}
    for name in ('tass', 'cartconv', 'vice'):
        found = shutil.which(getattr(args, name))
        if not found:
            parser.error('Executable not found: '+getattr(args, name))
        executables[name] = str(Path(found).resolve())
    digest = hashlib.sha256(scene.read_bytes()).hexdigest()
    out.mkdir(parents=True)
    shutil.copytree(root/'c64', out/'c64')
    shutil.copy2(root/'VERSION', out/'VERSION')
    original = {name: getattr(cli, name) for name in ('ROOT', 'C64', 'BUILD', 'GENERATED')}
    original_builder = pipeline.build_scene_frames
    cached = None

    def frozen(*positional, **keywords):
        nonlocal cached
        if cached is None:
            cached = original_builder(*positional, **keywords)
        return deepcopy(cached)

    commands, cartridges = [], []
    try:
        cli.ROOT, cli.C64, cli.BUILD, cli.GENERATED = out, out/'c64', out/'build', out/'generated'
        pipeline.build_scene_frames = frozen
        for renderer, destination in [('hors-v4', 'baseline'), ('hors-v5', 'candidate')]:
            stem = 'scene-'+renderer
            argv = ['build', '--no-config', '--scene', str(scene), '--renderer', renderer,
                '--cart-type', 'easyflash', '--output', stem, '--output-dir', str(out/destination),
                '--tass', executables['tass'], '--cartconv', executables['cartconv']]
            commands.append(argv)
            result = cli.main(argv)
            if result:
                raise RuntimeError(f'{renderer} build failed with status {result}')
            cartridges.append(out/destination/(stem+'.crt'))
    finally:
        pipeline.build_scene_frames = original_builder
        for name, value in original.items():
            setattr(cli, name, value)
    if hashlib.sha256(scene.read_bytes()).hexdigest() != digest:
        raise RuntimeError('Input scene changed during the benchmark')
    (out/'build-input.json').write_text(json.dumps(dict(name=args.name,
        scene=scene.name, scene_sha256=digest, commands=commands,
        compilation='one shared host frame set, independent V4/V5 builds'), indent=2)+'\n')
    result = compare(load_case(cartridges[0], out), load_case(cartridges[1], out),
        vice=executables['vice'], data=args.vice_data, out=out/'comparison', capture=args.capture)
    report = out/'comparison/comparison.md'
    report.write_text(report.read_text().replace('# Matched renderer comparison', '# '+args.name, 1))
    print(report)
    return 0 if result['performance_gate_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
