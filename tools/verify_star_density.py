#!/usr/bin/env python3
"""Native number-key density controls, limits, debounce and sprite patterns."""
import json
from pathlib import Path
import tempfile
from c643d.hors_v3_density import LEVELS, POINTS
from verify_cart_stream import labels
from verify_color_combos import run_monitor


def pattern(level, width=1):
    result=bytearray(63)
    for x,y in POINTS[:max(1,LEVELS[level]//8)]:
        for w in range(width):result[y*3+(x+w)//8]|=128>>((x+w)&7)
    return result


def setup_commands(sym,level):
    # Measurement-only setup; the event handler is independently exercised below.
    result=[f'> ${sym["sd_level"]:04x} ${level:02x}',
            f'> ${sym["sd_dot_count"]:04x} ${max(1,LEVELS[level]//8):02x}',
            f'> ${sym["sd_sprite_count"]+1:04x} ${min(8,LEVELS[level])-1:02x}']
    for base in (0x3f80,0x7f80,0xff80):
        result.append(f'> ${base:04x} '+' '.join(f'${n:02x}' for n in pattern(level)))
        result.append(f'> ${base-64:04x} '+' '.join(f'${n:02x}' for n in pattern(level,2)))
    return result


def verify(crt,vice,data,out):
    crt=Path(crt);sym=labels(crt.with_suffix('.lbl'));checks=[]
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='star-density-') as tmp:
        tmp=Path(tmp);cmd=[]
        def stop(label):cmd.extend(['delete',f'break ${sym[label]:04x}','g'])
        def sample(label,value):stop(label);cmd.append(f'r a=${value:02x}')
        def snap(level,speed,name):
            stop('sp_poll_return');cmd.extend(['bank ram',f'bsave "{tmp/str(len(checks))}.ram" 0 $0000 $ffff'])
            checks.append((level,speed,name))
        def release():
            sample('sp_row5_read',255);sample('sp_row4_read',255)
            sample('sd_row7_read',255);sample('sd_row1_read',255);stop('sp_poll_return')
        def key(k,level,speed=3,held=False):
            sample('sp_row5_read',254 if k=='+' else 247 if k=='-' else 255)
            if k not in ('+','-'):sample('sp_row4_read',247 if k=='0' else 255)
            if k in ('1','2','3'):
                sample('sd_row7_read',254 if k=='1' else 247 if k=='2' else 255)
                if k=='3':sample('sd_row1_read',254)
            snap(level,speed,k)
            if not held:release()
        meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
        if meta['background_effect']['profiles']['default']=='light':
            for label,value in [('sp_row5_read',255),('sp_row4_read',255),('sd_row7_read',255),('sd_row1_read',247)]:
                sample(label,value)
            stop('sp_poll_return');release()
        snap(3,3,'full-profile-selected')
        key('2',4,held=True);key('2',4);key('2',5);key('2',5)
        key('1',3)
        for level in (2,1,0,0):key('3',level)
        key('1',3)
        key('+',3,4);key('-',3,3);key('0',3,3)
        run_monitor(crt,vice,data,tmp,cmd,40_000_000)
        for i,(level,speed,name) in enumerate(checks):
            ram=(tmp/str(i)).with_suffix('.ram').read_bytes()
            assert ram[sym['sd_level']]==level,(name,'density')
            assert ram[sym['sp_level']]==speed,(name,'speed')
            assert ram[sym['sd_dot_count']]==max(1,LEVELS[level]//8)
            assert ram[sym['sd_sprite_count']+1]==min(8,LEVELS[level])-1
            for base in (0x3f80,0x7f80,0xff80):
                assert ram[base:base+63]==pattern(level),(name,'pattern',hex(base))
                assert ram[base-64:base-1]==pattern(level,2),(name,'near pattern',hex(base-64))
    result=dict(passed=True,keys=len(checks),levels=list(LEVELS),profile='full',default=16,
                number_keys_only_affect_density=True,speed_keys_only_affect_speed=True,
                keymap={'1':'reset','2':'more','3':'less'},
                maximum_minimum_clamped=True,held_key_debounce=True,all_three_sprite_patterns=True)
    (out/'density-keys.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
