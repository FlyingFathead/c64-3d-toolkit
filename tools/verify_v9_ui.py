#!/usr/bin/env python3
"""Verify V9 build/closing screens, Marbles endings and sunflower stage costs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from c643d import __version__
from verify_cart_build_screen import verify as screen
from verify_cart_ending import verify as ending
from verify_play_all_thanks import verify as thanks
from profile_cart_stream import profile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vice',default='x64sc')
    p.add_argument('--vice-data',required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    menu=root/f'examples/cart_demos/c643d-demo-v{__version__}-yunroll-cart-v9-all.crt'
    tasks=[('thanks',thanks,menu)]
    for pref in ('','-ram'):
        tasks.append(('screen-menu'+pref,screen,menu.with_name(menu.stem+pref+'.crt')))
        for hud in ('','-clean'):
            crt=root/f'examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v9-scene{hud}{pref}.crt'
            tasks.append(('screen-marbles'+hud+pref,screen,crt))
            if hud:
                tasks.append(('ending'+pref,ending,crt))
    def run(task):
        name,fn,crt=task
        result=fn(crt,a.vice,a.vice_data,root/'build/v9-ui'/name)
        print(name,'passed',flush=True)
        return name,result
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=dict(pool.map(run,tasks))
    # verify_v9_examples.py builds the V8 symbols first.
    for version in ('v8','v9'):
        crt=root/'../c64-3d-toolkit-history/examples/cart_demos/history/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt' if version=='v8' else menu
        results['sunflower-profile-'+version]=profile(crt,a.vice,a.vice_data,11)
    output=root/'docs/benchmarks/v9/ui-and-stages.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
