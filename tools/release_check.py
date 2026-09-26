#!/usr/bin/env python3
"""Validate the v0.8.2 source and recorded evidence; optionally run native smoke tests."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = 'docs/benchmarks/release-0.8.2'
# Release orchestration does not participate in measured renderer execution.
RELEASE_ONLY = {'tools/compile_release.py', 'tools/release_check.py', 'tools/release_smoke.py', 'tools/verify_cart_build_screen.py'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(root=ROOT):
    root = Path(root)
    if (root/'VERSION').read_text().strip() != '0.8.2':
        raise ValueError('This gate validates version 0.8.2')
    protected = json.loads((root/EVIDENCE/'preserved-files.json').read_text())
    for name, digest in protected['files'].items():
        if sha(root/name) != digest:
            raise ValueError('Preserved file changed: ' + name)
    public = json.loads((root/EVIDENCE/'public-family.json').read_text())
    rows = [r for case in public['cases'] for r in case['rows']]
    if len(public['cases']) != 16 or len(rows) != 192:
        raise ValueError('Incomplete HORS-V1 through V5 family matrix')
    expected = {'yunroll-cart-v10', 'hors-render-v2', 'hors-renderer-v3', 'hors-v4-ef', 'hors-v5-c1', 'hors-v5-c2'}
    for case in public['cases']:
        if {(r['method'],r['preference']) for r in case['rows']} != {(m,p) for m in expected for p in ('fps','ram')}:
            raise ValueError('Missing or duplicate family combination: ' + case['name'])
        for row in case['rows']:
            if row['status'] == 'capacity':
                if (case['name'],row['method'],row.get('reason')) != ('DRAGON WIREFRAME','yunroll-cart-v10',
                        'frame block 10492 exceeds 8192-byte staging buffer'):
                    raise ValueError('Unreviewed capacity failure: '+case['name'])
                continue
            proof = row.get('verification', {})
            if (row['status'] != 'passed' or not proof.get('pixel_match') or not proof.get('color_match')
                    or proof.get('orientations') != case['frames']):
                raise ValueError('Incomplete family picture verification: ' + case['name'])
    from compare_renderers import fingerprints
    current, current_sha = fingerprints(root)
    recorded = public['provenance'][0]['measurement']
    if any(p['measurement']['input_sha256'] != recorded['input_sha256'] for p in public['provenance']):
        raise ValueError('Family measurements do not share one source snapshot')
    differences = sorted(k for k in set(current) | set(recorded['inputs'])
                         if current.get(k) != recorded['inputs'].get(k))
    if set(differences) - RELEASE_ONLY:
        raise ValueError('Measured source changed: ' + ', '.join(set(differences)-RELEASE_ONLY))
    from c643d.renderer_names import DEFAULT_RENDERER, canonical_selector
    from c643d.cartridge_defaults import resolve
    from c643d.cli import make_parser
    from c643d.toolchain import load_toolchain_settings
    settings = load_toolchain_settings(None)
    args = make_parser(settings).parse_args(['build', '--no-config', '--shape', 'cube'])
    if DEFAULT_RENDERER != 'hors-v4' or resolve(args,settings) != 'easyflash':
        raise ValueError('Default renderer/cartridge changed')
    if canonical_selector('hors-v5') != canonical_selector('hors-v5-c1'):
        raise ValueError('Old V5 selector no longer preserves c1')
    if canonical_selector('hors-v5-c2') == canonical_selector('hors-v5-c1'):
        raise ValueError('C2 must remain an independent candidate')
    return dict(passed=True,version='0.8.2',preserved_files=len(protected['files']),
        preserved_cartridges=sum(n.endswith('.crt') for n in protected['files']),
        public_combinations=len(rows),public_passes=sum(r['status']=='passed' for r in rows),public_capacity=sum(r['status']=='capacity' for r in rows),
        public_picture_checks=sum(r['verification']['verified_frames'] for r in rows if r['status']=='passed'),
        measured_source_sha256=recorded['input_sha256'],current_source_sha256=current_sha,
        release_orchestration_differences=differences,
        note='Saved matrix evidence checked against the current renderer source; this does not rerun that full matrix.')


def native(out, args):
    from compile_release import source_files
    stage = out/'native-source'; stage.mkdir()
    for path in source_files(ROOT):
        name = path.relative_to(ROOT)
        if name.parts[0] not in ('tools','c64','assets','config') and str(name) not in (
                'VERSION','c643d.py','requirements.txt','requirements-core.txt','requirements-svg.txt',
                'examples/camera_crossing/camera-crossing.c643dscene'):
            continue
        target = stage/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,target)
    command = [sys.executable,str(stage/'tools/release_smoke.py'),'--out',str(out/'native')]
    for tool in ('tass','cartconv','vice','vice_data'):
        command += ['--'+tool.replace('_','-'),str(getattr(args,tool))]
    with (out/'native.log').open('w') as log:
        subprocess.run(command,cwd=stage,stdout=log,stderr=subprocess.STDOUT,check=True)
    return json.loads((out/'native/results.json').read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--native',action='store_true',help='also rebuild and verify public smoke cases in PAL VICE')
    parser.add_argument('--tass',default='64tass');parser.add_argument('--cartconv',default='cartconv')
    parser.add_argument('--vice',default='x64sc');parser.add_argument('--vice-data')
    args = parser.parse_args(argv);out=args.out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents or out.exists():
        parser.error('--out must be a new directory outside the checkout')
    if args.native and not args.vice_data:parser.error('--native requires --vice-data')
    out.mkdir(parents=True)
    try:
        result = audit()
        with (out/'unit-tests.log').open('w') as log:
            subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        result['unit_suite_passed']=True
        if args.native:result['native']=native(out,args)
        # Tests and diagnostics must not alter the source they checked.
        if audit()['current_source_sha256'] != result['current_source_sha256']:
            raise ValueError('Source changed during validation')
        (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        (out/'failure.txt').write_text(str(error)+'\n')
        print('Release check failed: '+str(error),file=sys.stderr);return 1

if __name__ == '__main__':raise SystemExit(main())
