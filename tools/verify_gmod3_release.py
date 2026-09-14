#!/usr/bin/env python3
"""Audit shipped GMod3 images against their measured release evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from c643d.gmod3_image import inspect_crt
from report_gmod3_performance import check_winners

ROOT=Path(__file__).resolve().parents[1]

def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(baseline=None):
    assert (ROOT/'VERSION').read_text().strip()=='0.8.1'
    page=(ROOT/'README.md').read_text()
    assert '## v0.8.0: GMod3 cartridge support added, switch to HORS-V4' in page
    assert page.index('## v0.8.1:')<page.index('## v0.8.0:')<page.index('## v0.7.9:')<page.index('## v0.7.8:')<page.index('## Previous release: v0.7.7')
    assert 'Includes all demos from the previous examples through v0.7.9.' in page
    assert '### Blender framing and input flips' not in page
    assert 'Final v0.7.9 refinements:' not in page
    first=page.split('### Grab a cartridge and hit SPACE',1)[1].splitlines()[4]
    assert 'Demo Cart v3.1: GMod3 All-in-One' in first and '58' in first
    for media in ('examples/stanford_dragon/previews/stanford_dragon-golden-hors-v3.gif',
        'examples/saku_2026/previews/saku_2026-light-starfield.gif',
        'examples/stanford_dragon/stanford_dragon-showcase.gif',
        'examples/hors_v3_preview/previews/sande_pretzel-surface-metallic-128-v3-vice.gif',
        'assets/c64-3d-toolkit-examples-showreel-v0.7.7-teaser.gif',
        'assets/c64-3d-toolkit-examples-showreel-v0.7.7.mp4'):
        assert media in page and (ROOT/media).is_file(),media
    folder=ROOT/'examples/gmod3_cart_demos';images=[]
    for name,count in [('demo-cart-v3.1-gmod3-all-in-one',58),('demo-cart-v3.0-gmod3-all-in-one-benchmark',65)]:
        info=inspect_crt(folder/(name+'.crt'));meta=json.loads((folder/(name+'-manifest.json')).read_text())
        assert info==meta['container']
        assert len(meta['entries'])==count and sum(e['frames'] for e in meta['entries'])==6474
        assert meta['used_kib']+meta['free_kib']==16384
        for e in meta['entries']:
            assert sha(folder/e['labels'])==e['runtime']['build_evidence']['symbols_sha256']
            assert e['runtime']['renderer']=='hors-renderer-v4'
        images.append(dict(file=name+'.crt',image=info,entries=count,used_kib=meta['used_kib'],free_kib=meta['free_kib']))
    measured=read('docs/benchmarks/release-0.8.1/collection/results.json')
    assert len(measured['entries'])==58 and measured['crt_sha256']==images[0]['image']['crt_sha256']
    assert all(e['passed'] and e['all_three_buffers'] and e['crt_sha256']==measured['crt_sha256'] for e in measured['entries'])
    sequence=read('docs/benchmarks/gmod3-sequence.json')
    assert sequence['passed'] and sequence['crt_sha256']==images[1]['image']['crt_sha256']
    assert [e['index'] for e in sequence['entries']]==list(range(65))+[0]
    assert all(e['last_picture_displayed'] for e in sequence['entries'])
    features=read('docs/benchmarks/release-0.8.1/features/results.json')
    assert features['controls']['passed'] and features['crt_sha256']==measured['crt_sha256']
    assert features['controls']['RUN_STOP_menu'] and features['controls']['RUN_STOP_from_help_menu']
    paging=read('docs/benchmarks/release-0.8.1/paging/results.json')
    assert paging['passed'] and paging['collection_sha256']==measured['crt_sha256']
    keyboard=read('docs/benchmarks/release-0.8.1/keyboard/results.json')
    assert keyboard['passed'] and keyboard['crt_sha256']==measured['crt_sha256']
    assert keyboard['startup_help'] and keyboard['hud_all_three_buffers'] and keyboard['held_key_exit']
    assert len(keyboard['results'])==2 and all(r['passed'] and len(r['entries'])==58 for r in keyboard['results'])
    benchmark=read('docs/benchmarks/release-0.8.1/benchmark-menu/results.json')
    assert benchmark['passed'] and benchmark['benchmark_unchanged']
    assert benchmark['crt_sha256']==images[1]['image']['crt_sha256']=='952704768c86994cbec5a4eaa83430876b60ba4d8055a82ca5f8fd744031af84'
    ab=read('docs/benchmarks/release-0.8.1/ab-summary.json')
    assert ab['patched_sha256']==measured['crt_sha256']
    assert ab['baseline_sha256']==sha(folder/'demo-cart-v3.0-gmod3-all-in-one.crt')
    assert ab['entries']==58 and abs(ab['largest_drop_percent'])<0.4
    short=read('docs/benchmarks/gmod3-cli/short-labels/builds.json')
    for item in short:
        stem=Path(item['command'].split(' --output ')[1].split()[0]).name
        pixels=read('docs/benchmarks/gmod3-cli/short-labels/'+stem+'-pixels.json')
        assert pixels['pixel_match'] and pixels['color_match']
        if item['startup_layout']:
            ui=read('docs/benchmarks/gmod3-cli/short-labels/'+stem+'.json')
            assert ui['passed'] and ui['sha256']==item['crt_sha256']
    matched=read('docs/benchmarks/hors-v4-matched/results.json')['entries']
    assert len(matched)==69 and {e['case'] for e in matched}==set(range(69))
    assert all(e['encoded_payloads_identical'] and e['gmod3']['passed'] and e['easyflash']['passed'] for e in matched)
    assert all(e['gmod3']['toolkit_version']==e['easyflash']['toolkit_version']=='0.8.0' for e in matched)
    differences=[e['difference_fps'] for e in matched]
    assert all(x>=0 for x in differences)
    assert all(e['gmod3']['mean_render_cycles']<=e['easyflash']['mean_render_cycles'] for e in matched)
    report=dict(passed=True,version='0.8.1',images=images,interactive_entries=58,automatic_entries=65,
        matched_workloads=69,higher_averages=sum(x>0 for x in differences),ties=sum(x==0 for x in differences),
        lower_averages=0,maximum_gain_fps=max(differences),
        tables=check_winners((ROOT/'docs/PERFORMANCE_COMPARISON.md').read_text()+'\n'+(ROOT/'docs/INTERACTIVE_BASELINE_PERFORMANCE.md').read_text()),
        interactive_ab=ab,keyboard_checks=sum(r['checks'] for r in keyboard['results']),
        benchmark_unchanged=True,
        physical_hardware_tested=False,ntsc_tested=False)
    if baseline:
        changed=[];protected=0;unchanged=0
        with zipfile.ZipFile(baseline) as archive:
            for item in archive.infolist():
                if item.is_dir():continue
                name=item.filename.split('/',1)[1];path=ROOT/name
                assert path.is_file(),('missing original file',name)
                same=sha(path)==hashlib.sha256(archive.read(item)).hexdigest()
                if same:unchanged+=1
                else:changed.append(name)
                is_protected=name.startswith('c64/') or name.endswith('.crt') or (
                    name.startswith('tools/c643d/') and name not in ('tools/c643d/cli.py','tools/c643d/renderer_names.py'))
                if is_protected:
                    protected+=1;assert same,('modified preserved backend or cartridge',name)
        report['original_archive_audit']=dict(archive_sha256=sha(Path(baseline)),unchanged_files=unchanged,
            changed_files=changed,protected_files=protected,protected_files_identical=True,missing_files=0)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-zip',type=Path)
    p.add_argument('--output',type=Path);a=p.parse_args()
    subprocess.run([sys.executable,str(ROOT/'tools/report_gmod3_performance.py'),'--check'],check=True)
    result=audit(a.baseline_zip)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
