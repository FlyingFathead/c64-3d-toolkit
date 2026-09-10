"""PAL display measurement and ranking for the opt-in scene autotuner."""
from pathlib import Path
import collections, hashlib, json, re, statistics, subprocess, tempfile
from .pipeline import FrameBuild
from .optimize import picture_bytes

CLOCK=985248
PAL_TICKS=19656


def measure_display(crt, oracle, vice, vice_data, refreshes=501):
    from verify_cart_stream import labels
    crt=Path(crt);manifest=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    if manifest.get('intro') or manifest.get('ending'):
        raise ValueError('Autotune display measurement requires a looping scene without presentation overlays')
    sym=labels(crt.with_suffix('.lbl'))
    expected={};wanted=set()
    for f in json.loads(Path(oracle).read_text()):
        pic=picture_bytes(FrameBuild(**f),manifest['screen_color']);bm,sc=pic[:7680],pic[7680:]
        visible=tuple(i for i in range(960) if any(bm[i*8:i*8+8]))
        signature=hashlib.sha256(bm+bytes(sc[i] for i in visible)).hexdigest()
        expected.setdefault(hashlib.sha256(bm).digest(),[]).append((signature,visible,sc));wanted.add(signature)
    identity=hashlib.sha256(crt.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='c643d-display-') as td:
        td=Path(td);warm=manifest['frames']+6
        cmd=['delete',f'break ${sym["profile_published"]:04x}']+['g']*warm+['delete',f'break ${sym["irq_no_flip"]:04x}']
        for i in range(refreshes+1):
            cmd+=['g','stopwatch','bank ram',f'bsave "{td/f"{i}.ram"}" 0 $0000 $ffff','bank cpu',f'bsave "{td/f"{i}.io"}" 0 $d000 $dd03']
        cmd+=['quit'];(td/'run.mon').write_text('\n'.join(cmd)+'\n')
        argv=[str(vice),'-console','+easyflashcrtwrite','-pal','+sound','-warp','-seed','1','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(td/'run.mon'),'-monlog','-monlogname',str(td/'monitor.log'),'-limitcycles',str(warm*1000000+(refreshes+1)*PAL_TICKS+20000000)]
        if vice_data:argv+=['-directory',str(vice_data)]
        with (td/'vice.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=log,check=True,timeout=240)
        ticks=[int(v) for v in re.findall(r'Stopwatch:\s*(\d+)',(td/'monitor.log').read_text())]
        if len(ticks)!=refreshes+1:raise RuntimeError('VICE did not reach every display observation')
        seen=set();switches=[];previous=None;changes=0;switch_rasters=[]
        for i in range(refreshes+1):
            ram=(td/f'{i}.ram').read_bytes();io=(td/f'{i}.io').read_bytes()
            ds=ram[sym['display_slot']];assert ds in (0,1,2)
            bmaddr=[0x2000,0x6000,0xe000][ds];scaddr=[0x400,0x4400,0xc800][ds]
            bm=ram[bmaddr:bmaddr+7680];choices=expected.get(hashlib.sha256(bm).digest(),[])
            matches=[sig for sig,visible,sc in choices if all(ram[scaddr+j]==sc[j] for j in visible)]
            if not matches:raise AssertionError(f'Displayed bitmap/colours disagree with oracle at refresh {i}')
            assert io[0xd00]&3==[3,2,0][ds] and io[0x18]&0xfe==[0x18,0x18,0x28][ds]
            seen.update(matches)
            if i and ds!=previous:
                changes+=1;switches.append((i,ticks[i]));switch_rasters.append(io[0x12]+((io[0x11]&128)<<1))
            previous=ds
    intervals=[b[1]-a[1] for a,b in zip(switches,switches[1:])]
    holds=collections.Counter(b[0]-a[0] for a,b in zip(switches,switches[1:]))
    assert hashlib.sha256(crt.read_bytes()).hexdigest()==identity
    return {'passed':True,'sha256':identity,'clock_hz':CLOCK,'refresh_observations':refreshes+1,
        'display_changes':changes,'elapsed_cycles':ticks[-1]-ticks[0],
        'display_fps':changes*CLOCK/(ticks[-1]-ticks[0]),
        'display_interval_mean_ms':statistics.mean(intervals)/985.248 if intervals else None,
        'display_interval_worst_ms':max(intervals)/985.248 if intervals else None,
        'display_interval_p95_ms':sorted(intervals)[int(.95*(len(intervals)-1))]/985.248 if intervals else None,
        'observed_hold_ticks':dict(holds),'requested_ticks':manifest['frame_ticks'],
        'fixed_cadence':bool(holds) and set(holds)=={manifest['frame_ticks']},
        'unique_visible_pictures_expected':len(wanted),'unique_visible_pictures_observed':len(seen),
        'picture_coverage_complete':wanted.issubset(seen),
        'display_switch_raster_lines':dict(collections.Counter(switch_rasters)),
        'measurement':'PAL VICE; seed 1; sound disabled; actual display-slot changes sampled at each raster IRQ after VIC register programming. Window edges count flips/time; interval extrema exclude edges.',
        'limits':'Standalone looping scene only. Does not validate production overlays, NTSC or physical hardware; no claim that changing minimum holds preserves authored duration.'}


def select(rows, objective='fps'):
    eligible=[r for r in rows if r.get('status')=='passed' and r.get('picture_coverage_complete')]
    if objective=='steady':eligible=[r for r in eligible if r.get('fixed_cadence')]
    if not eligible:return {'winner':None,'reason':'No measured candidate meets the requested constraints'}
    fastest=max(r['display_fps'] for r in eligible)
    # One display update per observation window: finer differences are not wins.
    tolerance=max(CLOCK/r['elapsed_cycles'] for r in eligible)
    tied=[r for r in eligible if fastest-r['display_fps']<=tolerance]
    def key(row):
        prep=row.get('prep_mean_ms')
        return (-row['ticks'],float('inf') if prep is None else prep,row['ROM_payload_bytes'])
    tied.sort(key=key)
    return {'winner':tied[0]['candidate'],'objective':objective,'tie_tolerance_fps':tolerance,
            'throughput_ties':[r['candidate'] for r in tied],
            'smallest_ROM_candidate':min(eligible,key=lambda r:r['ROM_payload_bytes'])['candidate'],
            'slowest_measured_candidate':min(eligible,key=lambda r:r['display_fps'])['candidate'],
            'tie_rule':'Prefer a longer minimum hold, then less measured preparation work, then smaller payload',
            'automatically_promoted':False}
