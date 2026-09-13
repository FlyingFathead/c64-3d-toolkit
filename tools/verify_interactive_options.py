#!/usr/bin/env python3
"""Build and measure matched interactive carts with stars omitted, off and on."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from verify_cart_stream import labels, verify
from verify_color_combos import run_monitor
from run_sande_perfs import measure

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    results={};oracle_hashes=set()
    cases=[('excluded',['--no-starfield']),('included-disabled',[]),
           ('included-enabled',['--starfield-default','enabled']),
           ('indexed4',['--v3-color-encoding','indexed4'])]
    for name,extra in cases:
        stem='interactive-'+name
        command=[sys.executable,str(ROOT/'c643d.py'),'build','--shape','torus','--frames','48',
            '--surface-fill','metallic','--interactive-cart','--output',stem,'--output-dir',str(out),
            '--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow',*extra]
        subprocess.run(command,cwd=ROOT,check=True)
        cart=out/(stem+'.crt');oracle=out/(stem+'-oracle.json')
        meta=json.loads((out/(stem+'-manifest.json')).read_text());sym=labels(cart.with_suffix('.lbl'))
        oracle_hashes.add(hashlib.sha256(oracle.read_bytes()).hexdigest())
        included=name!='excluded'
        assert meta['background_effect']['included']==included
        assert ('fx_irq' in sym)==included and ('fx_x0' in sym)==included
        assert ('sd_init' in sym)==included and ('sd_visible' in sym)==included
        assert 'hp_poll' in sym and 'sp_poll' in sym
        assert ('Shift+S' in meta['interactive_cart']['keys'])==included
        proof=verify(cart,a.vice,str(a.vice_data),oracle_path=oracle)
        row=dict(pixel_check=proof,stars_included=included,stars_initially_enabled=name=='included-enabled',
                 cartridge_sha256=hashlib.sha256(cart.read_bytes()).hexdigest(),frame_stream_bytes=meta['rom_frame_bytes'])
        with tempfile.TemporaryDirectory(prefix='interactive-options-') as tmp:
            tmp=Path(tmp);cmd=['delete',f'break ${sym["frame_begin"]:04x}','g','bank ram',f'bsave "{tmp}/initial.ram" 0 $0000 $ffff']
            if included:
                for label,value in [('v3_left_shift_read',0x7f),('fx_row1_read',0xdf)]:
                    cmd+=['delete',f'break ${sym[label]:04x}','g',f'r a=${value:02x}']
                cmd+=['delete',f'break ${sym["fx_poll_return"]:04x}','g','bank ram',f'bsave "{tmp}/toggled.ram" 0 $0000 $ffff']
            else:
                for label,value in [('v3_left_shift_read',0x7f),('hp_h_read',0xdf)]:
                    cmd+=['delete',f'break ${sym[label]:04x}','g',f'r a=${value:02x}']
                cmd+=['delete',f'break ${sym["hp_wait"]:04x}','g',f'break ${sym["hp_space_read"]:04x}','g','r a=$ef',
                      'delete',f'break ${sym["hp_restored"]:04x}','g','bank ram',f'bsave "{tmp}/resumed.ram" 0 $0000 $ffff']
            # RUN/STOP uses the existing density row or the small no-stars poll.
            stop_label='sd_row7_read' if included else 'hp_stop_read'
            cmd+=['delete',f'break ${sym[stop_label]:04x}','g','r a=$7f',
                  'delete',f'break ${sym["hp_wait"]:04x}','g',
                  'delete',f'break ${sym["hp_space_read"]:04x}','g','r a=$7f',
                  'delete',f'break ${sym["hp_restored"]:04x}','g',
                  'bank ram',f'bsave "{tmp}/stop-resumed.ram" 0 $0000 $ffff']
            run_monitor(cart,a.vice,a.vice_data,tmp,cmd,40_000_000)
            assert (tmp/'stop-resumed.ram').exists()
            row['native_run_stop_help_verified']=True
            initial=(tmp/'initial.ram').read_bytes()
            assert initial[sym['sp_level']]==3 and 'hp_packed' in sym
            if included:
                assert initial[sym['fx_enabled']]==int(name=='included-enabled')
                assert initial[sym['sd_level']]==3
                assert (tmp/'toggled.ram').read_bytes()[sym['fx_enabled']]==1-initial[sym['fx_enabled']]
                row['native_default_and_toggle_verified']=True
            else:
                assert (tmp/'resumed.ram').exists();row['native_help_without_stars_verified']=True
        if name!='indexed4':row['display']=measure(cart,oracle,a.vice,a.vice_data,1504)
        results[name]=row
        print(name,'passed',row.get('display',{}).get('display_fps'),flush=True)
    assert len(oracle_hashes)==1,'Starfield choices changed the model pictures'
    # Exclusion also works with SVG presentation controls still compiled in.
    spec=importlib.util.spec_from_file_location('saku_verification',ROOT/'examples/saku_2026/verify.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for variant in (False,True):
        stem='eight-modes-without-stars' if variant else 'modes-without-stars'
        extra=['--svg-background-card',str(ROOT/'examples/saku_2026/saku_2026-white-background.svg'),
               '--svg-outline-variant',str(ROOT/'examples/saku_2026/saku_2026-white-outline.svg')] if variant else []
        subprocess.run([sys.executable,str(ROOT/'c643d.py'),'build','--svg',str(ROOT/'examples/saku_2026/saku_2026.svg'),
            '--fill-style','gradient','--interactive-cart','--svg-presentation-modes','--frames','4','--no-starfield',
            '--output',stem,'--output-dir',str(out),'--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow',*extra],cwd=ROOT,check=True)
        oracle=out/(stem+'-oracle.json');oracle.with_suffix('.json.gz').write_bytes(gzip.compress(oracle.read_bytes(),mtime=0))
        cart=out/(stem+'.crt');sym=labels(cart.with_suffix('.lbl'))
        assert 'fx_irq' not in sym and 'fx_x0' not in sym and 'fx_box_test' not in sym and 'fx_advance' in sym
        results[stem]=module.pictures(cart,a.vice,a.vice_data)
    # Fixed and runtime-selectable startup HUD states; no geometry changes.
    for name,extra,interactive,toggle,visible in [
        ('hud-hidden-toggle',['--hide-hud','--allow-hud-toggle'],True,True,False),
        ('hud-visible-fixed',['--show-hud','--no-hud-toggle'],True,False,True),
        ('hud-hidden-fixed',['--hud-default','disabled','--no-hud-toggle'],True,False,False),
        ('hud-hidden-automatic',['--hide-hud'],False,False,False)]:
        command=[sys.executable,str(ROOT/'c643d.py'),'build','--shape','torus','--frames','8',
                 '--surface-fill','metallic','--no-starfield','--output',name,'--output-dir',str(out),
                 '--tass',a.tass,'--cartconv',a.cartconv,'--overwrite-policy','allow',*extra]
        if interactive:command.append('--interactive-cart')
        subprocess.run(command,cwd=ROOT,check=True)
        cart=out/(name+'.crt');meta=json.loads(cart.with_name(name+'-manifest.json').read_text());sym=labels(cart.with_suffix('.lbl'))
        assert meta['hud_visibility']['initial_info']==visible and meta['hud_visibility']['toggle_allowed']==toggle
        assert ('ui_poll' in sym)==toggle
        if interactive:
            assert ('Shift+U' in meta['interactive_cart']['keys'])==toggle
            assert any('SHIFT+U' in line for line in meta['interactive_cart']['help']['lines'])==toggle
        results[name]=dict(pixel_check=verify(cart,a.vice,str(a.vice_data),oracle_path=out/(name+'-oracle.json')))
        if toggle:results[name]['keys']=module.hud_keys(cart,a.vice,a.vice_data)
        print(name,'passed',flush=True)
    results['excluded']['hud_keys']=module.hud_keys(out/'interactive-excluded.crt',a.vice,a.vice_data)
    report=dict(passed=True,workload='48-sample metallic torus; identical geometry and host pictures',
        pal_vice=True,results=results,oracle_sha256=next(iter(oracle_hashes)),
        measurement='1504 PAL refreshes after warmup; actual display transitions; help/startup excluded')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
