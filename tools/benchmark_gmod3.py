#!/usr/bin/env python3
"""Reproduce GMod3 bank/copy probes and matched HORS-V3 comparisons in PAL VICE."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from c643d.gmod3_probe import build as build_probe, measure, verify_reset
from c643d.gmod3_validation import display_capture
from c643d.gmod3_v3 import assemble_cartridge as build_gmod3
from c643d.hors_v3 import assemble_cartridge as build_easyflash
from c643d.pipeline import FrameBuild
from c643d.objio import load_obj
from c643d.shapes import torus
from verify_cart_stream import verify
from verify_hors_v3_controls import verify_controls
from verify_gmod3_ui import verify as verify_ui
from profile_cart_stream import profile


def executable(value):
    found = shutil.which(value)
    if not found:
        raise ValueError(f'Executable not found: {value}')
    return str(Path(found).resolve())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True, help='new output directory for reproducible evidence')
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, required=True)
    p.add_argument('--probes-only', action='store_true')
    p.add_argument('--refreshes', type=int, default=1600)
    a = p.parse_args()
    out = a.out.resolve()
    if out.exists():
        p.error('--out must be a new directory; existing evidence is preserved')
    if a.refreshes < 1600:
        p.error('--refreshes must be at least 1600 to capture complete loops')
    tass, conv, vice = map(executable, (a.tass, a.cartconv, a.vice))
    data = str(a.vice_data.resolve())
    out.mkdir(parents=True)
    report = dict(format='c643d-gmod3-checkpoint1', probes=[], examples={}, passed=False,
        tool_versions=dict(tass=subprocess.run([tass,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
            vice=subprocess.run([vice,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]),
        scope='PAL x64sc emulation; read-only GMod3; no physical hardware or audio playback result')
    for size in (2,4,8,16):
        crt = build_probe(ROOT, out/'probes', tass=tass, cartconv=conv, size_mib=size)
        result = measure(crt, vice=vice, vice_data=data)
        if size == 16:
            result['reset'] = verify_reset(crt, vice=vice, vice_data=data)
        report['probes'].append(result)
        print(f'PASS: {size} MiB, {result["banks_verified"]} banks, '
              f'{result["fixed_store_cycles"]:g}/{result["indexed_store_cycles"]:g} cycle bank stores', flush=True)
    baseline = build_probe(ROOT, out/'probes', tass=tass, cartconv=conv, cart_type='easyflash')
    report['probes'].append(measure(baseline, vice=vice, vice_data=data))
    if not a.probes_only:
        for demo in ('metallic_torus', 'golden_dragon'):
            stem = 'gmod3_'+demo
            supplied = ROOT/f'tests/fixtures/gmod3/{stem}-oracle.json.gz'
            if not supplied.exists():
                raise ValueError('Missing frozen bank-benchmark fixture: '+str(supplied))
            oracle = out/f'{stem}-oracle.json'
            oracle.write_bytes(gzip.decompress(supplied.read_bytes()))
            frames = [FrameBuild(**f) for f in json.loads(oracle.read_text())]
            mesh = torus() if demo == 'metallic_torus' else load_obj(
                ROOT/'examples/stanford_dragon/stanford_dragon.obj',name='STANFORD DRAGON')
            opts = dict(tass=tass,cartconv=conv,outdir=out/demo,colors=True,color_index=1)
            gmod, gm = build_gmod3(ROOT, frames, mesh, stem=stem, size_mib=2 if demo == 'metallic_torus' else 16,
                first_bank=4 if demo == 'metallic_torus' else 1023, **opts)
            ef, em = build_easyflash(ROOT, frames, mesh, stem='easyflash_'+demo, interactive=True,
                include_starfield=False, **opts)
            if [f['sha256'] for f in gm['frame_data']] != [f['sha256'] for f in em['frame_data']]:
                raise AssertionError('Backend comparison changed the encoded picture payloads')
            pair = dict(encoded_payloads_identical=True, oracle_sha256=hashlib.sha256(oracle.read_bytes()).hexdigest())
            for kind, crt in [('gmod3',gmod),('easyflash',ef)]:
                pair[kind] = dict(pixels=verify(crt,vice,data,cycles=2,oracle_path=oracle),
                    profile=profile(crt,vice,data),
                    display=display_capture(crt,oracle,vice=vice,vice_data=data,
                        out=out/demo/'previews',refreshes=a.refreshes))
            pair['controls'] = verify_controls(gmod,oracle,vice,data)
            pair['startup'] = verify_ui(gmod,vice,data,out/demo/'startup')
            pair['display_fps_change_percent'] = 100*(pair['gmod3']['display']['displayed_fps']/pair['easyflash']['display']['displayed_fps']-1)
            report['examples'][demo] = pair
            print(f'PASS: {demo}, displayed GMod3 {pair["gmod3"]["display"]["displayed_fps"]:.3f} '
                  f'vs EasyFlash {pair["easyflash"]["display"]["displayed_fps"]:.3f} FPS',flush=True)
        # A second real-payload crossing covers the 8-bit boundary independently
        # of the Dragon's 1023/1024 crossing.
        oracle = out/'gmod3_metallic_torus-oracle.json'
        frames = [FrameBuild(**f) for f in json.loads(oracle.read_text())]
        crt, meta = build_gmod3(ROOT,frames,torus(),tass=tass,cartconv=conv,outdir=out/'boundaries',
            stem='gmod3_boundary_255',size_mib=4,first_bank=255,colors=True)
        if not min(d['bank'] for d in meta['frame_data']) <= 255 < max(d['bank'] for d in meta['frame_data']):
            raise AssertionError('Boundary workload did not cross 255/256')
        report['boundary_255_256'] = verify(crt,vice,data,cycles=2,oracle_path=oracle)
    report['passed'] = True
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'All requested checks passed: {out / "results.json"}',flush=True)


if __name__ == '__main__':
    main()
