#!/usr/bin/env python3
"""Generate and independently check the GMod3 tables in PERFORMANCE_COMPARISON."""
import argparse
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import re
from performance_tables import highlight_fps

ROOT=Path(__file__).resolve().parents[1]
BEGIN='<!-- BEGIN HORS-V4 GMOD3 -->'
END='<!-- END HORS-V4 GMOD3 -->'


def workload_label(row):
    # Distinct released inputs can share a title and sample count. Never merge
    # their rankings (e.g. mono and colour Falling Cubes).
    variant={0:'mono',1:'colour',22:'HiFi reel',23:'authored scene',54:'mono',55:'colour'}.get(row['source_id'])
    name=row['name']+(f' ({variant})' if variant else '')
    return f'{name} / {row["frames"]}'+(' / indexed4' if row.get('color_encoding')=='indexed4' else '')


def section(root=ROOT):
    path=root/'docs/benchmarks/hors-v4-matched/results.json'
    data=json.loads(path.read_text());rows=data['entries']
    assert len(rows)==69 and {r['case'] for r in rows}==set(range(69))
    assert len({workload_label(r) for r in rows})==len(rows),'Distinct workloads need distinct labels'
    assert all(r['encoded_payloads_identical'] and r['gmod3']['passed'] and r['easyflash']['passed'] for r in rows)
    wins=sum(r['difference_fps']>0 for r in rows);ties=sum(r['difference_fps']==0 for r in rows)
    deltas=[r['difference_fps'] for r in rows]
    lines=[BEGIN,'## HORS-V4 / GMod3: v0.8.0 matched comparison','',
        '`hors-v4-gmod3` identifies HORS-V4 using its default GMod3 backend. '
        'The baseline is `hors-v3` on EasyFlash. Both receive identical pictures, colours, '
        'sample order, encoding policy and HUD settings. These are automatic standalone tests: '
        'no input polling, stars, exhibition or authored frame-rate cap.','',
        f'Across {len(rows)} matched workloads: **{wins} GMod3 wins, {ties} ties, {len(rows)-wins-ties} lower averages**. '
        f'The observed change ranges from {min(deltas):+.3f} to {max(deltas):+.3f} FPS. '
        'This supports modest throughput gains and the larger collection capacity; it does not support a universal +1 FPS claim.','',
        'Each test verifies two complete picture loops plus warm-up in all three buffers, then counts '
        f'actual displayed-slot transitions for {data["observation_refreshes"]:,} PAL refreshes '
        f'({data["observation_refreshes"]*19656/985248:.3f} seconds). '
        'High/low FPS are reciprocals of the shortest/longest observed display hold; they are listed '
        'as diagnostics. Only the highest average in each matched pair is bold. Ties are explicit.','',
        'The 640-picture Marbles sequence is compared as five matching 128-picture segments, with '
        'no dropped pictures; uninterrupted five-page playback is checked separately in the collection. '
        'The 192-picture metallic Pretzel uses its released `indexed4` colour policy on both backends '
        'to fit the preserved EasyFlash ROML allocator. All other pairs use literal colour bytes. '
        'These settings are recorded per case in the raw report.','',
        '[Raw matched results](benchmarks/hors-v4-matched/results.json) · '
        '[Actual interactive collection results](benchmarks/gmod3-collection/interactive/results.json) · '
        '[Bank/copy diagnostics](benchmarks/gmod3-checkpoint1/results.json)','']
    groups=OrderedDict()
    for r in rows:
        name=r['name']
        group=('SAKU presentations' if name.startswith('SAKU') else 'Stanford Dragon' if name.startswith('DRAGON') else
            "Sande's Pretzel" if name.startswith('PRETZEL') else "Sande's TAC-2 joystick" if name.startswith('TAC-2') else
            'Marbles: all five segments' if 'MARBLES' in name else 'Demo Cart 2.0' if 29<=r['case']<=35 else
            'Blender scenes' if 'BLENDER' in name or 'HORSE AND SUNFLOWER' in name else 'Original demos and HiFi variants')
        groups.setdefault(group,[]).append(r)
    for group,items in groups.items():
        lines += ['### '+group,'', '| Scene / samples | Method | High FPS | Average FPS | Low FPS |',
            '| --- | --- | ---: | ---: | ---: |']
        for r in items:
            label=workload_label(r)
            for backend,method in [('easyflash','hors-v3'),('gmod3','hors-v4-gmod3')]:
                m=r[backend]
                # Quantization can make tiny measured differences a displayed tie.
                lines.append(f'| {label} | {method} | {m["high_fps"]:.3f} | {m["average_fps"]:.3f} | {m["low_fps"]:.3f} |')
        lines.append('')
    actual=json.loads((root/'docs/benchmarks/gmod3-collection/interactive/results.json').read_text())
    lines+=['### Actual All-in-One interactive defaults','',
        'Historical v0.8.0 / Demo Cart v3.0 measurements. For the v0.8.1 / v3.1 interactive hotfix, see [the fresh A/B tables](INTERACTIVE_BASELINE_PERFORMANCE.md).','',
        'These figures include the collection navigation, the complete interactive runtime, HUD and '
        'disabled-but-available starfield. Authored pacing remains enabled where supplied. '
        'They are not mixed into the automatic A/B ranking above. Each entry is individually checked '
        'with the final cartridge hash; SAKU starts in gradient-spin mode with stars off.','',
        '| Entry | Scene / stored samples | High FPS | Average FPS | Low FPS | Allocated KiB |',
        '| ---: | --- | ---: | ---: | ---: | ---: |']
    for r in actual['entries']:
        lines.append(f'| {r["index"]+1} | {r["name"]} / {r["stored_frames"]} | {r["high_fps"]:.3f} | {r["average_fps"]:.3f} | {r["low_fps"]:.3f} | {r["allocated_kib"]} |')
    lines += ['', 'There is one method in this inventory table, so no cross-scene “winner” is highlighted. '
        'Different scenes contain different work. The interactive cart uses 13,448 KiB and leaves '
        '2,936 KiB free; its automatic companion uses 13,416 KiB and leaves 2,968 KiB.','',
        '### Reproduce these results','', '```sh',
        '# These historical interactive measurements use the preserved v3.0 CRT.',
        'python tools/compare_gmod3_catalog.py --tass 64tass --cartconv cartconv --vice x64sc --vice-data /path/to/vice/data',
        'python tools/verify_gmod3_collection.py examples/gmod3_cart_demos/demo-cart-v3.0-gmod3-all-in-one.crt --vice x64sc --vice-data /path/to/vice/data --output docs/benchmarks/gmod3-collection/interactive',
        'python tools/report_gmod3_performance.py', 'python tools/report_gmod3_performance.py --check','```','',
        'Historical matrices elsewhere on this page retain their original protocols and measured cartridge versions. '
        'Their figures are not relabelled as new HORS-V4 measurements.',
        '<!-- hors-v4-results-sha256: '+hashlib.sha256(path.read_bytes()).hexdigest()+' -->',END,'']
    # Group by the first scene column, including sample count/encoding.
    cooked=highlight_fps([l.replace('| Scene / samples |','| Scene |') for l in lines])
    # Single-method inventory: remove numeric emphasis; unlike a method matrix,
    # comparing unrelated scenes would select a meaningless suite "winner".
    active=False
    for i,line in enumerate(cooked):
        if line.startswith('| Entry |'):active=True
        if active and line.startswith('|'):cooked[i]=line.replace('**','').replace(' (tie)','')
        elif active and not line.startswith('|'):active=False
    return cooked


