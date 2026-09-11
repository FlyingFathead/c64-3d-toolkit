#!/usr/bin/env python3
"""Build, validate and package a release in isolation; never commit, tag or push."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','build','logs','comparison-tests','__pycache__','.pytest_cache'}


def source_files(root):
    for parent,dirs,names in os.walk(root):
        dirs[:]=sorted(d for d in dirs if d not in SKIP)
        for name in sorted(names):
            # A linked worktree uses a .git file, not a directory. Never copy
            # its pointer into a release or an external A/B build tree.
            if name in SKIP:continue
            path=Path(parent)/name
            if path.suffix not in ('.pyc','.zip') and not path.is_symlink():yield path


def package(root, output, baseline=None):
    current={p.relative_to(root).as_posix():p for p in source_files(root)}
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel,path in current.items():z.write(path,rel)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:raise ValueError('Package CRC failure')
    if baseline:
        with zipfile.ZipFile(baseline) as z:
            prefix='' if 'VERSION' in z.namelist() else next(n[:-7] for n in z.namelist() if n.endswith('/VERSION'))
            old={n[len(prefix):]:hashlib.sha256(z.read(n)).digest() for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
        patch=output.with_name(output.stem.replace('-complete','-overlay')+'.zip')
        with zipfile.ZipFile(patch,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for rel,path in current.items():
                if old.get(rel)!=hashlib.sha256(path.read_bytes()).digest():z.write(path,rel)
        return [output,patch]
    return [output]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=3)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',default='/usr/local/share/vice')
    p.add_argument('--baseline-zip',type=Path,help='Also produce an overlay relative to this source ZIP')
    p.add_argument('--install',action='store_true',help='Install verified files and archive obsolete local examples after all checks pass')
    a=p.parse_args();work=a.workspace.expanduser().resolve()
    if work==ROOT or ROOT in work.parents:p.error('Workspace must be outside the checkout')
    if work.exists():p.error('Choose a new workspace directory')
    if a.jobs<1:p.error('--jobs must be positive')
    work.mkdir(parents=True);stage=work/'source';stage.mkdir()
    for path in source_files(ROOT):
        dest=stage/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    logs=work/'logs';logs.mkdir()
    env=os.environ.copy()
    env.update(JOBS=str(a.jobs),PYTHON=sys.executable,TASS=a.tass,CARTCONV=a.cartconv,
        VICE=a.vice,VICE_DATA=str(Path(a.vice_data).expanduser().resolve()),
        C64_VICE_REAL=str(Path(shutil.which(a.vice) or a.vice).resolve()),
        C64_VICE_LOG_DIR=str(work/'vice-logs'))
    wrapper=str(stage/'VICE-BATCH.sh')
    def run(label,args):
        print(label,flush=True)
        with (logs/(label+'.log')).open('w') as log:
            proc=subprocess.Popen(args,cwd=stage,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:print(line,end='',flush=True);log.write(line)
            if proc.wait():raise RuntimeError(label+' failed; see '+str(logs/(label+'.log')))
    run('build-examples',[sys.executable,'tools/build_hors_v2_examples.py','--tass',a.tass,'--cartconv',a.cartconv])
    run('build-showcase',[sys.executable,'tools/build_demo_cart_v2.py','--tass',a.tass,'--cartconv',a.cartconv])
    run('build-color-combos',[sys.executable,'c643d.py','color-combo-test','--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow'])
    run('index-examples',[sys.executable,'tools/index_release_examples.py'])
    run('archive-prebuilt',[sys.executable,'tools/cleanup_examples.py','--apply','--archive',str(work/'old-examples')])
    run('verify-release',[sys.executable,'tools/verify_hors_v2_release.py','--out',str(work/'example-checks'),
        '--vice',wrapper,'--vice-data',env['VICE_DATA'],'--jobs',str(a.jobs)])
    run('verify-version',[sys.executable,'tools/verify_release_version.py','--out',str(work/'version-checks'),
        '--tass',a.tass,'--cartconv',a.cartconv,'--vice',wrapper,'--vice-data',env['VICE_DATA']])
    run('verify-color-combos',[sys.executable,'tools/verify_color_combos.py',str(stage/'examples/color_combo_test/color-combo-test.crt'),
        '--vice',wrapper,'--vice-data',env['VICE_DATA'],'--report',str(work/'color-combo-checks.json')])
    version=(stage/'VERSION').read_text().strip()
    for label,cart in (
        ('demo1',f'examples/cart_demos/c643d-demo-v{version}-hors-render-v2-all.crt'),
        ('demo2','examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt')):
        run('verify-'+label+'-colors',[sys.executable,'tools/verify_demo_colors.py',cart,
            '--vice',wrapper,'--vice-data',env['VICE_DATA'],'--report',str(work/(label+'-color-checks.json'))])
    run('all-checks',['bash','RUN-CHECKS.sh',str(work/'checks')])
    run('release-report',[sys.executable,'tools/report_hors_v2_release.py',str(work)])
    version=(stage/'VERSION').read_text().strip()
    outputs=package(stage,work/f'c64-3d-toolkit-{version}-hors-v2-complete.zip',a.baseline_zip)
    report=dict(passed=True,version=version,renderer='hors-render-v2',installed=a.install,
        packages=[dict(file=x.name,sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in outputs])
    if a.install:
        for path in source_files(stage):
            dest=ROOT/path.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        subprocess.run([sys.executable,str(ROOT/'tools/cleanup_examples.py'),'--apply'],cwd=ROOT,check=True)
    (work/'release.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Release checks passed. Packages and evidence:',work)
    print('No Git commit, tag or push was performed.')


if __name__=='__main__':main()
