#!/usr/bin/env python3
"""Run the historical normal-PLAY-ALL renderer matrix on each registered Sande model."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

from build_sande_examples import ROOT, SOURCES, MODELS, SET_ID, build, sha
from c643d.cartuniform import Demo
from c643d.font import bitmap_text
from c643d.pipeline import FrameBuild
from compare_renderers import METHODS, SANDE_METHODS_REPORT, SANDE_COLOR_METHODS_REPORT


def comparison_section(root, source_colors=False):
    root = Path(root)
    report = json.loads((root / (SANDE_COLOR_METHODS_REPORT if source_colors else SANDE_METHODS_REPORT)).read_text())
    if bool(report.get('source_colors')) != source_colors:
        raise ValueError('Historical Sande report colour mode differs')
    if report['version'] != (root / 'VERSION').read_text().strip():
        raise ValueError('Historical Sande method report has a stale version')
    for filename, digest in report['source_sha256'].items():
        if sha(root / 'examples/demos_sande' / filename) != digest:
            raise ValueError('Historical Sande method sources changed: ' + filename)
    if set(report['models']) != set(MODELS):
        raise ValueError('Historical Sande method report does not cover the registry')
    lines = ['', '### Sande material colours across renderer methods' if source_colors else '### Sande bw models across renderer methods', '',
             'This matrix uses the same isolated **normal PLAY ALL** harness as the original renderer comparison: '
             'three ten-second visits per model, all 192 orientations, no controls and no FPS cap. '
             'Each model gets its own comparison cart so another model cannot consume its cartridge budget. '
             'V2 uses the canonical comparison encoder settings (gap 3, batch budget 2048); the standalone carts above use gap 6. '
             'Menu/controller cost and encoding settings mean these rates should be compared within this matrix.', '',
             '`hors-render-v1` is the public name for `yunroll-cart-v10`. '
             'N/A is a recorded capacity failure with the original data, never a simplified substitute.', '']
    expected = {(m, p) for m, p in METHODS}
    for model in MODELS:
        case = report['models'][model]
        if {(r['method'], r['preference']) for r in case['results']} != expected:
            raise ValueError('Incomplete historical Sande renderer matrix: ' + model)
        lines += [f"#### {case['title']}", '',
                  '| Method | Preference | High FPS | Average FPS | Low FPS | Frame-table RAM (B) | Frame data ROM (B) |',
                  '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
        failed = []
        oracle_hashes = set()
        for row in case['results']:
            name = 'hors-render-v1 (v10)' if row['method'] == 'yunroll-cart-v10' else row['method']
            if row['status'] == 'unsupported':
                lines.append(f"| {name} | {row['preference']} | N/A | N/A | N/A | N/A | N/A |")
                failed.append(f"- `{name}` ({row['preference']}): {row['reason']}")
                continue
            r, z, proof = row['timing'], row['size'], row['verification']
            if not proof['pixel_match'] or not proof['color_match'] or proof['orientations'] != 192:
                raise ValueError('Historical Sande pixel verification failed')
            if r['frame_count'] != 192 or row['protocol']['loops'] != 3 or row['protocol']['seconds_setting'] != 10:
                raise ValueError('Historical Sande protocols differ')
            oracle_hashes.add(r['oracle_sha256'])
            lines.append(f"| {name} | {row['preference']} | {r['high_fps']:.2f} | {r['display_fps']:.2f} | "
                         f"{r['low_fps']:.2f} | {z['resident_frame_data_bytes']:,} | {z['rom_frame_bytes']:,} |")
        if len(oracle_hashes) != 1:
            raise ValueError('Historical Sande methods do not share one source oracle')
        if failed:
            lines += ['', 'Recorded capacity limits:', '', *failed]
        lines.append('')
    report_name = 'methods-color.json' if source_colors else 'methods.json'
    flag = ' --source-colors' if source_colors else ''
    lines += [f'[Raw historical Sande method results](benchmarks/sande/{report_name})', '',
              '```bash', f'python tools/run_sande_methods.py{flag} --workspace ../c64-sande-methods --vice-data /usr/local/share/vice', '```', '']
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, default=Path('/usr/local/share/vice'))
    p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--skip-build', action='store_true', help='Use matching freshly built Sande oracles; intended for RUN-CHECKS.sh')
    p.add_argument('--source-colors', action='store_true', help='Use the original MTL colours instead of the bw defaults')
    a = p.parse_args()
    work = a.workspace.expanduser().resolve()
    if work.exists() or work == ROOT or ROOT in work.parents:
        p.error('--workspace must be a new directory outside the checkout')
    if not 1 <= a.jobs <= 4:
        p.error('--jobs must be 1..4')
    work.mkdir(parents=True)
    if not a.skip_build:
        build(tass=a.tass, cartconv=a.cartconv, source_colors=a.source_colors)
    recipe = json.loads((SOURCES / 'recipe.json').read_text())
    report = dict(set_id=SET_ID, version=(ROOT / 'VERSION').read_text().strip(), author='Sande',
                  source_sha256={p.name: sha(p) for p in sorted(SOURCES.iterdir()) if p.suffix in ('.obj', '.mtl') or p.name == 'recipe.json'},
                  models={})
    if a.source_colors:
        report['source_colors'] = True
    for model in MODELS:
        suffix = '-color' if a.source_colors else ''
        meta = json.loads((SOURCES / (model + '-hors-render-v2' + suffix + '-manifest.json')).read_text())
        if meta['source_recipe']['sha256'] != sha(SOURCES / 'recipe.json'):
            raise ValueError('Sande recipe changed; rebuild before using --skip-build')
        for filename, digest in meta['source_recipe']['files'].items():
            if sha(SOURCES / filename) != digest:
                raise ValueError('Sande source changed; rebuild before using --skip-build')
        oracle = ROOT / meta['runtime_work'] / 'oracle.json'
        frames = [FrameBuild(**row) for row in json.loads(oracle.read_text())]
        name = model.upper().replace('_', ' ')
        hud = bitmap_text(f"{name} V:{meta['vertices']:03d} E:{meta['edges']:03d}", 31)
        demo = Demo(name, frames, meta['colors'], meta['screen_color'], hud,
                    'examples/demos_sande/' + model + '.obj', sha(SOURCES / (model + '.obj')))
        row = asdict(demo)
        row['hud'] = demo.hud.hex()
        reference = work / (model + '-reference.json')
        reference.write_text(json.dumps(dict(format='c643d-vector-reference-v1', demos=[row])) + '\n')
        output = work / model
        command = [sys.executable, str(ROOT / 'tools/compare_renderers.py'), '--workspace', str(output),
                   '--reference-json', str(reference), '--methods', *dict.fromkeys(m for m, _ in METHODS),
                   '--workers', str(a.jobs), '--loops', '3', '--tass', a.tass, '--cartconv', a.cartconv,
                   '--vice', a.vice, '--vice-data', str(a.vice_data)]
        with (work / (model + '.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        rows = []
        for method, preference in METHODS:
            key = method + ('-ram' if preference == 'ram' else '')
            timing = json.loads((output / 'results' / (key + '-play-all.json')).read_text())
            item = dict(method=method, preference=preference)
            if timing.get('unsupported'):
                reasons = json.loads((output / 'results' / (key + '-unsupported.json')).read_text())
                item.update(status='unsupported', reason='; '.join(r['reason'] for r in reasons))
            else:
                item.update(status='passed', timing=timing['entries'][0],
                            protocol={k: timing[k] for k in ('loops', 'seconds_setting', 'mode', 'exhibition', 'pal_clock_hz', 'seed', 'vice_defaults')},
                            size=json.loads((output / 'results' / (key + '-sizes.json')).read_text())['entries'][0],
                            verification=json.loads((output / 'results' / (key + '-pixels-00.json')).read_text()))
            rows.append(item)
        report['models'][model] = dict(title=recipe['models'][model]['title'], reference_sha256=sha(reference), results=rows)
        print(model, 'historical renderer matrix PASS', flush=True)
    (work / ('methods-color.json' if a.source_colors else 'methods.json')).write_text(json.dumps(report, indent=2) + '\n')
    print('Sande historical methods complete:', work, flush=True)


if __name__ == '__main__':
    main()
