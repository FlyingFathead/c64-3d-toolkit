#!/usr/bin/env python3
"""Build and measure fresh baked Marbles exports at requested FPS; bundle failures too."""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',default='marbles-blender-01')
    p.add_argument('--fps',type=int,nargs='+',default=[25,20])
    p.add_argument('--blender',default='blender');p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    a=p.parse_args()
    if not a.id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a.id):p.error('invalid run ID')
    if any(not 1<=n<=50 for n in a.fps):p.error('FPS must be 1..50')
    out=ROOT/'logs'/a.id;out.mkdir(parents=True,exist_ok=False)
    for name in ('blender','tass','cartconv','vice'):
        executable=shutil.which(getattr(a,name))
        if not executable: p.error(f'{name} executable not found')
        setattr(a,name,executable)
    work=ROOT/'comparison-tests/blender-targets'/a.id;work.mkdir(parents=True,exist_ok=True)
    source=work/'source'
    shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('.git','build','logs','comparison-tests','__pycache__','monitor.log'))
    wrapper=work/'vice-default.py'
    wrapper.write_text('#!'+sys.executable+'\nimport os,sys\nos.execv('+repr(a.vice)+',['+repr(a.vice)+",'-console','-default','-pal',*sys.argv[1:]])\n")
    wrapper.chmod(0o755)
    results=[]
    try:
        for fps in dict.fromkeys(a.fps):
            stem=f'marbles-hors-render-v1-blender-{fps}fps';entry={'target_fps':fps,'status':'running'};results.append(entry)
            print(f'Blender output target: {fps} FPS; original source duration; hors-render-v1 clean/FPS preference',flush=True)
            command=[sys.executable,str(source/'c643d.py'),'build','--no-config','--renderer','hors-render-v1-scene','--blend',str(ROOT/'examples/blender_marbles/dont_lose_your_marbles.blend'),'--blender-output-fps',str(fps),'--blender',a.blender,'--tass',a.tass,'--cartconv',a.cartconv,'--intro','--ending','--no-text-overlay','--output',stem,'--output-dir',str(work),'--overwrite-policy','allow']
            with (out/(stem+'.log')).open('w') as log:
                proc=subprocess.Popen(command,cwd=source,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                for line in proc.stdout:
                    log.write(line);log.flush();print(line,end='',flush=True)
                code=proc.wait()
            if code:
                entry.update(status='build_failed',exit_code=code)
                print(f'{fps} FPS build failed; see {out/(stem+".log")}',flush=True)
                continue
            crt=work/(stem+'.crt')
            entry.update(crt_bytes=crt.stat().st_size,sha256=hashlib.sha256(crt.read_bytes()).hexdigest())
            try:
                for tool,key in (('verify_cart_stream.py','pixels'),('profile_cart_stream.py','profile')):
                    report=out/(stem+'-'+key+'.json')
                    with (out/(stem+'-'+key+'.log')).open('w') as log:
                        subprocess.run([sys.executable,str(source/'tools'/tool),str(crt),'--vice',str(wrapper),'--vice-data',a.vice_data,'--report',str(report)],cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
                    entry[key]=json.loads(report.read_text())
                entry['status']='passed'
                print(f'{fps} FPS target: measured profiler interval {entry["profile"]["frames_per_second"]:.2f} FPS; CRT {entry["crt_bytes"]} B',flush=True)
            except Exception as error:
                entry.update(status='verification_failed',error=str(error))
    finally:
        (out/'results.json').write_text(json.dumps({'rates':results,'scope':'Fresh Blender exports; PAL VICE; no music test. Profile intervals include final hold. Fractional targets have alternating refresh budgets; scalar budget counters use the shorter interval.'},indent=2)+'\n')
        bundle=ROOT/'logs'/(a.id+'-results.zip')
        with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(out.rglob('*')):
                if path.is_file():z.write(path,path.relative_to(out.parent))
            for path in sorted(work.glob('marbles-hors-render-v1-blender-*')):
                if path.is_file() and path.suffix in ('.crt','.lbl','.json'):z.write(path,'carts/'+path.name)
        bundle.with_suffix('.zip.sha256').write_text(hashlib.sha256(bundle.read_bytes()).hexdigest()+'  '+bundle.name+'\n')
        print('SEND BACK:',bundle,flush=True)
if __name__=='__main__':main()
