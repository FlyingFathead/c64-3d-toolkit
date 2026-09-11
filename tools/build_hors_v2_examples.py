#!/usr/bin/env python3
"""Rebuild every active v2 example from frozen complete pictures and sources."""
import argparse
import hashlib
import json
from pathlib import Path
from c643d import cli,cartuniform,__version__
from c643d.released_examples import load,decode
from c643d.hors_v2_stable import assemble_cartridge,assemble_scene
from c643d.cartframes import load_menu_reference
from c643d.toolchain import load_toolchain_settings

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    from c643d.cartridge import add_legacy_cart_argument
    add_legacy_cart_argument(p)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--only',help='Substring of replacement path (default: all)')
    a=p.parse_args();outputs=[]
    for row in load(ROOT):
        old=Path(row['old']);new=Path(str(old).replace('hors-render-v1','hors-render-v2'))
        if a.only and a.only not in str(new):continue
        if a.legacy_cart:new=new.with_stem(new.stem+'-legacy')
        print('Rebuilding',new,flush=True)
        frames,mesh,scene=decode(row);s=row['settings']
        options=dict(legacy_cart=a.legacy_cart,tass=a.tass,cartconv=a.cartconv,outdir=ROOT/new.parent,stem=new.stem,
            colors=s['colors'],color_index=s['screen_color']>>4,prefer=s.get('preference','fps'),draw_gap=3)
        if s['format']=='c643d-easyflash-stream-scene':
            crt,manifest=assemble_scene(ROOT,frames,scene,**options,hud_text=s['hud_text'],
                frame_ticks=s['frame_ticks'],intro=s['intro'],ending=s['ending'],
                text_overlay=s['text_overlay'],output_fps=s.get('output_fps'))
        else:
            crt,manifest=assemble_cartridge(ROOT,frames,mesh,**options,hud=bytes.fromhex(row['hud']))
        manifest['source_reference']=dict(path='assets/released-example-pictures-v1.json.gz',
            original_crt=row['old'],original_sha256=row['source_sha256'],
            preserved='all source pictures, resolved colours, sample order, HUD and presentation pacing')
        crt.with_name(crt.stem+'-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        outputs.append(dict(path=str(new),sha256=hashlib.sha256(crt.read_bytes()).hexdigest()))
    parser=cli.make_parser(load_toolchain_settings(ROOT/'config/c643d.ini'))
    for prefer in ('fps','ram'):
        if a.only and 'cart_demos' not in a.only:continue
        args=parser.parse_args(['cart-demos','--prefer',prefer,'--tass',a.tass,
            '--cartconv',a.cartconv,'--overwrite-policy','allow'])
        args.legacy_cart=a.legacy_cart
        cartuniform.build(args,sources=load_menu_reference(ROOT))
    if not a.only or 'cart_hifi' in a.only:
        import build_hifi_cart
        build_hifi_cart.main(['--renderer','hors-render-v2','--tass',a.tass,'--cartconv',a.cartconv]+(['--legacy-cart'] if a.legacy_cart else []))
    (ROOT/'build/hors-v2-example-build.json').write_text(json.dumps(outputs,indent=2)+'\n')


if __name__=='__main__':main()
