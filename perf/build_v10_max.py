#!/usr/bin/env python3
"""Build max-speed Marbles carts: all original samples, one-refresh minimum hold."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from c643d import cartscene
from c643d.cartframes import load_scene_source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass')
    p.add_argument('--cartconv',default='cartconv')
    a=p.parse_args()
    frames,scene,ref=load_scene_source(ROOT/'../c64-3d-toolkit-history/examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt')
    for prefer in ('fps','ram'):
        for hud in (True,False):
            stem='dont_lose_your_marbles-yunroll-cart-v10-scene-max'+('' if hud else '-clean')+('-ram' if prefer=='ram' else '')
            cartscene.assemble_scene(ROOT,frames,scene,tass=a.tass,cartconv=a.cartconv,
                outdir=ROOT/'comparison-tests/v10-max-diagnostic',stem=stem,hud_text=ref['hud_text'],
                frame_ticks=1,colors=ref['colors'],color_index=ref['screen_color']>>4,
                intro=True,ending=True,text_overlay=hud,renderer='yunroll-cart-v10-scene',prefer=prefer)
if __name__=='__main__': main()
