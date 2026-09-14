"""After rebuilding, verify the default demo-menu header in actual VICE screen RAM."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from c643d import __version__
from verify_cart_stream import labels

def verify(cart,vice,data):
    work=root/'build'/f'{cart.stem}-cartridge-demo'
    styles=['default']
    syms=[labels(work/f'{cart.stem}-runtime-{style}.lbl') for style in styles]
    with tempfile.TemporaryDirectory(prefix='menu-title-') as tmp:
        out=Path(tmp);cmds=[]
        def stop(a,start=None):cmds.extend(['delete',f'break ${a:04x}','g' if start is None else f'g ${start:04x}'])
        stop(syms[0]['build_screen_visible'])
        for i,s in enumerate(syms):
            stop(s['menu_wait_key'],syms[0]['build_screen_done'] if i==0 else syms[i-1]['menu_cycle_style'])
            cmds.extend(['bank ram',f'bsave "{out / str(i)}.ram" 0 $0400 $07e7'])
        cmds.append('quit');(out/'run.mon').write_text('\n'.join(cmds)+'\n')
        args=[vice,'-console','-default','-pal','+sound','-warp','+easyflashcrtwrite','-directory',data,'-cartcrt',str(cart),'-initbreak','reset','-monlogname',str(out/'monitor.log'),'-moncommands',str(out/'run.mon'),'-limitcycles','10000000']
        with (out/'vice.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
        rows=[]
        for i,style in enumerate(styles):
            raw=(out/f'{i}.ram').read_bytes()
            text=bytes(b+64 if 1<=b<=26 else b for b in raw).decode('latin1')
            assert __version__ in text,(style,text)
            assert 'HORS-V1' in text,(style,text)
            assert '0.6.9' not in text and 'V:' not in text and 'V10' not in text
            rows.append(dict(style=style,version=__version__,renderer='hors-render-v1',headings=[text[j:j+40].strip() for j in range(0,200,40)]))
    return dict(cartridge=cart.name,styles=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True);p.add_argument('--report',type=Path);a=p.parse_args()
    result=[verify(root/f'examples/cart_demos/c643d-demo-v{__version__}-hors-render-v1-all{suffix}.crt',a.vice,a.vice_data) for suffix in ('','-ram')]
    text=json.dumps(result,indent=2)+'\n';print(text)
    if a.report:a.report.write_text(text)
