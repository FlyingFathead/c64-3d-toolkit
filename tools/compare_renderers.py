#!/usr/bin/env python3
"""Reproduce renderer FPS lookup tables entirely outside the project checkout.

Normal PLAY ALL ONLY supplies comparative throughput. F5 is never benchmarked.
Historical resident code uses a test-only relocated timer and launch metadata;
all renderer instruction bytes and encoders stay unchanged. Generated products
and raw JSON stay in --workspace. Copy PERFORMANCE_COMPARISON.md into docs only
after all jobs and assertions pass. Use --check before releasing.
"""
from pathlib import Path
import argparse,sys,os,json,hashlib,subprocess,shutil,re
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor

PACING_PLANS={}
MAX_FPS=None
LOCK_MIN=False

class UnsupportedResident(Exception):
    pass

RESIDENT=('step','bytechunk','yunroll','yunroll-cart')
METHODS=[(m,'fps') for m in RESIDENT]+[(f'yunroll-cart-v{i}','fps') for i in range(2,11)]+[(f'yunroll-cart-v{i}','ram') for i in (7,8,9,10)]
METHODS += [('hors-render-v2','fps'),('hors-render-v2','ram')]

SHOWCASE_REPORTS=tuple(f'docs/benchmarks/hors-v2/showcase/{variant}/play-all.json' for variant in ('v1','v2'))
SHOWCASE_CART='examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt'

