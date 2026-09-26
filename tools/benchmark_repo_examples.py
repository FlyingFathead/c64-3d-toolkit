#!/usr/bin/env python3
"""Benchmark the frozen public demo corpus, Dragon and effect-free SAKU logos."""
import argparse
from dataclasses import asdict, replace
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from benchmark_renderer_history import ROOT, capacity_reason, picture_hash, save, sha
from compare_renderers import METHODS, EXTRA_METHODS, fingerprints

EXAMPLES = {
    'dragon-wireframe': ('stanford_dragon', 'stanford_dragon-wireframe-hors-v3', 'DRAGON WIREFRAME'),
    'dragon-metallic': ('stanford_dragon', 'stanford_dragon-metallic-hors-v3', 'DRAGON METALLIC'),
    'saku-solid': ('saku_2026', 'saku_2026-solid', 'SAKU SOLID LOGO ONLY'),
    'saku-gradient': ('saku_2026', 'saku_2026-gradient', 'SAKU GRADIENT LOGO ONLY'),
}
ALL_METHODS = list(dict.fromkeys(m for m, _ in METHODS + EXTRA_METHODS if m!='hors-v5-ef'))


def geometry_clears(frame):
    """Undo saved backend-specific clearing without changing picture records.

    Published oracles may carry V7 byte-range flags. Earlier backends require
    ordinary geometry cell runs; every backend then applies its own clear plan.
    """
    from c643d.pipeline import decode_record_points
    cells = {(x // 8, y // 8) for record in frame.records for x, y in decode_record_points(record)}
    if any(not (0 <= x < 40 and 0 <= y < 24) for x, y in cells):
        raise ValueError('Picture extends outside the common 320x192 comparison area')
    spans = []
    for cy in range(24):
        row = sorted(cx for cx, y in cells if y == cy)
        if not row:
            continue
        start = previous = row[0]
        for cx in row[1:] + [None]:
            if cx is not None and cx == previous + 1:
                previous = cx
                continue
            offset, count = cy * 320 + start * 8, previous - start + 1
            while count:
                part = min(count, 32)
                spans.append((offset & 255, offset >> 8, part))
                offset += part * 8
                count -= part
            if cx is not None:
                start = previous = cx
    return replace(frame, clear_spans=spans)


def freeze_example(key, destination, root=ROOT):
    from c643d.cartuniform import Demo
    from c643d.pipeline import FrameBuild
    from c643d.font import bitmap_text
    group, stem, name = EXAMPLES[key]
    path = root / 'examples' / group / 'cartridges' / (stem + '-oracle.json.gz')
    manifest = path.with_name(stem + '-manifest.json')
    metadata = json.loads(manifest.read_text())
    original = [FrameBuild(**f) for f in json.loads(gzip.decompress(path.read_bytes()))]
    frames = [geometry_clears(f) for f in original]
    screen = metadata['screen_color']
    before = picture_hash(original, screen)
    if len(frames) != metadata['frames'] or picture_hash(frames, screen) != before:
        raise ValueError('Saved reference normalization changed complete pictures')
    demo = Demo(name, frames, metadata['colors'], screen, bitmap_text(name, 31),
                path.relative_to(root).as_posix(), sha(path), border=metadata['border_color'])
    row = asdict(demo)
    row['hud'] = demo.hud.hex()
    destination.write_bytes(gzip.compress(json.dumps(dict(format='c643d-vector-reference-v1', demos=[row])).encode(), mtime=0))
    return dict(name=name, frames=len(frames), source=demo.source, source_sha256=sha(path),
                manifest_sha256=sha(manifest), pictures_sha256=before, reference_sha256=sha(destination))


def collect(work, cases, methods=None):
    """Retain every method/case row; require both timing and complete verification."""
    from c643d.cartpaths import menu_manifest_path
    output = {c['name']: dict(c, rows=[]) for c in cases}
    for method, preference in METHODS + EXTRA_METHODS:
        if method=='hors-v5-ef':continue
        if methods is not None and method not in methods:continue
        key = method + ('-ram' if preference == 'ram' else '')
        reports = work / 'results'
        def read(suffix, default):
            path = reports / (key + suffix)
            return json.loads(path.read_text()) if path.exists() else default
        timing = read('-play-all.json', {})
        entries = {e['name']: e for e in timing.get('entries', [])}
        unsupported = {e['name']: e['reason'] for e in read('-unsupported.json', [])}
        crt = work / 'carts' / (key + '.crt')
        metadata = json.loads(menu_manifest_path(crt).read_text()) if crt.exists() else {}
        streams = {e['name']: e for e in metadata.get('streamed_entries', [])}
        for name, case in output.items():
            row = dict(method=method, preference=preference)
            try:
                if name in unsupported:
                    if capacity_reason(unsupported[name]) is None:
                        raise ValueError('Unrecognized capacity reason: ' + unsupported[name])
                    if name in entries:
                        raise ValueError('Case appears as both supported and unsupported')
                    row.update(status='capacity', reason=unsupported[name])
                else:
                    entry = entries[name]
                    proof = read(f"-pixels-{entry['entry']:02d}.json", {})
                    stream = streams[name]
                    oracle = json.loads((work / 'source' / stream['work'] / 'oracle.json').read_text())
                    if not (proof.get('pixel_match') and proof.get('color_match') and
                            proof.get('orientations') == case['frames'] == entry['frame_count'] and
                            picture_hash(oracle, stream['screen_color']) == case['pictures_sha256']):
                        raise ValueError('Complete picture/colour/order verification failed')
                    row.update(status='passed', timing=entry, verification=proof,
                               crt_bytes=crt.stat().st_size, crt_sha256=sha(crt))
            except (OSError, KeyError, ValueError) as error:
                row.update(status='failed', reason='Incomplete build or verification: ' + str(error))
            case['rows'].append(row)
    for case in output.values():
        hashes = {r['timing']['oracle_sha256'] for r in case['rows'] if r['status'] == 'passed'}
        if len(hashes) > 1:
            raise ValueError('Methods did not share the same source oracle: ' + case['name'])
    return list(output.values())


def markdown(report):
    lines = ['# Public renderer comparison: V5 candidates', '',
        'PAL VICE 3.10, default machine settings, sound disabled, seed 1. Common V9 normal PLAY ALL; '
        'three ten-second visits per case, uncapped. All authored/frozen pictures and colours remain present. '
        'These are comparisons between current implementations, not old-release regression measurements.', '',
        'The canonical twelve-entry corpus shares one cart per method. Each Dragon/SAKU case has its own cart. '
        'SAKU uses the standalone 48-frame solid and gradient logo rotations: no starfield, cards, interactive '
        'colour controls or exhibition scheduler. Every method has the same static benchmark HUD. Dragon uses '
        'all 128 published orientations. Saved byte-clear plans are rebuilt into ordinary geometry cell spans '
        'before each backend applies its own lossless encoding; complete bitmap/colour hashes must remain unchanged.', '',
        '## Average FPS leaders', '',
        '| Case | Pictures | Fastest measured method / preference | Average FPS | V2 FPS | V4 FPS | V5-c1 FPS | V5-c2 FPS |',
        '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |']
    for case in report['cases']:
        passed = [r for r in case['rows'] if r['status'] == 'passed']
        best = max(passed, key=lambda r: r['timing']['display_fps']) if passed else None
        def rate(method):
            rows = [r for r in passed if r['method'] == method and r['preference'] == 'fps']
            if rows:return f"{rows[0]['timing']['display_fps']:.3f}"
            return 'N/A / FAIL' if any(r['method']==method for r in case['rows']) else '—'
        label = best['method'] + ' / ' + best['preference'] if best else '—'
        speed = f"{best['timing']['display_fps']:.3f}" if best else '—'
        lines.append(f"| {case['name']} | {case['frames']} | {label} | {speed} | {rate('hors-render-v2')} | {rate('hors-v4-ef')} | {rate('hors-v5-c1')} | {rate('hors-v5-c2')} |")
    lines += ['', 'Highest measured average FPS is marked below; small differences may reflect interval/rotation phase. '
        'Do not average unlike workloads or mix these uncapped rates with four-refresh native scene contests. '
        'High/low values describe observed display intervals, not sustained rates. '
        'CRT bytes describe the complete cart, including other corpus entries where applicable. '
        'N/A records a confirmed capacity limit; FAIL is a build/verification error.', '']
    for case in report['cases']:
        lines += ['## ' + case['name'], '', f"{case['frames']} pictures; picture SHA-256 `{case['pictures_sha256']}`.", '',
                  '| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |',
                  '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
        best = max((r['timing']['display_fps'] for r in case['rows'] if r['status'] == 'passed'), default=None)
        for row in case['rows']:
            if row['status'] == 'passed':
                t = row['timing']; marker = '**WINNER**; ' if t['display_fps'] == best else ''
                lines.append(f"| {row['method']} | {row['preference']} | {t['high_fps']:.3f} | {t['display_fps']:.3f} | {t['low_fps']:.3f} | {t['p95_display_ms']:.3f} | {t['worst_display_ms']:.3f} | {row['crt_bytes']:,} | {marker}pixels and colours passed |")
            else:
                status = 'N/A' if row['status'] == 'capacity' else 'FAIL'
                lines.append(f"| {row['method']} | {row['preference']} | {status} | {status} | {status} | — | — | — | {row['reason'].replace('|', '/')} |")
        lines.append('')
    lines += ['## Verification', '', f"{report['passed_rows']} passed combinations; {report['capacity_rows']} capacity N/As; {report['failed_rows']} failures. "
              f"{report['verified_pictures']:,} completed-picture checks. Physical C64 and NTSC are unmeasured.", '',
              'See public-results.json for source/tool/input hashes and per-row measurements. '
              'The external benchmark workspace retains playable CRTs, raw traces, labels and oracles.', '']
    return '\n'.join(lines)


def finish(cases, provenance, out):
    rows = [r for case in cases for r in case['rows']]
    report = dict(format='c643d-public-benchmarks-v1', cases=cases, provenance=provenance,
                  passed_rows=sum(r['status']=='passed' for r in rows),
                  capacity_rows=sum(r['status']=='capacity' for r in rows),
                  failed_rows=sum(r['status']=='failed' for r in rows),
                  verified_pictures=sum(r.get('verification',{}).get('verified_frames',0) for r in rows))
    save(out / 'public-results.json', report)
    (out / 'PUBLIC_RENDERER_COMPARISON.md').write_text(markdown(report))
    from optimizer_profiler import console_table
    import os
    color = sys.stdout.isatty() and 'NO_COLOR' not in os.environ and os.environ.get('TERM') != 'dumb'
    for case in cases:
        print('\n' + case['name'] + '\n' + console_table(case['rows'], core=True, color=color))
    print(out / 'PUBLIC_RENDERER_COMPARISON.md')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', choices=['menu', *EXAMPLES], default=['menu', *EXAMPLES])
    parser.add_argument('--methods',nargs='+',choices=ALL_METHODS,default=ALL_METHODS,
                        help='optional subset; default includes all original cores and current candidates')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--vice-data', type=Path, required=True)
    parser.add_argument('--tass', default='64tass'); parser.add_argument('--cartconv', default='cartconv'); parser.add_argument('--vice', default='x64sc')
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents or out.exists():
        parser.error('--out must be a new directory outside the checkout')
    if not 1 <= args.workers <= 4:
        parser.error('--workers must be 1..4')
    for key in ('tass','cartconv','vice'):
        resolved = shutil.which(getattr(args,key))
        if not resolved: parser.error('Executable not found: ' + getattr(args,key))
        setattr(args,key,str(Path(resolved).resolve()))
    args.vice_data = args.vice_data.expanduser().resolve()
    out.mkdir(parents=True)
    start = fingerprints(ROOT)[1]
    cases = []; provenance = []; statuses = []
    for key in dict.fromkeys(args.cases):
        work = out / key
        command = [sys.executable,str(ROOT/'tools/compare_renderers.py'),'--workspace',str(work),
                   '--methods',*args.methods,'--loops','3','--workers',str(args.workers),'--vice-data',str(args.vice_data)]
        for tool in ('tass','cartconv','vice'): command += ['--'+tool,getattr(args,tool)]
        if key == 'menu':
            from c643d.cartframes import load_menu_reference, MENU_REFERENCE_SHA256
            expected = [dict(name=d.name,frames=len(d.frames),pictures_sha256=picture_hash(d.frames,d.screen),
                             source='assets/v4-menu-vector-reference.json.gz',source_sha256=MENU_REFERENCE_SHA256)
                        for d in load_menu_reference(ROOT)]
        else:
            reference = out / (key+'-reference.json.gz')
            expected = [freeze_example(key,reference)]
            command += ['--reference-json',str(reference)]
        with (out/(key+'.log')).open('w') as log:
            completed = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        statuses.append(completed.returncode)
        cases += collect(work,expected,args.methods)
        record = json.loads((work/'provenance.json').read_text()); record.pop('vice_data',None)
        provenance.append(dict(case=key,measurement=record))
    if fingerprints(ROOT)[1] != start:
        raise RuntimeError('Repository inputs changed during measurement')
    report = finish(cases,provenance,out)
    return int(any(statuses) or report['failed_rows'] != 0)

if __name__ == '__main__':
    raise SystemExit(main())
