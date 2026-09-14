#!/usr/bin/env python3
"""Generate the v3.0 versus v3.1 interactive collection A/B tables."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/benchmarks/release-0.8.1'
TARGET=ROOT/'docs/INTERACTIVE_BASELINE_PERFORMANCE.md'


def report():
    old=json.loads((EVIDENCE/'baseline/results.json').read_text())
    new=json.loads((EVIDENCE/'collection/results.json').read_text())
    folder=ROOT/'examples/gmod3_cart_demos'
    for result in (old,new):
        assert hashlib.sha256((folder/result['cartridge']).read_bytes()).hexdigest()==result['crt_sha256']
        assert len(result['entries'])==58
        assert all(e['passed'] and e['all_three_buffers'] and e['stars_off'] for e in result['entries'])
    assert old['clock_hz']==new['clock_hz']==985248
    assert old['pal_cycles']==new['pal_cycles']==19656
    paired=[]
    for a,b in zip(old['entries'],new['entries']):
        for key in ('index','name','frames','stored_frames','picture_sha256','bank_range','target_fps','observed_refreshes'):
            assert a[key]==b[key],(key,a['index'])
        delta=b['average_fps']-a['average_fps']
        paired.append(dict(index=a['index'],name=a['name'],old=a,new=b,difference_fps=delta,
            difference_percent=100*delta/a['average_fps'],render_cycles_percent=100*(b['mean_render_cycles']/a['mean_render_cycles']-1)))
    summary=dict(entries=58,baseline_sha256=old['crt_sha256'],patched_sha256=new['crt_sha256'],
        higher=sum(e['difference_fps']>0 for e in paired),ties=sum(e['difference_fps']==0 for e in paired),
        lower=sum(e['difference_fps']<0 for e in paired),
        largest_drop_fps=min(e['difference_fps'] for e in paired),
        largest_drop_percent=min(e['difference_percent'] for e in paired),
        median_change_percent=statistics.median(e['difference_percent'] for e in paired),
        largest_render_cycle_increase_percent=max(e['render_cycles_percent'] for e in paired))
    lines=['# Demo Cart v3.1 interactive performance: A/B against v3.0','',
        'Toolkit v0.8.1 versus the actual shipped v0.8.0 interactive cartridge. Both were rerun in PAL VICE 3.10 with the same seed, machine settings, scene data, native frame order, default speed, visible HUD and disabled stars/exhibition. This isolates the interactive hotfix from the older EasyFlash/GMod3 backend comparison.','',
        f"Across 58 entries: {summary['higher']} higher averages, {summary['ties']} ties and {summary['lower']} lower averages. The largest decrease is {abs(summary['largest_drop_fps']):.4f} FPS; the largest relative decrease is {abs(summary['largest_drop_percent']):.3f}%. Median change: {summary['median_change_percent']:+.3f}%. Maximum increase in mean active rendering cycles: {summary['largest_render_cycle_increase_percent']:.3f}%.",'',
        'The hotfix has a small measurable cost. RUN/STOP now has priority over held speed keys and is also latched during the raster IRQ; that extra input work accounts for the increase. Help contents, menu navigation and HUD switching run on demand. Picture encoding and drawing addresses are preserved. This is a control-correctness patch, with no claim of a speedup or zero regression.','',
        'Each entry verifies two complete picture loops plus warm-up across all three buffers, then counts actual displayed-slot transitions over 2,400 PAL refreshes (47.881 seconds). Startup and help time are excluded. High/low FPS are reciprocals of the shortest/longest display hold; only the highest average in each pair is bold, including exact ties. Quantisation is about 0.0209 FPS per displayed frame in this observation window.','',
        'The benchmark cartridge is byte-identical to v0.8.0; it has no added runtime polling. SAKU uses its default gradient presentation here; alternate presentations and both star profiles have separate correctness checks. These measurements cover default interactive playback, not every combination of enabled effects. Physical C64 and NTSC were not tested.','',
        '[Old raw observations](benchmarks/release-0.8.1/baseline/results.json) · [Patched raw observations](benchmarks/release-0.8.1/collection/results.json) · [Keyboard verification](benchmarks/release-0.8.1/keyboard/results.json)','',
        'Reproduce with `tools/verify_gmod3_collection.py` on each CRT, using `--output docs/benchmarks/release-0.8.1/baseline` or `collection`, then run `python tools/report_interactive_baseline.py`. Supply `--vice` and `--vice-data` for your VICE installation.','']
    for e in paired:
        a,b=e['old'],e['new'];winner=max(a['average_fps'],b['average_fps'])
        lines += [f"## {a['index']+1:02d}. {a['name']} ({a['stored_frames']} stored pictures)",'',
            '| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |',
            '| --- | ---: | ---: | ---: | ---: |']
        for label,row in [('v3.0 / hors-v4-gmod3',a),('v3.1 / hors-v4-gmod3',b)]:
            avg=f"{row['average_fps']:.4f}"
            if row['average_fps']==winner:avg='**'+avg+'**'
            lines.append(f"| {label} | {row['high_fps']:.4f} | {avg} | {row['low_fps']:.4f} | {row['mean_render_cycles']:.1f} |")
        lines += ['',f"Change: {e['difference_fps']:+.4f} FPS ({e['difference_percent']:+.3f}%).",'']
    return '\n'.join(lines),summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    text,summary=report()
    if a.check:
        assert TARGET.read_text()==text,'Interactive performance report is stale'
    else:
        TARGET.write_text(text)
        (EVIDENCE/'ab-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