def fingerprints(root):
    files={}
    for folder in ('c64','tools','assets','config','examples'):
        for p in sorted((root/folder).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.md','.pyc'):continue
            rel=p.relative_to(root).as_posix()
            if rel=='config/c643d.ini':continue
            if folder=='examples':
                if '/old/' in rel:continue
                if p.suffix!='.prg' and not any(key in rel for key in ('dont_lose_your_marbles-yunroll-cart-v4-scene-clean.', 'dont_lose_your_marbles-yunroll-cart-v4-scene-clean-manifest.', 'horse_and_sunflower-yunroll-cart-v7-scene.', 'horse_and_sunflower-yunroll-cart-v7-scene-manifest.')):continue
            files[rel.replace('/history/', '/')]=hashlib.sha256(p.read_bytes()).hexdigest()
    files['.gitignore']=hashlib.sha256((root/'.gitignore').read_bytes()).hexdigest()
    files['VERSION']=hashlib.sha256((root/'VERSION').read_bytes()).hexdigest()
    for rel in (*SHOWCASE_REPORTS,SHOWCASE_CART):
        files[rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    return files,hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()


def showcase_section(root):
    """Display the verified shipped showcase as a separate named workload."""
    left,right=(json.loads((root/rel).read_text()) for rel in SHOWCASE_REPORTS)
    for report,renderer in ((left,'hors-render-v1'),(right,'hors-render-v2')):
        assert report['renderer']==renderer and report['preference']=='fps'
        assert report['mode']=='normal PLAY ALL ONLY' and not report['exhibition']
        assert report['loops']==3 and report['seconds_setting']==10
        assert report['pal_clock_hz']==985248 and report['seed']==1 and report['vice_defaults']
        assert len(report['entries'])==len(report['pixel_verification'])
        for entry,proof in zip(report['entries'],report['pixel_verification'],strict=True):
            assert proof['pixel_match'] and proof['color_match']
            assert proof['orientations']==entry['frame_count']
    assert right['sha256']==hashlib.sha256((root/SHOWCASE_CART).read_bytes()).hexdigest(), 'Showcase results do not match the shipped v2 cartridge; rebuild and rerun the showcase before publishing'
    lines=['','## Demo Cart 2.0','',
        'The seven-scene showcase has its own **hors-render-v1 vs hors-render-v2** comparison. Both methods use identical complete source pictures, colours and sample order. PAL VICE, FPS preference, normal PLAY ALL, three ten-second visits per entry. F5 is excluded.', '',
        'These are the measured shipped showcase cartridges, with their per-scene encoding policy. This is a separate workload from the original twelve-animation matrix; the COLOUR CUBE 24 here is not its CUBE or FALLING CUBES entry. Gains rank displayed-frame counts rather than tiny timer-phase differences.','',
        '| Scene | Samples | v1 FPS | v2 FPS | Gain | v1 worst display ms | v2 worst display ms |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for x,y in zip(left['entries'],right['entries'],strict=True):
        assert (x['name'],x['frame_count'],x['oracle_sha256'])==(y['name'],y['frame_count'],y['oracle_sha256'])
        lines.append(f"| {x['name']} | {x['frame_count']} | {x['display_fps']:.2f} | {y['display_fps']:.2f} | {(y['display_flips']/x['display_flips']-1)*100:+.2f}% | {x['worst_display_ms']:.2f} | {y['worst_display_ms']:.2f} |")
    lines+=['',
        'All seven entries passed bitmap and colour checks for both methods. Worst intervals describe the observed window; a higher average FPS does not guarantee a lower worst interval.', '',
        '[Demo Cart 2.0 and source scenes](../examples/cart_demos_v2/README.md) · [v1 raw results](benchmarks/hors-v2/showcase/v1/play-all.json) · [v2 raw results](benchmarks/hors-v2/showcase/v2/play-all.json) · [Release and HiFi results](HORS_RENDER_V2_RESULTS.md)', '',
        'The chart fingerprint includes both reports and the shipped v2 CRT; generation verifies their cartridge hash and matching picture oracles. The release/check runner refreshes the showcase evidence before generating this page.','']
    return lines

def once(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Comparison adapter needs review: '+old[:90])
    return text.replace(old,new,1)

def adapt_snapshot(root):
    # Only the isolated snapshot is changed. All generations use V9 normal
    # PLAY ALL, with the same timer instructions relocated out of resident data.
    p=root/'tools/c643d/cartuniform.py';s=p.read_text()
    s=once(s,"    print('fps locking: not set')","    print('fps locking: comparison pacing enabled' if 'comparison_pacer' in globals() else 'fps locking: not set')")
    s=once(s,'    image,plans,manifest=pack_demo_prgs(entries,source_root=root)',"    variant='v9' # Comparison controller, not renderer selection\n    image,plans,manifest=pack_demo_prgs(entries,source_root=root)")
    s=once(s,"if any(p.banks!=3 for p in plans) or manifest['highest_bank_used']!=first_free-1:","if manifest['highest_bank_used']!=first_free-1:")
    s=once(s,"        asm=work/'main.asm';asm.write_text(src);prg=work/'runtime.prg'","        if 'comparison_pacer' in globals():src=comparison_pacer(src,demo)\n        asm=work/'main.asm';asm.write_text(src);prg=work/'runtime.prg'")
    s=once(s,'    runtimes={};shared={}',"    rate_plans=[comparison_rate(e['name']) if 'comparison_rate' in globals() else dict(ticks=1) for e in stream_info]\n    (gen/'comparison-rates.inc').write_text('\\n'.join(name+':\\n'+ '\\n'.join(bytes_lines([p.get(key,default) for p in rate_plans])) for name,key,default in [('comparison_base','ticks',1),('comparison_rem','remainder',0),('comparison_den','denominator',1)])+'\\n')\n    runtimes={};shared={}")
    p.write_text(s)
    p=root/'c64/cart/easyflash-demo-scroll-runtime-v9.asm';s=p.read_text()
    s=once(s,'play_all_tick:\n','    .logical $0334\nplay_all_tick:\n')
    s=once(s,'play_all_tick_done:\n    rts','play_all_tick_done:\n    rts\n    .here')
    s=once(s,'runtime_next_demo:\n    jsr runtime_common','runtime_next_demo:\n    jsr runtime_common\n    jsr load_menu_shared')
    old='    ldx selected_entry\n    jsr load_entry_x\n    jsr install_control_shim'
    new='    ldx selected_entry\n'+''.join(f'    lda {name},x\n    sta ${0x300+i:04x}\n' for i,name in enumerate(('demo_irq_lo','demo_irq_hi','demo_entry_lo','demo_entry_hi')))+'    jsr load_entry_x\n    jsr install_control_shim'
    s=once(s,old,new)
    start=s.index('    ; Tell the control shim');end=s.index('; Install the 256-byte',start);chunk=s[start:end]
    for i,name in enumerate(('demo_irq_lo','demo_irq_hi','demo_entry_lo','demo_entry_hi')):
        chunk=once(chunk,f'lda {name},x',f'lda ${0x300+i:04x}')
    s=s[:start]+chunk+s[end:]
    needle='    cpx #$f7\n    bne install_control_loop\n'
    s=once(s,needle,needle+"    lda #2\n    sta EF_BANK\n    lda #$07\n    sta EF_CONTROL\n    ldx #0\ncomparison_timer_copy:\n    lda $a700+MENU_STYLE*$0800,x\n    sta $0334,x\n    inx\n    cpx #64\n    bne comparison_timer_copy\n    lda #1\n    sta $0304\n    lda #0\n    sta $0305\n")
    s=once(s,'.include "cart-demo-data.inc"','.include "cart-demo-data.inc"\n.include "comparison-rates.inc"')
    s=once(s,'    ldx selected_entry\n    lda demo_irq_lo,x','    ldx selected_entry\n    lda comparison_base,x\n    sta $0306\n    lda comparison_rem,x\n    sta $0307\n    lda comparison_den,x\n    sta $0308\n    lda demo_irq_lo,x')
    s=once(s,'    sta $0334,x','    sta $0334,x\n    lda $a780+MENU_STYLE*$0800,x\n    sta $0380,x')
    s=once(s,'.if * > $c800',".fill $c780-*, $ff\n.logical $0380\ncomparison_reload:\n    lda $0306\n    sta $0304\n    lda $0305\n    clc\n    adc $0307\n    cmp $0308\n    bcc comparison_fraction\n    sbc $0308\n    inc $0304\ncomparison_fraction:\n    sta $0305\n    rts\n.here\n.if * > $c800")
    p.write_text(s)
    p=root/'c64/cart/easyflash-demo-control-v9.asm';p.write_text(once(p.read_text(),'jsr $c700','jsr $0334'))
    # Pin the same emulator defaults for image checks and scene diagnostics.
    for name in ('verify_cart_stream.py','profile_cart_stream.py'):
        p=root/'tools'/name;s=p.read_text();s=once(s,"'-console'","'-default','-console'");p.write_text(s)
    p=root/'tools/benchmark_play_all.py';s=p.read_text()
    s=s.replace("s['irq_no_flip']-5","s.get('comparison_flip',s['irq_no_flip']-5)").replace('s["irq_no_flip"]-5',"s.get('comparison_flip',s['irq_no_flip']-5)")
    # The shared benchmark now records intervals natively; adapt only the
    # optional paced flip label, without injecting duplicate keyword fields.
    if 'display_interval_cycles=intervals' not in s:
        raise RuntimeError('Comparison requires the interval-aware PLAY ALL benchmark')
    p.write_text(s)
    p=root/'tools/verify_cart_stream.py';s=p.read_text()
    s=once(s,'        for i in range(count):\n            mon +=',"        mon += [f'trace exec ${sym.get(\"comparison_flip\",sym[\"irq_no_flip\"]-5):04x}']\n        for i in range(count):\n            mon +=")
    s=once(s,'        if len(ticks)!=count:',"        events=[(int(x,16),int(t)) for x,t in re.findall(r'^\\.C:([0-9a-fA-F]{4})\\s.*?\\s(\\d+)\\s*$',(td/'monitor.log').read_text(),re.M)]\n        flips=[t for x,t in events if x==sym.get('comparison_flip',sym['irq_no_flip']-5)]\n        if len(ticks)!=count:")
    s=once(s,"        if manifest.get('frame_index_bits')==16:\n            result.update","        result['display_interval_cycles']=[b-a for a,b in zip(flips,flips[1:])]\n        if manifest.get('frame_index_bits')==16:\n            result.update")
    p.write_text(s)


def configure(a):
    global BASE,ROOT,OUT,REPORT,TASS,VICE,DATA,SOURCES,cli,cartuniform,emit_tables,bytes_lines,new_easyflash_image,load_toolchain_settings,labels,verify,benchmark,ORIGINAL_PREPARE
    BASE=a.workspace;ROOT=BASE/'source';OUT=BASE/'carts';REPORT=BASE/'results'
    for p in (OUT,REPORT):p.mkdir(exist_ok=True)
    TASS=a.tass;VICE=a.vice;DATA=a.vice_data
    sys.path.insert(0,str(ROOT/'tools'))
    from c643d import cli,cartuniform
    from c643d.cartframes import load_menu_reference
    from c643d.emit import emit_tables,bytes_lines
    from c643d.cartridge import new_easyflash_image
    from c643d.toolchain import load_toolchain_settings
    from verify_cart_stream import labels,verify
    from benchmark_play_all import benchmark
    dataset=BASE/'menu-input.json'
    if dataset.exists():
        from c643d.cartuniform import Demo
        from c643d.pipeline import FrameBuild
        data=json.loads(dataset.read_text());SOURCES=[]
        for row in data['demos']:
            row=dict(row);row['frames']=[FrameBuild(**f) for f in row['frames']];row['hud']=bytes.fromhex(row['hud']);SOURCES.append(Demo(**row))
    else:SOURCES=load_menu_reference(ROOT)
    if not SOURCES or any(not d.name for d in SOURCES) or len({d.name for d in SOURCES})!=len(SOURCES):raise ValueError('demo names must be nonempty and unique')
    ORIGINAL_PREPARE=cartuniform.prepare

def aliases(work,colors):
    path=work/'runtime.lbl';sym=labels(path);data=(work/'runtime.prg').read_bytes();load=int.from_bytes(data[:2],'little')
    # Label-only instrumentation: resolve the call site, never alter machine code.
    begin=sym['frame_begin'];at=begin-load+2
    draw=sym['draw_current_lines'];needle=bytes((0x20,draw&255,draw>>8))
    off=data.index(needle,at,at+80);end=load+off-2+3
    pub=sym['publish_completed_frame'];pn=bytes((0x20,pub&255,pub>>8));po=data.index(pn,off,off+50)
    extra={'profile_recycle':begin,'frame_draw_complete':end,'profile_published':load+po-2+3}
    with path.open('a') as f:
        for name,addr in extra.items():
            if name not in sym:f.write(f'al {addr:04x} .{name}\n')

def resident_prepare(root,renderer,tass,tass_args=(),sources=None,prefer='fps'):
    method=METHOD
    entries=[];info=[];fail=[]
    for original_i,d in enumerate(sources):
        work=ROOT/'build'/('resident-'+method)/f'{original_i:02d}';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
        try:
            if max(len(f.records) for f in d.frames)>255:raise RuntimeError('resident record count exceeds 255')
            emit_tables(gen/'tables.inc',d.frames,'yunroll' if method=='yunroll-cart' else method,0)
        except RuntimeError as e:
            fail.append(dict(name=d.name,reason=str(e)));continue
        (gen/'hud.inc').write_text(f'HUD_STATIC_LEN = {len(d.hud)}\nhud_static_bitmap:\n'+'\n'.join(bytes_lines(d.hud))+'\nhud_static_bitmap_end:\n')
        src=(ROOT/f'c64/renderer-{method}.asm').read_text().replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(d.frames)}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(d.colors)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${d.screen:02x}',1)
        if PACING_PLANS:src=apply_pacing(src,PACING_PLANS[d.name])
        (work/'main.asm').write_text(src)
        subprocess.run([tass,'--cbm-prg','--vice-labels','-l',str(work/'runtime.lbl'),'-o',str(work/'runtime.prg'),str(work/'main.asm')],check=True,stdout=subprocess.DEVNULL,cwd=ROOT)
        aliases(work,d.colors)
        (work/'oracle.json').write_text(json.dumps([asdict(f) for f in d.frames]))
        entries.append((d.name,work/'runtime.prg'))
        info.append(dict(name=d.name,renderer=method,frames=len(d.frames),colors=d.colors,screen_color=d.screen,source=d.source,source_sha256=d.source_sha256,work=str(work.relative_to(ROOT)),rom_frame_bytes=0,frame_data=[]))
    (REPORT/(method+'-unsupported.json')).write_text(json.dumps(fail,indent=2))
    if not entries:raise UnsupportedResident('No complete demo fits this resident implementation')
    # Payload banks vary for resident data; no stream pool to reserve.
    from math import ceil
    return entries,new_easyflash_image(),info,[],1+sum(ceil((p.stat().st_size-2)/8192) for _,p in entries)

def beta_prepare(root,renderer,tass,tass_args=(),sources=None,prefer='fps',**unused):
    """Byte-only beta in a private assembly tree; legacy source stays intact.

    Canonical twelve-entry carts retain gap 3 to keep the v1 frame payload
    sizes within the same EasyFlash allocation. This isolates mapping changes.
    Per-scene tuning is measured separately in the new showcase/search.
    """
    import tempfile
    from c643d.hors_v2 import patch_helper,encoder
    root=Path(root)
    with tempfile.TemporaryDirectory(prefix='comparison-hors-v2-') as td:
        stage=Path(td);shutil.copytree(root/'c64',stage/'c64')
        helper=stage/'c64/cart/easyflash-stream-v10-helper.asm'
        helper.write_text(patch_helper(helper.read_text()))
        runtime=stage/'c64/renderer-yunroll-cart-v10.asm';text=runtime.read_text()
        first=text.index('* = $4f00\nv3_entry_lo:');last=text.index('* = $5c00',first)
        runtime.write_text(text[:first]+'v3_entry_lo = $4f00 ; beta direct-only\n'+text[last:])
        entries,image,info,used,first_free=ORIGINAL_PREPARE(stage,'yunroll-cart-v10',tass,tass_args,
            sources=sources,prefer=prefer,work_prefix='comparison-hors-v2',
            frame_encoders={d.name:encoder(3,2048) for d in sources})
        for e in info:
            if e['byte_span_frames']!=e['frames']:raise ValueError('Beta requires all direct byte spans')
            e.update(renderer='hors-render-v2-beta1',wire_format='hors-v2-batched-literal-spans-1',
                     encoding_choice={'gap':3,'batch_budget':2048})
        for path in (stage/'build').iterdir():shutil.copytree(path,root/'build'/path.name,dirs_exist_ok=True)
        entries=[(name,root/path.relative_to(stage)) for name,path in entries]
    return entries,image,info,used,first_free


def menu_worker(method,pref,loops):
    global METHOD
    METHOD=method
    name=METHOD+('-ram' if pref=='ram' else '')
    resident=METHOD in ('step','bytechunk','yunroll','yunroll-cart')
    if resident:cartuniform.prepare=resident_prepare
    beta=METHOD=='hors-render-v2-beta1'
    if beta:cartuniform.prepare=beta_prepare
    stable=METHOD=='hors-render-v2'
    if stable:
        from c643d.hors_v2_stable import prepare_menu
        cartuniform.prepare=lambda *args,**kw:prepare_menu(*args,prepare=ORIGINAL_PREPARE,**kw)
    parser=cli.make_parser(load_toolchain_settings(ROOT/'config/c643d.ini'))
    a=parser.parse_args(['cart-demos','--stream-renderer','yunroll-cart-v9' if resident else 'yunroll-cart-v10' if beta or stable else METHOD,'--prefer',pref,'--output',name,'--output-dir',str(OUT),'--tass',TASS,'--cartconv',CARTCONV,'--overwrite-policy','allow'])
    crt=OUT/(name+'.crt')
    if not crt.exists():
        try:cartuniform.build(a,sources=SOURCES)
        except UnsupportedResident as error:
            (REPORT/(name+'-play-all.json')).write_text(json.dumps(dict(renderer=METHOD,mode='normal PLAY ALL ONLY',exhibition=False,seconds_setting=10,loops=loops,entries=[],unsupported=True,reason=str(error)),indent=2)+'\n')
            (REPORT/(name+'-sizes.json')).write_text(json.dumps(dict(crt_bytes=0,entries=[]))+'\n')
            print(name,'N/A:',error,flush=True);return
    from c643d.cartpaths import menu_manifest_path
    manifest=json.loads(menu_manifest_path(crt).read_text())
    for e in manifest['streamed_entries']:aliases(ROOT/e['work'],e['colors'])
    sizes=[]
    for e in manifest['streamed_entries']:
        work=ROOT/e['work'];sym=labels(work/'runtime.lbl')
        data_ram=0
        if resident:
            data_ram=sym['generated_ptr_end']-0x1600+sym['generated_clear_data_end']-0x4800+sym['generated_line_primary_end']-0x8000
            if 'generated_line_overflow_end' in sym:data_ram+=sym['generated_line_overflow_end']-sym['generated_clear_data_end']
        sizes.append(dict(name=e['name'],runtime_prg_bytes=(work/'runtime.prg').stat().st_size,resident_frame_data_bytes=data_ram,rom_frame_bytes=e['rom_frame_bytes']))
    (REPORT/(name+'-sizes.json')).write_text(json.dumps(dict(crt_bytes=crt.stat().st_size,entries=sizes),indent=2)+'\n')
    dest=REPORT/(name+'-play-all.json')
    if not dest.exists():
        r=benchmark(crt,VICE,DATA,loops=loops);r['renderer']=METHOD;r['harness']='common V9 normal PLAY ALL; external comparison build';dest.write_text(json.dumps(r,indent=2)+'\n')
    for i,e in enumerate(manifest['streamed_entries']):
        dest=REPORT/(name+f'-pixels-{i:02d}.json')
        if dest.exists():continue
        r=verify(crt,VICE,DATA,menu_entry=i);r['name']=e['name'];dest.write_text(json.dumps(r,indent=2)+'\n')
        print(name,e['name'],'pixels verified',flush=True)
    print(name,'COMPLETE',flush=True)
    if MAX_FPS or LOCK_MIN:paced_worker(METHOD,pref,loops)

def apply_pacing(src,plan):
    """Only 11 extra IRQ bytes; fractional reload lives in the test controller."""
    if not 1<=plan['ticks']<=255:raise ValueError('pacing interval exceeds 255 PAL ticks')
    start=src.index('raster_irq:');end=src.index('irq_no_flip:',start)
    block=src[start:end]
    block=once(block,'        lda ready_slot','        dec $0304\n        bne irq_no_flip\n        inc $0304\n        lda ready_slot')
    old='        lda #$ff\n        sta ready_slot'
    block=once(block,old,'comparison_flip:\n'+old+'\n        jsr $0380\n')
    return src[:start]+block+src[end:]


def paced_worker(method,pref,loops):
    """Measure complete uncapped rotations before selecting any automatic cap."""
    global PACING_PLANS
    key=method+('-ram' if pref=='ram' else '')
    from c643d.cartpaths import menu_manifest_path
    baseline=json.loads(menu_manifest_path(OUT/(key+'.crt')).read_text())
    PACING_PLANS={}
    for i,e in enumerate(baseline['streamed_entries']):
        measured=json.loads((REPORT/(key+f'-pixels-{i:02d}.json')).read_text())
        if LOCK_MIN:
            import math
            ticks=math.ceil(measured['max_frame_cycles']/19656)+1
            plan=dict(ticks=ticks,selected_fps=50/ticks,measured_worst_frame_cycles=measured['max_frame_cycles'],guard_pal_ticks=1)
        else:
            plan=dict(ticks=50//MAX_FPS,remainder=50%MAX_FPS,denominator=MAX_FPS,selected_fps=MAX_FPS)
        PACING_PLANS[e['name']]=plan
        print(f"fps locking: {e['name']}: {plan['selected_fps']:.4f} FPS ({'measured minimum + one refresh guard' if LOCK_MIN else 'maximum'})",flush=True)
    cartuniform.comparison_pacer=lambda src,demo:apply_pacing(src,PACING_PLANS[demo.name])
    cartuniform.comparison_rate=lambda name:PACING_PLANS[name]
    name=key+'-paced'
    a=cli.make_parser(load_toolchain_settings(ROOT/'config/c643d.ini')).parse_args(['cart-demos','--stream-renderer','yunroll-cart-v9' if method in RESIDENT else 'yunroll-cart-v10' if method in ('hors-render-v2-beta1','hors-render-v2') else method,'--prefer',pref,'--output',name,'--output-dir',str(OUT),'--tass',TASS,'--cartconv',CARTCONV,'--overwrite-policy','allow'])
    cartuniform.build(a,sources=SOURCES)
    crt=OUT/(name+'.crt');meta=json.loads(menu_manifest_path(crt).read_text())
    for e in meta['streamed_entries']:aliases(ROOT/e['work'],e['colors'])
    result=benchmark(crt,VICE,DATA,loops=loops);result['renderer']=method;result['pacing']=PACING_PLANS
    # Full animation picture checks also trace actual VIC display intervals.
    for i,e in enumerate(meta['streamed_entries']):
        q=verify(crt,VICE,DATA,menu_entry=i)
        (REPORT/(name+f'-pixels-{i:02d}.json')).write_text(json.dumps(q,indent=2)+'\n')
        gaps=q['display_interval_cycles'];assert gaps
        ticks=sorted({round(n/19656) for n in gaps})
        expected=PACING_PLANS[e['name']]['ticks']
        assert min(ticks)>=expected,(e['name'],'cap exceeded',ticks,expected)
        if LOCK_MIN:assert ticks==[expected],(e['name'],'measured minimum not sustainable',ticks,expected)
        result['pacing'][e['name']]['observed_hold_ticks']=ticks
        result['pacing'][e['name']]['met_every_deadline']=max(ticks)<=expected+bool(PACING_PLANS[e['name']].get('remainder',0))
    (REPORT/(name+'-play-all.json')).write_text(json.dumps(result,indent=2)+'\n')


def load_scene_references(root):
    """Frozen vectors recovered from the original V4/V7 CRTs, not rebuilt scenes."""
    import gzip
    from types import SimpleNamespace
    from c643d.pipeline import FrameBuild
    path=Path(root)/'assets/comparison-scene-vector-reference.json.gz'
    blob=path.read_bytes()
    if hashlib.sha256(blob).hexdigest()!='a3fd2a7f93992e475c8bb181533538519b3363a44caee0f2dd4d2202026ffa3c':
        raise ValueError('Scene comparison reference differs from the frozen baseline')
    data=json.loads(gzip.decompress(blob))
    if data['format']!='c643d-scene-vector-reference-v1':
        raise ValueError('Unsupported scene reference format')
    result={}
    for name,row in data['scenes'].items():
        ref=row['manifest']
        frames=[FrameBuild(**f) for f in row['frames']]
        if len(frames)!=ref['frames']:raise ValueError('Scene reference frame count mismatch')
        scene=SimpleNamespace(name=ref['name'],
            mesh=SimpleNamespace(**{k:[None]*ref[k] for k in ('vertices','edges','faces')}),
            source_fps=ref['source_fps'],sample_step=ref['sample_step'],
            frames=[SimpleNamespace(source_frame=f) for f in ref['source_frames']])
        result[name]=(frames,scene,ref)
    return result


def scene_worker(version):
    from c643d.cartscene import assemble_scene
    from profile_cart_stream import profile
    refs=load_scene_references(ROOT)
    marbles=refs['marbles'];horse=refs['horse-sunflower']
    out=BASE/'scenes';out.mkdir(exist_ok=True)
    for name,data,overlay in [('marbles-clean',marbles,False),('marbles-hud',marbles,True),('horse-sunflower',horse,False)]:
        fs,scene,ref=data;stem=f'{name}-v{version}';crt=out/(stem+'.crt');dst=REPORT/(stem+'-scene.json')
        if dst.exists():continue
        if not crt.exists():assemble_scene(ROOT,fs,scene,tass=TASS,cartconv=CARTCONV,outdir=out,stem=stem,hud_text=ref['hud_text'],frame_ticks=ref['frame_ticks'],colors=ref['colors'],color_index=ref['screen_color']>>4,intro=name.startswith('marbles'),ending=name.startswith('marbles'),text_overlay=overlay,renderer=f'yunroll-cart-v{version}-scene',prefer='fps')
        p=profile(crt,VICE,DATA);q=verify(crt,VICE,DATA)
        dst.write_text(json.dumps(dict(name=name,renderer=f'v{version}-scene',diagnostic_only=True,profile=p,verification=q),indent=2)+'\n')
        print(stem,'verified',flush=True)


def chart(a,provenance):
    results={};names=None;oracles={};checks=0
    for method,pref in METHODS:
        key=method+('-ram' if pref=='ram' else '')
        r=json.loads((a.workspace/'results'/(key+'-play-all.json')).read_text())
        assert r['mode']=='normal PLAY ALL ONLY' and not r['exhibition'] and r['seconds_setting']==10
        assert r['loops']==a.loops
        if method=='yunroll-cart-v9' and pref=='fps':names=[e['name'] for e in r['entries']]
        results[key]={e['name']:e for e in r['entries']}
        for i,e in enumerate(r['entries']):
            value=(e['frame_count'],e['oracle_sha256'])
            assert oracles.setdefault(e['name'],value)==value,'Different source pictures'
            p=json.loads((a.workspace/'results'/(key+f'-pixels-{i:02d}.json')).read_text())
            assert p['pixel_match'] and p['color_match'];checks+=p['verified_frames']
    def short(k):return k.replace('yunroll-cart-v10','hors-render-v1').replace('yunroll-cart-v','V').replace('yunroll-cart','cart scaffold')
    def winners(name,keys):
        valid=[k for k in keys if name in results[k]];best=max(results[k][name]['display_flips'] for k in valid)
        return [k for k in valid if results[k][name]['display_flips']==best]
    fpskeys=[m for m,p in METHODS if p=='fps']
    dataset=a.workspace/'menu-input.json'
    input_note=('All menu builds use one frozen custom/current-registry dataset, SHA-256 `'+hashlib.sha256(dataset.read_bytes()).hexdigest()+'`. Every method receives the same pictures, colours, HUD and sample order.' if dataset.exists() else 'All menu builds use the exact released V4 vector reference (`assets/v4-menu-vector-reference.json.gz`), including colours, HUD and animation sample order. Native method-specific lossless encoding is retained.')
    lines=['# Renderer performance comparison','',
        'Canonical lookup table for comparing methods and toolkit releases. **ONLY use normal PLAY ALL for comparative FPS. F5 is an exhibition mode and MUST NOT be used for benchmarking.**','',
        'Measured on PAL VICE 3.10, 985,248 cycles/s, default machine settings, sound disabled, seed 1; 64tass 1.59.3120. This is emulated C64 time, not host wall time or the HUD FPS counter. Physical C64 and NTSC are not measured.','',
        f'Each cell is actual display flips / elapsed emulated time across {a.loops} normal PLAY ALL visits. Every visit uses the unchanged 10-second setting. Observation starts on the first timer-count IRQ and ends at automatic-next: 499 PAL refresh intervals (about 9.955 s). The first visible picture is outside that window. Rates are rounded to two decimals; **bold** marks the highest displayed-frame count among FPS-preferred methods for that animation, including ties. Tiny timer-phase differences are not ranked as wins.','',
        '## Best method for each animation','',
        '| Animation | Source samples | Best method(s), FPS preference | Display FPS | V9 vs V8 displayed frames | HORS v2 vs v1 displayed frames |','| --- | ---: | --- | ---: | ---: | ---: |']
    for name in names:
        win=winners(name,fpskeys);old=results['yunroll-cart-v10'][name]['display_flips'];new=results['hors-render-v2'][name]['display_flips']
        legacy=(results['yunroll-cart-v9'][name]['display_flips']/results['yunroll-cart-v8'][name]['display_flips']-1)*100
        lines.append(f"| {name} | {oracles[name][0]} | {', '.join(short(k) for k in win)} | {results[win[0]][name]['display_fps']:.2f} | {legacy:+.2f}% | {(new/old-1)*100:+.2f}% |")
    lines+=showcase_section(Path(__file__).resolve().parents[1])
    sizes={}
    for key in results:
        raw=json.loads((a.workspace/'results'/(key+'-sizes.json')).read_text());sizes[key]={e['name']:e for e in raw['entries']}
    lines+=['','## Per-animation lookup','',
        'High/low are 985,248 divided by the shortest/longest **actual display-flip interval within a normal PLAY ALL window**, including VIC and IRQ stalls. Average is total displayed frames / measured time, not an arithmetic average of instantaneous FPS. Window edges are excluded from interval extrema. High FPS can include a brief queued-frame burst; it does not describe sustained throughput. Bold average marks the best frame-count result across FPS-preferred methods. RAM variants are listed separately. All values are FPS unless the header says bytes.','']
    for name in names:
        lines += [f'### {name}','', '| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        win=winners(name,fpskeys)
        for key in results:
            e=results[key].get(name)
            if e is None:
                lines.append(f'| {short(key)} | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |');continue
            z=sizes[key][name];avg=f"{e['display_fps']:.2f}"
            if key in win:avg='**'+avg+'**'
            lines.append(f"| {short(key)} | {e['high_fps']:.2f} | {avg} | {e['low_fps']:.2f} | {z['resident_frame_data_bytes']:,} | {z['rom_frame_bytes']:,} | {z['runtime_prg_bytes']:,} |")
        lines.append('')
    lines+=['','## Storage and fixed RAM allocations','',
        '| Method | Comparison CRT bytes | Entries | Runtime PRG size range, bytes | Fixed bitmap + screen storage | Stream staging + metadata caches |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    sizes={}
    for key in results:
        size=json.loads((a.workspace/'results'/(key+'-sizes.json')).read_text());sizes[key]={e['name']:e for e in size['entries']}
        lens=[e['runtime_prg_bytes'] for e in size['entries']]
        span=f'{min(lens):,}–{max(lens):,}' if lens else 'N/A (no demo fits)'
        lines.append(f"| {short(key)} | {size['crt_bytes']:,} | {len(lens)} | {span} | 27,000 B | {'0 B' if key in RESIDENT else '11,264 B'} |")
    lines+=['','Fixed graphics storage counts three 8,000-byte bitmaps and three 1,000-byte screen-colour matrices. Streamed methods also reserve 8,192 bytes staging and three 1,024-byte metadata caches. These are allocation components, **not total used or free RAM**: renderer code, LUTs, state, directories, menu/control storage and padding also occupy address space. RAM preference saves code but does not reclaim those fixed buffers. PRG length includes load address and gaps; it must not be added to these figures as if it were a disjoint allocation. The resident comparison CRT has fewer entries because HiFi does not fit, so its whole-cart size is not directly comparable to twelve-entry streamed carts.','',
        '| Animation | Resident frame tables (RAM bytes) | V2–V4 vectors (ROM bytes) | V5 | V6 | V7 | V8 | V9 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name in names:
        resident=sizes['step'].get(name);cells=[f"{resident['resident_frame_data_bytes']:,}" if resident else 'N/A']
        cells += [f"{sizes['yunroll-cart-v'+str(v)][name]['rom_frame_bytes']:,}" for v in (2,5,6,7,8,9)]
        lines.append('| '+name+' | '+' | '.join(cells)+' |')
    lines+=['','Resident table bytes count pointer, clear/colour and line records, excluding renderer code/LUTs. ROM bytes count unique encoded frame blocks, excluding menu/runtime/CHIP headers and unused bank space. These figures explain capacity tradeoffs; they do not pretend to be a free-RAM measurement.']
    lines+=['','¹ N/A means the complete dataset does not fit that preserved resident implementation. In the shipped dataset, 128 HiFi orientations exceed the 64-entry pointer arena, and HiFi sunflower also exceeds the 8-bit run-count limit. Exact per-method rejection reasons are in the external `*-unsupported.json` files. No frames, geometry or colours were removed to force a result. `yunroll-cart` is the initial resident scaffold, not V2 streaming.','',
        '## Authored scenes: separate paced diagnostics','',
        'These are **not PLAY ALL A/B FPS results** and must not be mixed into the menu tables or used to rank renderer throughput. The unchanged authored sequence runs with its original pacing and intro/ending behavior. Samples/s includes waits; mean active render cycles shows rendering cost. Clean/HUD Marbles and Horse & Sunflower use matching full source samples across V4–V10, frozen in `assets/comparison-scene-vector-reference.json.gz` from the original V4/V7 cartridges. No external history directory is required. For V10, the monitor acknowledges the indefinite SPACE build screen through its normal exit before running the authored intro; no cartridge bytes or measured renderer instructions are changed. Earlier generations do not provide the authored scene backend.','',
        '| Scene | Method | Samples/s (paced) | Mean render cycles | Worst render cycles | Over-budget samples |','| --- | --- | ---: | ---: | ---: | ---: |']
    for name in ('marbles-clean','marbles-hud','horse-sunflower'):
        for v in range(4,11):
            r=json.loads((a.workspace/'results'/f'{name}-v{v}-scene.json').read_text());p=r['profile'];q=r['verification'];assert q['pixel_match'] and q['color_match'];checks+=q['verified_frames']
            lines.append(f"| {name} | V{v}-scene | {p['frames_per_second']:.3f} | {p['mean_render_cycles']:,.0f} | {p['worst_render_cycles']:,} | {p.get('frames_exceeding_render_budget','—')} / {p['frames']} |")
    lines+=['','## Workload and interpretation','',
        '- '+input_note,
        '- hors-render-v2 uses gap 3 / batch budget 2048 in this canonical twelve-entry cart, retaining the v1 byte-span payload sizes to fit the same cartridge budget. Its independent pictures and guarded vector-page reuse are built in a private assembly tree. The seven-entry Demo Cart 2.0 uses separate measured encoding choices and is reported in its own section above.',
        '- The public matrix compares released renderer generations. The authored-scene diagnostic rows preserve the unchanged V4–V10 productions.',
        '- This table compares preserved renderer implementations under one **external comparison PLAY ALL wrapper**, not the exact historical release cartridges. The V9 normal PLAY ALL controller is used for every method. Its identical timer instructions live at `$0334` instead of `$c700`, because resident data occupies `$c700`; launch metadata is cached before loading and shared menu data restored between entries. Renderer code is unchanged apart from the existing cartridge IRQ-vector redirection. All these wrapper adaptations are generated outside the repo.',
        '- Resident and streamed methods have different memory/ROM costs. A faster resident method does not imply it can hold the larger HiFi datasets. Compare the same named animation and sample count.',
        '- A frame count tie is reported as a tie; a few extra samples over roughly 30 seconds are a small gain. Compare individual animations before quoting a suite total.',
        f'- Full bitmap and colour verification covered **{checks:,} completed pictures**. Raw traces, cartridge hashes, per-entry oracle hashes, unsupported-build reasons and individual results remain in the external workspace.',
        '- These measurements do not establish a universal performance floor or guarantee behavior for untested inputs.','',
        '## Reproduce and keep this chart current','',
        'Run from the repository root. The tool defaults to ignored `comparison-tests/`; an external `--workspace` is also supported. It creates an isolated source snapshot and never writes old test cartridges into `examples` or `build` in this checkout. Python, 64tass, cartconv and PAL VICE with its data files are required.','',
        '```bash','python tools/compare_renderers.py \\','  --workspace ../c64-renderer-comparison \\','  --tass 64tass --cartconv cartconv --vice x64sc \\','  --vice-data /usr/local/share/vice','',
        '# Only after the complete run succeeds:','cp ../c64-renderer-comparison/PERFORMANCE_COMPARISON.md docs/PERFORMANCE_COMPARISON.md','python tools/compare_renderers.py --check','```','',
        'Future demos: `--current-demos` compiles the current registry once and tests every resulting named entry across methods. Alternatively pass `--reference-json dataset.json.gz` in the `c643d-vector-reference-v1` format. Dataset files are saved outside tracked source and frozen for all methods. RAM-limited resident combinations are reported as N/A without dropping frames; bank capacity/build failures stop the comparison rather than silently simplify it. New renderer generations must be added to `METHODS` and the supported builders; chart rows themselves come from the data, not a twelve-row constant.','',
        'Optional pacing: `--max-fps 10` creates separate paced comparison carts after the uncapped pass. Integer rates 1–50 are supported; 10 FPS holds five PAL refreshes, while 12 FPS alternates four/five. `--lock-to-min-fps` measures two complete uncapped animation cycles, chooses a fixed per-demo refresh interval from the worst frame plus one refresh guard, then builds and verifies the paced copy. These options are mutually exclusive and **off by default** (`fps locking: not set`). A fixed cap cannot make an overloaded renderer meet a deadline; reports include observed hold intervals and missed deadlines. Pacing applies to these experimental menu reels, not the unchanged authored-scene timing or normal shipped cartridges. Paced/subset runs do not generate the release chart.','',
        'Use `--resume` only with the same source/tool fingerprint and options. Logs and JSON reports stay outside the repo. Archive that workspace with the release if long-term raw evidence is needed.','',
        '**Release gate:** run `--check` before publishing. If renderer code, builders, input assets, examples, version or this tester changes, rerun the complete uncapped matrix and replace this chart before tagging. Preserve old method rows; add new generations to the tester and regenerate. Never silently copy old numbers into a changed workload. Capped runs are separate experiments and must not replace this uncapped baseline.','',
        f"<!-- comparison-input-sha256: {provenance['input_sha256']} -->",f"<!-- comparison-source-version: {provenance['version']} -->",'']
    if provenance['reference_sha256']:lines.append('<!-- comparison-reference-sha256: '+provenance['reference_sha256']+' -->')
    if provenance['current_demos']:lines.append('<!-- comparison-current-demos: true -->')
    (a.workspace/'PERFORMANCE_COMPARISON.md').write_text('\n'.join(lines))


def main():
    global CARTCONV,MAX_FPS,LOCK_MIN
    repo=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,default=repo/'comparison-tests');p.add_argument('--resume',action='store_true')
    p.add_argument('--check',action='store_true',help='fail if the checked-in chart has stale input provenance')
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',type=Path)
    p.add_argument('--loops',type=int,default=3);p.add_argument('--workers',type=int,default=3)
    lock=p.add_mutually_exclusive_group()
    lock.add_argument('--max-fps',type=int,help='opt-in paced comparison reels, integer 1..50 FPS; default off')
    lock.add_argument('--lock-to-min-fps',action='store_true',help='full uncapped pass, then conservative per-demo fixed PAL cadence; default off')
    sources=p.add_mutually_exclusive_group()
    sources.add_argument('--reference-json',type=Path,help='external c643d-vector-reference-v1 JSON/gzip dataset')
    sources.add_argument('--current-demos',action='store_true',help='compile the current demo registry once, including newly added entries')
    p.add_argument('--methods',nargs='+',help='optional subset of method names; produces an experiment, not the release chart')
    p.add_argument('--_worker',help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.check:
        _,sha=fingerprints(repo);path=repo/'docs/PERFORMANCE_COMPARISON.md'
        if not path.exists() or f'comparison-input-sha256: {sha}' not in path.read_text():p.error('comparison chart missing or stale; --check only validates, it does not regenerate. Run the full comparison with --vice-data PATH in a fresh --workspace, then copy its PERFORMANCE_COMPARISON.md into docs/. See docs/PERFORMANCE_COMPARISON.md for commands.')
        reference=re.search(r'comparison-reference-sha256: ([0-9a-f]{64})',path.read_text())
        if reference and (not a.reference_json or hashlib.sha256(a.reference_json.read_bytes()).hexdigest()!=reference[1]):p.error('custom chart requires the matching --reference-json file for verification')
        print('Comparison chart matches current source inputs.');return
    if not a.vice_data:p.error('--vice-data is required')
    a.workspace=a.workspace.resolve();a.vice_data=a.vice_data.resolve()
    safe_local=repo/'comparison-tests'
    if a.workspace==repo or repo.is_relative_to(a.workspace) or (a.workspace.is_relative_to(repo) and not a.workspace.is_relative_to(safe_local)):
        p.error('workspace must be external or inside the ignored comparison-tests directory')
    if a.workspace.is_relative_to(safe_local) and '/comparison-tests/' not in (repo/'.gitignore').read_text().splitlines():
        p.error('comparison-tests must be explicitly ignored before use')
    if not 1<=a.workers<=4 or not 1<=a.loops<=20:p.error('workers must be 1..4; loops 1..20')
    for key in ('tass','cartconv','vice'):
        value=shutil.which(getattr(a,key))
        if not value:p.error(f'{key} executable not found')
        setattr(a,key,str(Path(value).resolve()))
    CARTCONV=a.cartconv;MAX_FPS=a.max_fps;LOCK_MIN=a.lock_to_min_fps
    if MAX_FPS is not None and not 1<=MAX_FPS<=50:p.error("--max-fps must be an integer in 1..50")
    print("fps locking: "+(f"maximum {MAX_FPS} FPS" if MAX_FPS else "measured minimum (two passes)" if LOCK_MIN else "not set"),flush=True)
    if a._worker:
        configure(a)
        kind,*parts=a._worker.split(':')
        if kind=='menu':menu_worker(*parts,a.loops)
        else:scene_worker(int(parts[0]))
        return
    files,sha=fingerprints(repo)
    if a.reference_json:a.reference_json=a.reference_json.resolve()
    provenance=dict(current_demos=a.current_demos,reference_sha256=hashlib.sha256(a.reference_json.read_bytes()).hexdigest() if a.reference_json else None,max_fps=MAX_FPS,lock_to_min_fps=LOCK_MIN,methods=a.methods,input_sha256=sha,inputs=files,version=(repo/'VERSION').read_text().strip(),loops=a.loops,
                    tool_sha256={k:hashlib.sha256(Path(getattr(a,k)).read_bytes()).hexdigest() for k in ('tass','cartconv','vice')},vice_data=str(a.vice_data))
    stamp=a.workspace/'provenance.json'
    if a.resume:
        if not stamp.exists() or json.loads(stamp.read_text())!=provenance:p.error('resume fingerprint/options differ; use a new workspace')
    else:
        if a.workspace.exists() and any(a.workspace.iterdir()):p.error('workspace must be empty (or use --resume)')
        a.workspace.mkdir(parents=True,exist_ok=True)
        shutil.copytree(repo,a.workspace/'source',ignore=shutil.ignore_patterns('.git','build','comparison-tests','logs','__pycache__'))
        adapt_snapshot(a.workspace/'source')
        if a.reference_json:
            import gzip
            blob=a.reference_json.read_bytes();blob=gzip.decompress(blob) if blob[:2]==b'\x1f\x8b' else blob
            data=json.loads(blob)
            if data.get('format')!='c643d-vector-reference-v1':p.error('unsupported vector reference format')
            (a.workspace/'menu-input.json').write_text(json.dumps(data))
        elif a.current_demos:
            configure(a)
            rows=[]
            for demo in cartuniform.demos(ROOT):
                row=asdict(demo);row['hud']=demo.hud.hex();rows.append(row)
            (a.workspace/'menu-input.json').write_text(json.dumps(dict(format='c643d-vector-reference-v1',demos=rows)))
        stamp.write_text(json.dumps(provenance,indent=2)+'\n')
    jobs=['menu:'+m+':'+pref for m,pref in METHODS]+['scene:'+str(v) for v in range(4,11)]
    if a.methods:jobs=[j for j in jobs if j.startswith('menu:') and j.split(':')[1] in a.methods]
    if MAX_FPS or LOCK_MIN:jobs=[j for j in jobs if j.startswith('menu:')]
    if not jobs:p.error('no matching methods')
    def run(job):
        cmd=[sys.executable,str(Path(__file__).resolve()),'--workspace',str(a.workspace),'--tass',a.tass,'--cartconv',a.cartconv,'--vice',a.vice,'--vice-data',str(a.vice_data),'--loops',str(a.loops),'--_worker',job]
        if MAX_FPS:cmd+=['--max-fps',str(MAX_FPS)]
        if LOCK_MIN:cmd+=['--lock-to-min-fps']
        with (a.workspace/(job.replace(':','-')+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        print(job,'PASS' if r.returncode==0 else 'FAIL (see external log)',flush=True)
        return r.returncode
    with ThreadPoolExecutor(max_workers=a.workers) as pool:status=list(pool.map(run,jobs))
    if any(status):raise SystemExit('Incomplete comparison; no chart produced. Fix failing job and use --resume.')
    assert fingerprints(repo)[0]==files,'Repository inputs changed during comparison'
    if MAX_FPS or LOCK_MIN or a.methods:
        print('Experiment complete; raw and paced results remain in',a.workspace/'results');return
    chart(a,provenance)
    print(a.workspace/'PERFORMANCE_COMPARISON.md')

if __name__=='__main__':main()
