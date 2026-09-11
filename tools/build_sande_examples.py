#!/usr/bin/env python3
"""Rebuild Sande's standalone OBJ demos with a pinned, config-independent recipe."""
import argparse
import hashlib
import json
from pathlib import Path

from c643d import cli
from c643d.cartridge import inspect_easyflash_crt

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'examples/demos_sande'
SET_ID = 'sande_models'
MODELS = tuple(json.loads((SOURCES / 'recipe.json').read_text())['models'])
RENDERERS = ('hors-render-v1', 'hors-render-v2')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output_dir=SOURCES, *, models=MODELS, renderer='hors-render-v2',
          prefer='fps', tass='64tass', cartconv='cartconv', legacy_cart=False, interactive=False,
          source_colors=False):
    if interactive and renderer != 'hors-render-v2':
        raise ValueError('Interactive Sande carts require hors-render-v2')
    if interactive and source_colors:
        raise ValueError('Source-material colour carts and interactive monochrome carts are separate variants')
    recipe = json.loads((SOURCES / 'recipe.json').read_text())
    build_arguments = list(recipe['build_arguments'])
    if source_colors:
        build_arguments.remove('--no-color')
        color_arg = build_arguments.index('--color')
        del build_arguments[color_arg:color_arg + 2]
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name in models:
        stem = name + '-' + renderer + ('-ram' if prefer == 'ram' else '')
        if interactive:
            stem += '-interactive'
        if source_colors:
            stem += '-color'
        if legacy_cart:
            stem += '-legacy'
        source = SOURCES / (name + '.obj')
        argv = ['build', '--no-config', '--obj', str(source), '--name', name,
                '--renderer', renderer, '--prefer', prefer,
                '--output', stem, '--output-dir', str(output_dir),
                '--tass', tass, '--cartconv', cartconv, '--overwrite-policy', 'allow',
                *build_arguments]
        if legacy_cart:
            argv.append('--legacy-cart')
        if interactive:
            argv.append('--interactive-cart')
        status = cli.main(argv)
        if status:
            raise RuntimeError(f'{name}: build failed ({status})')
        crt = output_dir / (stem + '.crt')
        manifest_path = output_dir / (stem + '-manifest.json')
        manifest = json.loads(manifest_path.read_text())
        manifest.setdefault('runtime_work', f'build/{stem}-stream-v10')
        manifest['toolkit_version'] = (ROOT / 'VERSION').read_text().strip()
        if interactive:
            manifest['sande_controls'] = dict(
                rotation='CRSR left/right or joystick port 1/2 left/right; direction persists after release',
                foreground='F3', background='F4 / SHIFT+F3', border='F8: black/follow background', reset='F2',
                cycle='F5', slower='F6', faster='F7',
                independent_border='CTRL+F7',
                f4_links_background_and_border=True,
                defaults=dict(foreground='white', background='black', border='black'),
                source='tools/c643d/sande_controls.py')
        topology = {key: manifest[key] for key in ('vertices', 'edges', 'faces')}
        if topology != recipe['models'][name]['topology']:
            raise ValueError(f'{name}: source topology changed: {topology}')
        manifest['source_recipe'] = dict(
            path='examples/demos_sande/recipe.json', author='Sande',
            sha256=sha(SOURCES / 'recipe.json'),
            files={name + ext: sha(SOURCES / (name + ext)) for ext in ('.obj', '.mtl')},
            build_arguments=build_arguments)
        if source_colors:
            from c643d.objio import load_mtl
            manifest['sande_material_colors'] = dict(
                source=name + '.mtl', mode='original MTL diffuse colours mapped to the C64 palette',
                palette=load_mtl(SOURCES / (name + '.mtl')),
                monochrome_overrides_removed=['--no-color', '--color white'])
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        info = inspect_easyflash_crt(crt, require_metadata=not legacy_cart)
        results.append(dict(model=name, cartridge=crt.name, sha256=sha(crt),
                            **topology, frames=manifest['frames'], metadata=info))
        print(f'{crt.name}: {topology}, {manifest["frames"]} samples', flush=True)
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=SOURCES)
    p.add_argument('--models', nargs='+', choices=MODELS, default=MODELS)
    p.add_argument('--renderer', choices=RENDERERS, default='hors-render-v2')
    p.add_argument('--prefer', choices=('fps', 'ram'), default='fps')
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--legacy-cart', action='store_true')
    variants = p.add_mutually_exclusive_group()
    variants.add_argument('--interactive', action='store_true', help='Separate v2 carts with cursor/joystick direction and F-key palette controls')
    variants.add_argument('--source-colors', action='store_true', help='Separate -color carts using the original OBJ/MTL diffuse colours')
    a = p.parse_args(argv)
    return build(**vars(a))


if __name__ == '__main__':
    main()
