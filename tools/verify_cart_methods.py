#!/usr/bin/env python3
"""Build and run both cartridge methods outside the checkout against GitHub releases.

Downloads v0.7.3 (legacy) and v0.7.4 (standard) release assets. A control build
uses each published cartridge identity to require byte-identical legacy CRTs. Actual release
outputs retain the current VERSION. No repository files or Git refs are changed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

from compile_release import source_files
from c643d.released_examples import is_current_v2_example

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'FlyingFathead/c64-3d-toolkit'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_release(version, dest):
    dest.mkdir(parents=True)
    api = f'https://api.github.com/repos/{REPOSITORY}/releases/tags/v{version}'
    with urllib.request.urlopen(api, timeout=60) as response:
        release = json.load(response)
    asset = next(x for x in release['assets'] if x['name'] == f'c64-3d-toolkit-v{version}.zip')
    archive = dest / asset['name']
    with urllib.request.urlopen(asset['browser_download_url'], timeout=120) as response, archive.open('wb') as output:
        shutil.copyfileobj(response, output)
    digest = sha(archive)
    if asset.get('digest'):
        assert asset['digest'] == 'sha256:' + digest, 'GitHub asset digest mismatch'
    checksum = next((x for x in release['assets'] if x['name'] == asset['name'] + '.sha256'), None)
    if checksum:
        with urllib.request.urlopen(checksum['browser_download_url'], timeout=60) as response:
            text = response.read().decode()
        assert text.split()[0] == digest, 'Published checksum mismatch'
        (dest / checksum['name']).write_text(text)
    extracted = dest / 'source'; extracted.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for info in z.infolist():
            path = (extracted / info.filename).resolve()
            if not path.is_relative_to(extracted.resolve()):
                raise ValueError('Unsafe release archive path')
        z.extractall(extracted)
    roots = list(extracted.glob('*/VERSION'))
    root = roots[0].parent if roots else extracted
    assert (root / 'VERSION').read_text().strip() == version
    index = json.loads((root / 'examples/release-index.json').read_text())
    for row in index['files']:
        assert sha(root / row['path']) == row['sha256'], row['path']
    proof = dict(version=version, release_url=release['html_url'], asset_url=asset['browser_download_url'],
                 archive_sha256=digest, github_digest=asset.get('digest'), checksum_asset=bool(checksum),
                 indexed_files_verified=len(index['files']))
    (dest / 'download.json').write_text(json.dumps(proof, indent=2) + '\n')
    return root, proof


def current_carts(root, legacy=False, inherited=False):
    version = (root / 'VERSION').read_text().strip()
    candidates = [p for p in (root / 'examples').rglob('*.crt') if
             is_current_v2_example(p, version, legacy_cart=legacy)]
    if inherited:
        candidates=[]
        for path in (root/'examples').rglob('*.crt'):
            match=re.search(r'-v(\d+\.\d+\.\d+)-',path.name)
            identity=match.group(1) if match else version
            if tuple(map(int,identity.split('.'))) > tuple(map(int,version.split('.'))):continue
            if is_current_v2_example(path,identity,legacy_cart=legacy):candidates.append(path)
    groups={}
    for path in sorted(candidates):
        key=canonical_name(path,version)
        match=re.search(r'-v(\d+\.\d+\.\d+)-',path.name)
        identity=tuple(map(int,match.group(1).split('.'))) if match else (0,0,0)
        if key not in groups or identity>groups[key][0]:groups[key]=(identity,path)
    carts=[row[1] for row in groups.values()]
    combo = root / 'examples/color_combo_test' / ('color-combo-test-legacy.crt' if legacy else 'color-combo-test.crt')
    carts.append(combo)
    assert len(carts) == 20 and all(p.is_file() for p in carts), (root, len(carts))
    return sorted(carts)


def canonical_name(path, version):
    return re.sub(r'-v\d+\.\d+\.\d+-','-vVERSION-',path.name.replace('-legacy.crt', '.crt'))


def compare_files(left, right, left_legacy=False, right_legacy=False, left_inherited=False, right_inherited=False):
    lv = (left / 'VERSION').read_text().strip(); rv = (right / 'VERSION').read_text().strip()
    a = {canonical_name(p, lv): p for p in current_carts(left, left_legacy, left_inherited)}
    b = {canonical_name(p, rv): p for p in current_carts(right, right_legacy, right_inherited)}
    assert a.keys() == b.keys()
    rows = []
    for name in sorted(a):
        x, y = a[name].read_bytes(), b[name].read_bytes()
        rows.append(dict(cart=name, before_sha256=sha(a[name]), after_sha256=sha(b[name]),
                         before_file=a[name].relative_to(left).as_posix(),after_file=b[name].relative_to(right).as_posix(),
                         identical=x == y, before_bytes=len(x), after_bytes=len(y),
                         differing_bytes=sum(u != v for u, v in zip(x, y)) + abs(len(x)-len(y))))
    return rows


def reproduce_inherited_identities(control, baseline, toolchain, run):
    """Rebuild carried-over artifacts with identities recorded in the release.

    The 0.7.3 release retained the 0.7.2 Marbles and HiFi carts. Change only the
    isolated control's VERSION while rebuilding them. Never patch CRT bytes.
    """
    from c643d.cartpaths import menu_manifest_path
    version=(control/'VERSION').read_text().strip();overrides=[]
    for cart in current_carts(baseline,inherited=True):
        metadata=menu_manifest_path(cart)
        if not metadata.exists():metadata=cart.with_name(cart.stem+'-manifest.json')
        meta=json.loads(metadata.read_text())
        identity=meta.get('build_screen',{}).get('version',version)
        if identity==version:continue
        if not re.fullmatch(r'\d+\.\d+\.\d+',identity):raise ValueError('Invalid baseline identity')
        previous=[p for p in current_carts(control,True,inherited=True) if canonical_name(p,version)==canonical_name(cart,version)]
        (control/'VERSION').write_text(identity+'\n')
        try:
            if cart.parent.name=='cart_hifi':
                run('control-inherited-hifi',control,['tools/build_hifi_cart.py',*toolchain,'--legacy-cart'])
                produced=control/cart.relative_to(baseline).with_stem(cart.stem+'-legacy')
                assert produced.is_file()
                for old in previous:
                    if old!=produced:old.unlink()
            elif meta['format']=='c643d-easyflash-stream-scene':
                run('control-inherited-'+cart.parent.name,control,['tools/build_hors_v2_examples.py',
                    '--only',cart.parent.name,*toolchain,'--legacy-cart'])
            else:raise ValueError('Unsupported inherited identity: '+cart.name)
        finally:(control/'VERSION').write_text(version+'\n')
        overrides.append(dict(cartridge=cart.relative_to(baseline).as_posix(),recorded_identity=identity,
                              action='Reassembled with recorded VERSION; no binary patching'))
    return overrides


def compare_runtime_payloads(legacy_root, standard_root):
    """Permit only the boot ROM and the documented four-page scene relocation."""
    import struct
    def image(path):
        data=path.read_bytes(); result=bytearray(b'\xff'*0x100000)
        pos=int.from_bytes(data[16:20],'big')
        while pos<len(data):
            _,size,_,bank,address,length=struct.unpack_from('>4sIHHHH',data,pos)
            offset=bank*16384+(8192 if address==0xA000 else 0)
            result[offset:offset+length]=data[pos+16:pos+size];pos+=size
        return result
    version=(standard_root/'VERSION').read_text().strip()
    standard={canonical_name(p,version):p for p in current_carts(standard_root)}
    results=[]
    for p in current_carts(legacy_root,True):
        name=canonical_name(p,version);a=image(p);b=image(standard[name])
        meta=p.with_name(p.stem+'-manifest.json')
        scene=meta.exists() and 'scene' in json.loads(meta.read_text())['format']
        # Boot instructions, vectors and metadata differ inside bank 0 ROMH.
        if scene:
            assert a[0x3800:0x3C00]==b[0x9800:0x9C00],name+' scene restoration'
            assert a[0x2400:0x3800]==b[0x2400:0x3800],name+' scene prefix'
            assert a[0x3C00:0x3FFA]==b[0x3C00:0x3FFA],name+' scene suffix'
            a[0x9800:0x9C00]=b[0x9800:0x9C00]
        a[0x2000:0x4000]=b[0x2000:0x4000]
        assert a==b,name+' runtime or frame payload changed outside boot/relocation'
        results.append(dict(cart=name,runtime_and_frame_bytes_identical=True,scene_relocation_verified=scene))
    return results


def copy_source(dest, version=None):
    dest.mkdir(parents=True)
    for src in source_files(ROOT):
        dst = dest / src.relative_to(ROOT); dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    assert not (dest / '.git').exists(), 'External build must not inherit Git metadata'
    if version:
        (dest / 'VERSION').write_text(version + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--tass', default='64tass'); p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc'); p.add_argument('--vice-data', required=True)
    p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--build-only', action='store_true', help='stop after all builds and checksum comparisons')
    a = p.parse_args(); work = a.workspace.expanduser().resolve()
    if work == ROOT or ROOT in work.parents or work in ROOT.parents or work.exists():
        p.error('Use a new workspace outside the checkout')
    if a.jobs < 1:p.error('--jobs must be positive')
    work.mkdir(parents=True); logs = work / 'logs'; logs.mkdir()
    version = (ROOT / 'VERSION').read_text().strip()
    env = os.environ.copy()
    env['C64_VICE_REAL'] = str(Path(shutil.which(a.vice) or a.vice).resolve())
    env['C64_VICE_LOG_DIR'] = str(work / 'vice-logs')

    def run(label, root, args):
        print(label, flush=True)
        with (logs / (label + '.log')).open('w') as log:
            subprocess.run([sys.executable, *args], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)

    baselines = {}
    proofs = []
    for v in ('0.7.3', '0.7.4'):
        print('Downloading published release', v, flush=True)
        baselines[v], proof = download_release(v, work / ('github-' + v)); proofs.append(proof)
    variants = [('standard', False, version), ('legacy', True, version), ('legacy-073-control', True, '0.7.3')]
    for label, legacy, identity in variants:
        root = work / label; copy_source(root, identity)
        flags = ['--legacy-cart'] if legacy else []
        toolchain = ['--tass', a.tass, '--cartconv', a.cartconv]
        run(label + '-examples', root, ['tools/build_hors_v2_examples.py', *toolchain, *flags])
        run(label + '-showcase', root, ['tools/build_demo_cart_v2.py', *toolchain, *flags])
        run(label + '-combo', root, ['c643d.py', 'color-combo-test', '--overwrite-policy', 'allow', *toolchain, *flags])
        run(label + '-smoke', root, ['c643d.py', 'cartridge-smoke', '--overwrite-policy', 'allow', *toolchain, *flags])
        current_carts(root, legacy)
    overrides=reproduce_inherited_identities(work/'legacy-073-control',baselines['0.7.3'],toolchain,run)
    exact = compare_files(baselines['0.7.3'], work / 'legacy-073-control', right_legacy=True,left_inherited=True,right_inherited=True)
    report = dict(version=version, downloads=proofs, legacy_073_exact=exact,
                  control_identity_overrides=overrides,
                  all_legacy_073_identical=all(x['identical'] for x in exact),
                  standard_vs_074=compare_files(baselines['0.7.4'], work / 'standard'),
                  legacy_vs_standard=compare_files(work / 'legacy', work / 'standard', left_legacy=True))
    report['runtime_payloads']=compare_runtime_payloads(work/'legacy',work/'standard')
    (work / 'checksums.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['all_legacy_073_identical'], 'Legacy does not reproduce every published v0.7.3 CRT; inspect checksums.json'
    if not a.build_only:
        for label, legacy, _ in variants[:2]:
            root = work / label; wrapper = str(root / 'VICE-BATCH.sh')
            run(label + '-playback', root, ['tools/verify_hors_v2_release.py', '--out', str(work / (label + '-playback')),
                '--vice', wrapper, '--vice-data', a.vice_data, '--jobs', str(a.jobs), *(['--legacy-cart'] if legacy else [])])
            combo = root / 'examples/color_combo_test' / ('color-combo-test-legacy.crt' if legacy else 'color-combo-test.crt')
            run(label + '-combo-playback', root, ['tools/verify_color_combos.py', str(combo), '--vice', wrapper,
                '--vice-data', a.vice_data, '--report', str(work / (label + '-combo.json'))])
        run_cold_and_fps(work, variants[:2], a, run)
        report['fps_comparison']=compare_fps(work)
    report['passed'] = True
    report['playback_tested'] = not a.build_only
    (work / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Cartridge method comparison PASS:', work, flush=True)


def compare_fps(work):
    rows=[]
    baseline_root=work/'github-0.7.4/source'
    baseline_root=next(baseline_root.glob('*/VERSION')).parent
    old_names={'all':'release-demo1-fps-play-all.json','all-ram':'release-demo1-ram-play-all.json',
               'demo2':'release-demo2-play-all.json'}
    for case in ('all','all-ram','demo2'):
        reports={method:json.loads((work/f'{method}-fps-{case}.json').read_text()) for method in ('legacy','standard')}
        old=json.loads((baseline_root/'docs/benchmarks/loading-0.7.4'/old_names[case]).read_text())
        old_cart=next(p for p in current_carts(baseline_root) if p.name==Path(old['cartridge']).name)
        assert sha(old_cart)==old['sha256'],'Baseline benchmark is not for the published CRT'
        for method,current in reports.items():
            cart=next(p for p in current_carts(work/method,method=='legacy') if p.name==Path(current['cartridge']).name)
            assert sha(cart)==current['sha256']
            for reference_name,reference in [('v0.7.4',old),('standard',reports['standard'])]:
                assert len(reference['samples'])==len(current['samples'])
                counts=all(a['display_flips']==b['display_flips'] for a,b in zip(reference['samples'],current['samples']))
                changes=[100*(b['display_fps']/a['display_fps']-1) for a,b in zip(reference['entries'],current['entries'])]
                rows.append(dict(case=case,method=method,reference=reference_name,windows=len(current['samples']),
                    identical_display_counts=counts,identical_timing_samples=reference['samples']==current['samples'],
                    max_absolute_fps_change_percent=max(map(abs,changes))))
                assert counts,(case,method,reference_name,'display counts changed')
    return rows


def run_cold_and_fps(work, variants, args, run):
    """Execute each CRT at Warp off/on and benchmark production PLAY ALL."""
    from PIL import Image
    from c643d.cartlaunch import command
    from c643d.cartridge import inspect_easyflash_crt
    rows = []
    for label, legacy, _ in variants:
        root = work / label; out = work / (label + '-cold'); out.mkdir()
        carts = current_carts(root, legacy)
        carts.append(root / 'build' / ('easyflash-smoke-legacy.crt' if legacy else 'easyflash-smoke.crt'))
        def check(crt):
            original = sha(crt); inspect_easyflash_crt(crt, require_metadata=not legacy)
            pictures = []
            for warp in (False, True):
                screen = out / (crt.stem + ('-warp' if warp else '-normal') + '.png')
                argv = command(args.vice, crt, ['-console', '-directory', args.vice_data, '+sound',
                    '-warp' if warp else '+warp', '-seed', '1', '-jamaction', '5', '-limitcycles', '2000000',
                    '-exitscreenshot', str(screen)], clean_settings=True)
                result = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
                screen.with_suffix('.log').write_text(result.stdout)
                assert result.returncode in (0, 1) and 'cycle limit reached' in result.stdout.lower(), result.stdout[-1000:]
                assert 'JAM at' not in result.stdout and 'CPU JAM' not in result.stdout
                assert ('EF: EAPI not found' if legacy else 'EF: EAPI found') in result.stdout
                assert 'as ID 32' in result.stdout and sha(crt) == original
                with Image.open(screen) as im:pictures.append((im.size, im.convert('RGB').tobytes()))
            assert pictures[0] == pictures[1]
            return dict(method=label, cart=crt.name, sha256=original, warp_on_off=True, unchanged=True)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:rows.extend(pool.map(check, carts))
        version = (root / 'VERSION').read_text().strip()
        for suffix in ('all', 'all-ram'):
            cart = root / 'examples/cart_demos' / (f'c643d-demo-v{version}-hors-render-v2-{suffix}' + ('-legacy' if legacy else '') + '.crt')
            run(label + '-fps-' + suffix, root, ['tools/benchmark_play_all.py', str(cart), '--vice', str(root / 'VICE-BATCH.sh'),
                '--vice-data', args.vice_data, '--report', str(work / (label + '-fps-' + suffix + '.json'))])
        cart = root / 'examples/cart_demos_v2' / ('demo-cart-2-preview-hors-v2' + ('-legacy' if legacy else '') + '.crt')
        run(label + '-fps-demo2', root, ['tools/benchmark_play_all.py', str(cart), '--vice', str(root / 'VICE-BATCH.sh'),
            '--vice-data', args.vice_data, '--report', str(work / (label + '-fps-demo2.json'))])
    (work / 'cold-boots.json').write_text(json.dumps(dict(passed=True, cases=len(rows)*2, carts=rows), indent=2) + '\n')


if __name__ == '__main__':
    main()
