#!/usr/bin/env python3
"""Compare V9 FPS/RAM carts with preserved V8 in PAL VICE.

Run build_v9_examples.py for both preferences first. V8 menu symbols can be
rebuilt into build/v8-baseline with the V8 example sources; its shipped CRT is
always used for the comparison. No source data or old cartridge is overwritten.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
from unittest.mock import patch
from pathlib import Path

from c643d import __version__, cli, cartuniform
from c643d.cartframes import load_menu_reference, load_scene_source
from c643d.toolchain import load_toolchain_settings
from c643d.v7reference import load_scene
from verify_cart_stream import verify
from profile_cart_stream import profile
from verify_cart_menu_launch import verify as verify_launch
from verify_v7_play_all import verify as verify_play_all


def main():
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', required=True)
    p.add_argument('--report', type=Path, default=root/'docs/benchmarks/v9/validation.json')
    a = p.parse_args()
    # Rebuild both V8 preferences outside examples. The shipped CRTs are frozen.
    for pref in ('fps','ram'):
        stem='c643d-demo-v0.6.8-yunroll-cart-v8-all'+('-ram' if pref=='ram' else '')
        args = cli.make_parser(load_toolchain_settings(root/'config/c643d.ini')).parse_args([
            'cart-demos', '--stream-renderer', 'yunroll-cart-v8', '--prefer', pref,
            '--output', stem, '--output-dir', str(root/'build/v8-baseline'),
            '--tass', a.tass, '--cartconv', a.cartconv, '--overwrite-policy', 'allow'])
        with patch("c643d.__version__", "0.6.8"):
            cartuniform.build(args, sources=load_menu_reference(root))
        original=(root/'examples/cart_demos'/f'{stem}.crt').read_bytes()
        fresh=(root/'build/v8-baseline'/f'{stem}.crt').read_bytes()
        # cartconv versions may differ only in the 32-byte cosmetic title.
        assert original[:32]+original[64:] == fresh[:32]+fresh[64:], 'V8 payload changed'
    baseline = root/'examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt'
    shipped = baseline.read_bytes()
    report = dict(toolkit_version=__version__, machine='PAL', clock_hz=985248,
                  method='Picture/colour regression and isolated diagnostic profiles only. A/B throughput is measured exclusively by benchmark_play_all.py using normal PLAY ALL, never F5. PAL VICE, not physical hardware.', menu=[], scenes={}, v8_rebuild_payload_identical=True, v8_ram_rebuild_payload_identical=True,
                  v8_shipped_sha256=hashlib.sha256(shipped).hexdigest())
    a.report.parent.mkdir(parents=True, exist_ok=True)
    def save():
        a.report.write_text(json.dumps(report, indent=2)+'\n')
    names = [demo.name for demo in load_menu_reference(root)]
    def compare(index):
        old = verify(baseline, a.vice, a.vice_data, menu_entry=index)
        row = dict(entry=index, name=names[index], v8=old)
        for pref in ('fps', 'ram'):
            suffix = '' if pref == 'fps' else '-ram'
            crt = root/f'examples/cart_demos/c643d-demo-v{__version__}-yunroll-cart-v9-all{suffix}.crt'
            new = verify(crt, a.vice, a.vice_data, menu_entry=index)
            row['v9_'+pref] = new
        return row
    with ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(compare, range(12)):
            report['menu'].append(row)
            print(row['name'], 'pictures/colours passed', flush=True)
            save()
    for name in ('dont_lose_your_marbles', 'horse_and_sunflower'):
        folder = root/('examples/cart_marbles' if name.startswith('dont') else 'examples/cart_horse_and_sunflower')
        suffixes = ('', '-clean') if name.startswith('dont') else ('',)
        for suffix in suffixes:
            old = folder/f'{name}-yunroll-cart-v8-scene{suffix}.crt'
            if name.startswith('dont'):
                frames, _, _ = load_scene_source(folder/f'{name}-yunroll-cart-v4-scene{suffix}.crt')
            else:
                frames, _, _ = load_scene(folder/f'{name}-yunroll-cart-v7-scene.crt')
            oracle = root/'build'/f'{old.stem}-stream-scene'/'oracle.json'
            oracle.parent.mkdir(parents=True, exist_ok=True)
            oracle.write_text(json.dumps([asdict(f) for f in frames]))
            result = {'v8': dict(validation=verify(old,a.vice,a.vice_data), profile=profile(old,a.vice,a.vice_data))}
            old_ram = old.with_name(old.stem+'-ram.crt')
            result['v8_ram'] = dict(validation=verify(old_ram,a.vice,a.vice_data,oracle_path=oracle), profile=profile(old_ram,a.vice,a.vice_data))
            for pref in ('fps', 'ram'):
                new = folder/f'{name}-yunroll-cart-v9-scene{suffix}{"-ram" if pref == "ram" else ""}.crt'
                result['v9_'+pref] = dict(validation=verify(new,a.vice,a.vice_data,oracle_path=oracle), profile=profile(new,a.vice,a.vice_data))
            report['scenes'][name+suffix] = result
            print(name+suffix, {k:round(v['profile']['frames_per_second'],3) for k,v in result.items()}, flush=True)
            save()
    menu = root/f'examples/cart_demos/c643d-demo-v{__version__}-yunroll-cart-v9-all.crt'
    report['launch'] = verify_launch(menu, a.vice, a.vice_data)
    report['play_all'] = verify_play_all(menu, a.vice, a.vice_data)
    save()


if __name__ == '__main__':
    main()
