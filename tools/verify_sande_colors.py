#!/usr/bin/env python3
"""Verify the original Sande MTL palette and every completed colour-cart picture."""
import argparse
import json
from pathlib import Path

from build_sande_examples import ROOT, SOURCES, MODELS, SET_ID, sha
from c643d.cartridge import inspect_easyflash_crt
from c643d.colors import c64_color_name
from c643d.objio import load_obj
from verify_cart_stream import expected_frame, verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', default='/usr/local/share/vice')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    results = []
    recipe = json.loads((SOURCES / 'recipe.json').read_text())
    frame_count = int(recipe['build_arguments'][recipe['build_arguments'].index('--frames') + 1])
    for model in MODELS:
        crt = SOURCES / (model + '-hors-render-v2-color.crt')
        meta = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
        assert meta['source_recipe']['sha256'] == sha(SOURCES / 'recipe.json')
        for filename, digest in meta['source_recipe']['files'].items():
            assert sha(SOURCES / filename) == digest, filename
        assert not any(flag in meta['source_recipe']['build_arguments'] for flag in ('--no-color', '--color'))
        source = load_obj(SOURCES / (model + '.obj'))
        assert source.source_colors, 'No source materials loaded: ' + model
        frames = json.loads((ROOT / meta['runtime_work'] / 'oracle.json').read_text())
        assert len(frames) == frame_count
        observed = set()
        for frame in frames:
            bitmap, colors = expected_frame(frame, meta['screen_color'])
            observed.update(colors[cell] >> 4 for cell in range(960) if any(bitmap[cell * 8:cell * 8 + 8]))
        allowed = set(source.source_colors)
        if not source.source_colors_cover_all_edges:
            allowed.add(meta['screen_color'] >> 4)
        assert observed and observed <= allowed, (model, observed, allowed)
        if allowed != {1}:
            assert observed != {1}, 'Material colours were replaced by the white default'
        if len(allowed) == 1:
            assert observed == allowed
        proof = verify(crt, a.vice, a.vice_data, cycles=2, capture=a.out / 'previews')
        result = dict(cartridge=crt.name, sha256=sha(crt), metadata=inspect_easyflash_crt(crt, require_metadata=True),
                      source_palette=[c64_color_name(c) for c in sorted(allowed)],
                      observed_foregrounds=[c64_color_name(c) for c in sorted(observed)],
                      source_materials_verified=True, verification=proof)
        (a.out / (model + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(model, 'material colours and', proof['verified_frames'], 'pictures PASS', flush=True)
    (a.out / 'summary.json').write_text(json.dumps(dict(set_id=SET_ID, passed=True, results=results), indent=2) + '\n')


if __name__ == '__main__':
    main()
