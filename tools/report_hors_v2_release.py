#!/usr/bin/env python3
"""Save measured release evidence and stable v2 documentation after the gates."""
import argparse
import json
from pathlib import Path
import shutil
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace',type=Path)
    a=p.parse_args();work=a.workspace.resolve();checks=work/'checks'
    proof=json.loads((work/'example-checks/summary.json').read_text())
    if not proof.get('passed'):raise ValueError('Example validation has not passed')
    target=ROOT/'docs/benchmarks/hors-v2';target.mkdir(parents=True,exist_ok=True)
    shutil.copytree(work/'version-checks',target/'version-checks',dirs_exist_ok=True)
    for name in ('unit.log','boundaries.log','menu-ui.json','provenance.log','vice-version.txt'):
        shutil.copy2(checks/name,target/name)
    shutil.copytree(work/'example-checks',target/'examples',dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('*.bin','*.png','*.bmp','*.crt'))
    for folder in ('v1','v2'):
        shutil.copytree(checks/'showcase'/folder,target/'showcase'/folder,dirs_exist_ok=True)
    for name in ('COMPARISON.md','SHA256SUMS.txt'):
        shutil.copy2(checks/'showcase'/name,target/name)
    canonical=target/'canonical';canonical.mkdir(exist_ok=True)
    for name in ('provenance.json','PERFORMANCE_COMPARISON.md'):
        shutil.copy2(checks/'canonical'/name,canonical/name)
    shutil.copytree(checks/'canonical/results',canonical/'results',dirs_exist_ok=True)
    shutil.copy2(ROOT/'build/demo-cart-2-preview-hors-v2-scroll-check/default-start.png',
                 ROOT/'examples/cart_demos_v2/menu-preview.png')
    comparison=(checks/'showcase/COMPARISON.md').read_text().split('\n',2)[2]
    text='# hors-render-v2 release results\n\n'
    text+='Stable v2, PAL VICE, normal PLAY ALL: three ten-second visits per entry. '
    text+='Changes rank displayed-frame counts; all methods use matching complete pictures and colours. '
    text+='Peak interval FPS is not sustained throughput. F5 is excluded.\n\n'
    text+=comparison+'\n'
    text+='The alternate-VERSION gate also passed: temporary v1/v2 carts showed the manifest version on their startup screens, all menu styles and thanks screens. Root VERSION supplies Python and Windows setup identity.\n\n'
    text+='The [main performance page](PERFORMANCE_COMPARISON.md) compares released renderer generations, '
    text+='including stable v2 FPS/RAM rows, and displays Demo Cart 2.0 in its own section. CUBE can still favour the resident yunroll renderer.\n\n'
    text+=f"Release examples: **{proof['cartridges']} cartridges**, **{proof['checks']} picture checks**, "
    text+=f"**{proof['verified_pictures']:,} completed pictures**. Native Marbles ending, menu states and HiFi reel transitions also passed. "
    text+='The ending verifier acknowledges the SPACE build screen after reaching intro_start, before waiting for frame_begin.\n\n'
    text+='The independent Linux beta run reproduced the earlier raw measurements and cartridge hashes. '
    text+='Stable results above are a new run after promotion, using the preserved beta drawing kernel. '
    text+='These checks measure emulated C64 time; physical C64 and NTSC are not measured.\n\n'
    text+='V2 adds no reserved RAM to the drawing helper. Fixed graphics storage is 27,000 bytes '
    text+='and staging/metadata caches reserve 11,264 bytes. These components are not a total free-RAM figure. '
    text+='ROM and runtime sizes for each historical row are in the full chart.\n\n'
    text+='Reproduce with `JOBS=3 bash COMPILE-RELEASE.sh --workspace ../c64-072-release-build`. '
    text+='Detailed JSON evidence is in `docs/benchmarks/hors-v2/`; full monitor traces remain in the external release workspace.\n'
    (ROOT/'docs/HORS_RENDER_V2_RESULTS.md').write_text(text)
    version=(ROOT/'VERSION').read_text().strip()
    release=ROOT/'docs/benchmarks'/('release-'+version)
    release.mkdir(parents=True,exist_ok=True)
    for source,name in [(checks/'unit.log','unit.txt'),(checks/'canonical.log','canonical.txt'),
                        (work/'example-checks/summary.json','examples.json'),
                        (work/'color-combo-checks.json','color-combo.json'),
                        (work/'demo1-color-checks.json','demo1-colors.json'),
                        (work/'demo2-color-checks.json','demo2-colors.json'),
                        (checks/'hors-v3-defaults/validation.json','hors-v3-defaults.json'),
                        (checks/'saku/results.json','saku.json')]:
        shutil.copy2(source,release/name)
    unit=(checks/'unit.log').read_text()
    count=re.search(r'Ran (\d+) tests?',unit)
    skipped=re.search(r'skipped=(\d+)',unit)
    v3=json.loads((ROOT/'docs/benchmarks/hors-v3-preview/summary.json').read_text())
    dragon=json.loads((ROOT/'examples/stanford_dragon/validation.json').read_text())
    report=dict(passed=True,version=version,unit_tests=int(count[1]) if count else None,
        unit_skipped=int(skipped[1]) if skipped else 0,v2_examples=proof,
        hors_v3_cartridges=len(v3['results']),stanford_dragon_cartridges=len(dragon['results']),
        stanford_dragon_pictures=sum(r['verification']['verified_frames'] for r in dragon['results']),
        canonical_comparison_passed=True,physical_hardware_tested=False,
        default_renderer='hors-renderer-v3',menu_renderer='hors-render-v2',
        saku_checks=json.loads((checks/'saku/results.json').read_text()),
        hors_v3_default_checks=json.loads((checks/'hors-v3-defaults/validation.json').read_text()))
    (release/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(text)


if __name__=='__main__':main()
