#!/usr/bin/env python3
"""Check saved HORS-V3 evidence, or repeat the PAL VICE measurements."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'docs/benchmarks/hors-v3-preview'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Check saved source, cartridge, and evidence hashes (default)')
    mode.add_argument('--run', action='store_true', help='Run VICE pixel checks and displayed-FPS measurements')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data', type=Path)
    parser.add_argument('--cartridge-dir', type=Path, default=ROOT / 'examples/hors_v3_preview/cartridges')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/hors-v3-verification')
    parser.add_argument('--variants', nargs='+')
    args = parser.parse_args()
    record = json.loads((RECORDS / 'summary.json').read_text())
    if not args.run:
        for name, expected in record['sha256'].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            if actual != expected:
                raise SystemExit(f'V3 evidence is stale: {name}')
        for row in record['results']:
            assert row['pixel_match'] and row['color_match'] and row['picture_coverage_complete']
            if row.get('background_controls'):
                bg = row['background_controls']
                assert bg['passed'] and bg['sha256'] == row['sha256']
                assert bg['keys']['passed'] and bg['palette']['passed']
                assert all(v['color_match'] and v['border_background_match']
                           for v in bg['measurements'].values())
        print(f"HORS-V3 evidence matches source and all {len(record['results'])} cartridges.")
        print('This checks saved evidence; it does not rerun the full release suite.')
        return
    if not args.vice_data:
        parser.error('--run requires --vice-data')
    known = {r['id'] for r in record['results']}
    if args.variants and set(args.variants) - known:
        parser.error('Unknown variants: ' + ', '.join(sorted(set(args.variants) - known)))
    from run_sande_perfs import measure
    from verify_cart_stream import verify
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for row in record['results']:
        if args.variants and row['id'] not in args.variants:
            continue
        stem = row['stem']
        cart = args.cartridge_dir.resolve() / (stem + '.crt')
        oracle = args.cartridge_dir.resolve() / (stem + '-oracle.json')
        if not oracle.exists():
            oracle = ROOT / row['oracle']
        proof = verify(cart, args.vice, str(args.vice_data.resolve()), 2,
                       out / 'previews', oracle_path=oracle)
        (out / (stem + '-verification.json')).write_text(json.dumps(proof, indent=2) + '\n')
        result = measure(cart, oracle, args.vice, args.vice_data.resolve(), 1504)
        (out / (stem + '-display.json')).write_text(json.dumps(result, indent=2) + '\n')
        manifest = json.loads(cart.with_name(stem + '-manifest.json').read_text())
        if manifest.get('interactive_cart'):
            from verify_hors_v3_controls import verify_controls
            controls = verify_controls(cart, oracle, args.vice, args.vice_data.resolve())
            (out / (stem + '-controls.json')).write_text(json.dumps(controls, indent=2) + '\n')
            if manifest['interactive_cart'].get('background_override'):
                from verify_hors_v3_background import verify_keys, verify_palette, measure_background
                background = dict(sha256=result['sha256'],
                    keys=verify_keys(cart,oracle,args.vice,args.vice_data.resolve()),
                    palette=verify_palette(cart,oracle,args.vice,args.vice_data.resolve()),
                    measurements={})
                for name, ticks in [('steady',None),('auto-50',50),('auto-1',1)]:
                    background['measurements'][name] = measure_background(
                        cart,oracle,args.vice,args.vice_data.resolve(),cycle_ticks=ticks)
                background['passed'] = True
                (out / (stem + '-background.json')).write_text(json.dumps(background,indent=2)+'\n')
        print(f"{row['id']}: {result['display_fps']:.3f} displayed FPS; "
              f"{proof['verified_frames']} completed pictures verified", flush=True)
    print(f'Fresh results: {out}')


if __name__ == '__main__':
    main()