def check_winners(text):
    """Independent audit: high/low unbolded; averages equal each workload max."""
    lines=text.splitlines();tables=0;checked=0
    for i,line in enumerate(lines):
        if not line.startswith('|') or i+1>=len(lines) or not re.fullmatch(r'[| :\-]+',lines[i+1]):continue
        headers=[x.strip() for x in line.strip('|').split('|')];rows=[]
        for row in lines[i+2:]:
            if not row.startswith('|'):break
            rows.append([x.strip() for x in row.strip('|').split('|')])
        for j,h in enumerate(headers):
            if any(w in h.lower().split() for w in ('low','high','peak','minimum','maximum','min','max')):
                assert all('**' not in row[j] for row in rows),('highlighted extremum',h)
        averages=[j for j,h in enumerate(headers) if h.lower() in ('average fps','average')]
        if len(averages)!=1 or not rows or headers[0]=='Entry':continue
        j=averages[0];workload=headers[0].lower() in ('scene','model','animation')
        groups={}
        for row in rows:
            try:value=float(row[j].replace('**','').replace(' (tie)','').replace(',',''))
            except ValueError:continue
            groups.setdefault(row[0] if workload else '',[]).append((value,'**' in row[j]))
        for group in groups.values():
            best=max(v for v,b in group)
            assert all(b==(v==best) for v,b in group),('wrong average winner',headers,group)
            checked+=len(group)
        tables+=1
    matched=text.split(BEGIN,1)[1].split('### Actual All-in-One interactive defaults',1)[0]
    pairs={}
    for line in matched.splitlines():
        if not line.startswith('|'):continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)==5 and cells[1] in ('hors-v3','hors-v4-gmod3'):
            pairs.setdefault(cells[0],[]).append(cells[1])
    assert len(pairs)==69 and all(sorted(v)==['hors-v3','hors-v4-gmod3'] for v in pairs.values()),'Merged or missing matched workloads'
    return dict(tables_with_average=tables,average_cells_checked=checked,high_low_unbolded=True,distinct_matched_pairs=len(pairs))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    path=ROOT/'docs/PERFORMANCE_COMPARISON.md';old=path.read_text();new='\n'.join(section())
    if BEGIN in old:prefix,tail=old.split(BEGIN,1);suffix=tail.split(END,1)[1].lstrip('\n')
    else:
        at=old.index('## Best method for each animation');prefix=old[:at];suffix=old[at:]
    wanted=prefix+new+'\n'+suffix
    # Normalize historical tables separately; keep the actual single-method
    # collection inventory outside the cross-method winner formatter.
    before,tail=wanted.split(BEGIN,1);middle,after=tail.split(END,1)
    wanted='\n'.join(highlight_fps(before.splitlines()))+'\n'+BEGIN+middle+END+'\n'+'\n'.join(highlight_fps(after.splitlines()))+'\n'
    for old_name,short_name in [('hors-renderer-v3','hors-v3'),('hors-render-v2','hors-v2'),('hors-render-v1','hors-v1')]:
        wanted=wanted.replace(old_name,short_name)
    audit=check_winners(wanted)
    if a.check:
        assert old==wanted,'Performance page is stale; regenerate with this tool'
        print('PASS generated tables and independent winner audit:',audit)
    else:path.write_text(wanted);print('Updated',path,audit)

if __name__=='__main__':main()
