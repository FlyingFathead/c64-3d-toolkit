#!/usr/bin/env python3
"""Verify the V5 build screen, timeout and CIA SPACE-skip path in PAL VICE."""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
from c643d.cartpaths import menu_manifest_path
from verify_cart_stream import labels
from verify_cart_ending import text_image
from c643d.buildscreen import screen_codes


def verify(crt, vice, vice_data, output):
    crt=Path(crt).resolve();root=Path(__file__).resolve().parents[1]
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    multi=menu_manifest_path(crt)
    if multi.exists():
        m=json.loads(multi.read_text())
        sym=labels(root/'build'/f'{crt.stem}-cartridge-demo'/f'{crt.stem}-runtime-{m["menu_style"]}.lbl')
        next_label='menu_wait_key'
    else:
        m=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
        sym=labels(crt.with_suffix('.lbl'));next_label='intro_stage_1'
    result=dict(cartridge=crt.name,tests={})
    for skip in (False,True):
        with tempfile.TemporaryDirectory(prefix='c643d-screen-') as tmp:
            tmp=Path(tmp)
            mon=['delete',f'break ${sym["build_screen_visible"]:04x}','g','stopwatch',
                 'bank ram',f'bsave "{tmp}/screen.ram" 0 $0000 $ffff',
                 'bank cpu',f'bsave "{tmp}/screen.io" 0 $d000 $dbff','delete']
            if skip:
                # Drive the selected SPACE column low through the CIA port.
                # This checks the native scanner/branch, not a host key event.
                mon += ['> $dc01 $00','> $dc03 $10']
            mon += [f'break ${sym["build_screen_done"]:04x}','g','stopwatch','delete']
            if skip: mon += ['> $dc03 $00']
            mon += [f'break ${sym[next_label]:04x}','g','stopwatch','quit']
            (tmp/'run.mon').write_text('\n'.join(mon)+'\n')
            cmd=[str(vice),'-console', '+easyflashcrtwrite','-pal','+sound','-warp','-seed','1','-cartcrt',str(crt),
                 '-initbreak','reset','-moncommands',str(tmp/'run.mon'),'-monlog',
                 '-monlogname',str(tmp/'monitor.log'),'-directory',str(vice_data),'-limitcycles','20000000']
            with (tmp/'vice.log').open('w') as log:
                subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
            text=(tmp/'monitor.log').read_text();ticks=[int(t) for t in re.findall(r'Stopwatch:\s*(\d+)',text)]
            assert len(ticks)==3,text[-1000:]
            elapsed=(ticks[1]-ticks[0])/985248
            assert elapsed<0.02 if skip else 2.95<elapsed<3.02,elapsed
            r=bytearray((tmp/'screen.ram').read_bytes());r[0xd000:0xdc00]=(tmp/'screen.io').read_bytes()
            assert r[0xd020]&15==0 and r[0xd021]&15==0
            assert r[0xd011]&0x7f==0x1b and r[0xd018]&0xfe==0x16
            assert all((c&15)==1 for c in r[0xd800:0xdbe8])
            for line in ['c64-3d-toolkit','v. '+m['build_screen']['version'],m['build_screen']['renderer'],
                         'github.com/FlyingFathead/c64-3d-toolkit','SPACE to start']:
                assert bytes(screen_codes(line)) in r[0x400:0x7e8],line
            if not skip:
                char=next((Path(vice_data)/'C64').glob('chargen-901225*')).read_bytes()[0x800:]
                from PIL import Image
                text_image(r,char,0).resize((960,600),Image.Resampling.NEAREST).save(output/'build-screen.png')
            result['tests']['space_scan' if skip else 'timeout']=dict(seconds=elapsed,following_screen_reached=True)
    result['skip_input']='CIA column driven low in monitor; host keyboard event injection not exercised'
    (output/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt');p.add_argument('--vice',default='x64sc')
    p.add_argument('--vice-data',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.crt,a.vice,a.vice_data,a.output),indent=2))
