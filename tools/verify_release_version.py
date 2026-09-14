#!/usr/bin/env python3
"""Build v1/v2 menus under a different VERSION and check actual VICE screens."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    if not a.worker:
        from compile_release import source_files
        version='9.8.7' if (ROOT/'VERSION').read_text().strip()!='9.8.7' else '9.8.6'
        with tempfile.TemporaryDirectory(prefix='c643d-version-probe-') as td:
            root=Path(td)
            for path in source_files(ROOT):
                rel=path.relative_to(ROOT)
                if rel.parts[0] in ('docs','examples'):continue
                dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
            (root/'VERSION').write_text(version+'\n')
            cmd=[sys.executable,str(root/'tools/verify_release_version.py'),'--worker','--out',str(a.out),
                 '--tass',a.tass,'--cartconv',a.cartconv,'--vice',a.vice,'--vice-data',a.vice_data]
            subprocess.run(cmd,cwd=root,check=True)
        return
    from c643d import cli,cartuniform,__version__
    from c643d.cartframes import load_menu_reference
    from c643d.toolchain import load_toolchain_settings
    from c643d.cartpaths import menu_manifest_path
    from verify_cart_stream import labels,startup_monitor
    parser=cli.make_parser(load_toolchain_settings(ROOT/'config/c643d.ini'))
    sources=load_menu_reference(ROOT)[:3];reports=[]
    for renderer in ('hors-render-v1','hors-render-v2'):
        stem='version-probe-'+renderer
        options=parser.parse_args(['cart-demos','--stream-renderer',renderer,'--output',stem,
            '--output-dir',str(ROOT/'carts'),'--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow'])
        cartuniform.build(options,sources=sources)
        crt=ROOT/'carts'/(stem+'.crt');meta=json.loads(menu_manifest_path(crt).read_text())
        assert meta['version']==__version__
        subprocess.run([sys.executable,str(ROOT/'tools/verify_cart_menu.py'),str(crt),'--vice',a.vice,
            '--vice-data',a.vice_data,'--report',str(a.out/(renderer+'-menu.json'))],check=True)
        work=ROOT/'build'/(stem+'-cartridge-demo');s=labels(work/(stem+'-runtime-default.lbl'))
        startup,go=startup_monitor(meta,s)
        mon=['delete',*startup,f'break ${s["menu_wait_key"]:04x}',go,'delete',
             f'break ${s["play_all_thanks_visible"]:04x}',f'g ${s["play_all_thanks_start"]:04x}',
             'bank ram',f'bsave "{work / "thanks.ram"}" 0 $0000 $ffff','quit']
        (work/'version.mon').write_text('\n'.join(mon)+'\n')
        with (a.out/(renderer+'-thanks.log')).open('w') as log:
            subprocess.run([a.vice,'-console','-pal','+sound','-warp','-seed','1','+easyflashcrtwrite',
                '-directory',a.vice_data,'-cartcrt',str(crt),'-initbreak','reset',
                '-monlogname',str(work/'monitor.log'),'-moncommands',str(work/'version.mon'),'-limitcycles','10000000'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
        assert __version__.encode() in (work/'thanks.ram').read_bytes()[0x400:0x800]
        reports.append(dict(renderer=renderer,version=__version__,all_menu_styles=True,build_screen=True,thanks_screen=True))
    (a.out/'validation.json').write_text(json.dumps(dict(passed=True,checks=reports),indent=2)+'\n')
    print('Alternate VERSION probe PASS:',__version__,'v1/v2 startup, all menu styles and thanks screens')


if __name__=='__main__':main()
