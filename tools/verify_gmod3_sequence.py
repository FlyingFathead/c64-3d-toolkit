#!/usr/bin/env python3
"""Check every benchmark transition, final displayed picture and reset."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from verify_gmod3_collection import ROOT, labels, run_monitor
from c643d.gmod3_catalog import frames_for
from verify_cart_stream import expected_frame


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/gmod3-sequence.json');a=p.parse_args()
    crt=a.crt.resolve();meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    assert not meta['interactive'];menu=labels(crt.parent/meta['collection_labels']);checks=[]
    with tempfile.TemporaryDirectory(prefix='gmod3-sequence-') as td:
        tmp=Path(td);cmd=['delete',f'break ${menu["menu_poll"]:04x}','g','delete','z 100',
            f'break ${menu["menu_space_read"]:04x}','g','r a=$ef','delete',f'break ${menu["menu_space_release"]:04x}','g',
            'delete','break $a600']
        for i in range(len(meta['entries'])+1):
            cmd+=['g','stopwatch','bank ram',f'bsave "{tmp}/{i}.ram" 0 $0000 $ffff']
        # Return via real reset paths after running all bank ranges.
        for kind in (0,1):
            cmd+=['delete',f'break ${menu["menu_poll"]:04x}',f'reset {kind}','bank ram',
                f'bsave "{tmp}/reset-{kind}.ram" 0 $0000 $ffff']
        ticks=run_monitor(crt,a.vice,a.vice_data,tmp,cmd,1_800_000_000)
        assert len(ticks)==len(meta['entries'])+1
        for i,row in enumerate(meta['entries']+[meta['entries'][0]]):
            ram=(tmp/f'{i}.ram').read_bytes();sym=labels(crt.parent/row['labels'])
            assert ram[0x330]==row['index'],('entry order',i,ram[0x330])
            assert ram[sym['ready_slot']]==255,('unpublished final picture',i)
            count=int.from_bytes(ram[menu['collection_count']:menu['collection_count']+2],'little')
            assert count==row['frames'],('incomplete sequence',i,count)
            slot=ram[sym['display_slot']];fi=ram[sym['slot_frame']+slot]
            assert fi==(row['frames']-1)%(128 if row['frames']>255 else 256),(i,fi)
            frames=frames_for(ROOT/'build/gmod3-catalog',row)
            if 'slice' in row:frames=frames[slice(*row['slice'])]
            bm,sc=expected_frame(frames[-1].__dict__,row['screen_color'])
            baddr,saddr=(0x2000,0x6000,0xe000)[slot],(0x400,0x4400,0xc800)[slot]
            assert ram[baddr:baddr+7680]==bm and ram[saddr:saddr+960]==sc,('last picture',i)
            checks.append(dict(index=row['index'],name=row['name'],frames=count,last_picture_displayed=True,
                elapsed_since_previous_cycles=ticks[i]-ticks[i-1] if i else None))
        for kind in (0,1):assert (tmp/f'reset-{kind}.ram').read_bytes()[0x330]==0
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(passed=True,crt_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        space_start=True,automatic_wrap=True,soft_and_hard_reset=True,entries=checks),indent=2)+'\n')
    print('PASS all benchmark entries, full final picture holds, wrap and resets')

if __name__=='__main__':main()
