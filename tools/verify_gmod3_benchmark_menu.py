#!/usr/bin/env python3
"""Check the preserved benchmark front door using native VICE keyboard maps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from c643d.gmod3_probe import labels, vice_command
from c643d.buildscreen import screen_codes

ROOT=Path(__file__).resolve().parents[1]


def verify(vice,data,output):
    folder=ROOT/'examples/gmod3_cart_demos';crt=folder/'demo-cart-v3.0-gmod3-all-in-one-benchmark.crt'
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    digest=hashlib.sha256(crt.read_bytes()).hexdigest()
    assert digest=='952704768c86994cbec5a4eaa83430876b60ba4d8055a82ca5f8fd744031af84'
    menu=labels(folder/meta['collection_labels']);results=[]
    output.mkdir(parents=True,exist_ok=True)
    for mode,index in [('sym',2),('pos',3)]:
        with tempfile.TemporaryDirectory(prefix='benchmark-menu-') as td:
            tmp=Path(td);shim=tmp/'hostkeys.so'
            subprocess.run(['cc','-shared','-fPIC','-o',str(shim),str(ROOT/'tools/vice_hostkeys.c'),'-ldl'],check=True)
            commands=['delete',f'break ${menu["menu_poll"]:04x}','g','delete','z $20000'];events=[]
            def key(k,down,mod=0):
                commands.append(f';hostkey {k} {mod} {int(down)}');events.append(f'HOSTKEY {k} {mod} {int(down)}')
            def tap(k):
                key(k,True);commands.append('z $20000');key(k,False);commands.append('z $20000')
            def snap(name):commands.extend(['bank ram',f'bsave "{tmp/name}.ram" 0 $0000 $ffff'])
            for selected in range(65):
                snap(str(selected))
                if selected in (0,15,30,45,60):commands.append(f'scrsh "{output}/benchmark-{mode}-{selected//15}.png" 2')
                tap(65363)
            snap('wrap')
            key(65505,True);tap(65363);key(65505,False);commands.append('z $20000');snap('reverse-wrap')
            tap(32);commands.append('z $80000');snap('started')
            commands.append('quit');(tmp/'run.mon').write_text('\n'.join(commands)+'\n')
            env=os.environ.copy();env['LD_PRELOAD']=str(shim)
            with (tmp/'vice.log').open('w') as log:
                subprocess.run(vice_command(vice,crt,data)+['-keymap',str(index),f'-{mode}keymap',str(data/'C64'/f'gtk3_{mode}.vkm'),
                    '-initbreak','reset','-moncommands',str(tmp/'run.mon')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
            assert re.findall(r'HOSTKEY \d+ \d+ [01]',(tmp/'vice.log').read_text())==events
            for selected in range(65):
                ram=(tmp/f'{selected}.ram').read_bytes();assert ram[0x330]==selected
                for row,text in [(0,'Demo Cart v3.0'),(1,'GMod3 All-in-One / benchmark'),
                    (2,f'HORS-V4-GMOD3 | 65 entries | page {selected//15+1}/5'),
                    (19,'CURSOR: choose | SPACE: start'),(21,'No input polling or starfield'),
                    (23,'used: 13416 KiB | free: 2968 KiB')]:
                    assert ram[0x400+row*40:0x400+(row+1)*40]==bytes(screen_codes(text.center(40))),(mode,selected,row)
                start=(selected//15)*15
                for i,e in enumerate(meta['entries'][start:start+15]):
                    line=f'{e["index"]+1:02d} {e["name"][:30]:<30} {e["frames"]:4d}  '[:40].ljust(40)
                    expected=screen_codes(line)
                    if e['index']==selected:expected=[x|128 for x in expected]
                    assert ram[0x400+(4+i)*40:0x400+(5+i)*40]==bytes(expected)
            assert (tmp/'wrap.ram').read_bytes()[0x330]==0
            assert (tmp/'reverse-wrap.ram').read_bytes()[0x330]==64
            ram=(tmp/'started.ram').read_bytes();last=labels(folder/meta['entries'][64]['labels'])
            assert ram[0x330]==64 and ram[last['tick_counter']]>0,'SPACE did not start last demo'
            results.append(dict(keymap=mode,all_65_entries_correct=True,all_five_pages=True,space_launch=True,wrap_both_directions=True,host_events=len(events)))
    result=dict(passed=True,crt_sha256=digest,benchmark_unchanged=True,results=results)
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vice',required=True);p.add_argument('--vice-data',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/release-0.8.1/benchmark-menu');a=p.parse_args()
    print(json.dumps(verify(a.vice,a.vice_data.resolve(),a.output.resolve()),indent=2))
