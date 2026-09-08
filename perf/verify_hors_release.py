#!/usr/bin/env python3
"""Verify built hors-render-v1 menu pictures, authored scenes and native Marbles endings."""
import argparse,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_cart_stream import verify
from profile_cart_stream import profile
from verify_cart_ending import verify as ending
from verify_v7_play_all import verify as play_all

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--workers',type=int,choices=range(1,5),default=4)
    a=p.parse_args();out=ROOT/'logs/hors-release';out.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for crt in sorted((ROOT/'examples').rglob('*hors-render-v1*.crt')):
        if 'cart_demos' in crt.parts:
            jobs.extend((crt,i) for i in range(12))
        else:jobs.append((crt,None))
    def run(job):
        crt,i=job;result={'cart':crt.name,'entry':i,'pixels':verify(crt,a.vice,a.vice_data,menu_entry=i)}
        if i is None:
            result['profile']=profile(crt,a.vice,a.vice_data)
            if 'marbles' in crt.name:result['ending']=ending(crt,a.vice,a.vice_data,out/(crt.stem+'-ending'))
        (out/(crt.stem+('-'+str(i) if i is not None else '')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(crt.name,i,'PASS',flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(run,jobs))
    for crt in sorted((ROOT/'examples/cart_demos').glob('*hors-render-v1*.crt')):
        result=play_all(crt,a.vice,a.vice_data)
        (out/(crt.stem+'-controls.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('hors-render-v1 release checks passed; reports:',out)
if __name__=='__main__':main()
