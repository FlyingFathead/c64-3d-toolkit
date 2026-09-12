#!/usr/bin/env python3
"""Record a fresh, complete HORS-V3 measurement run and render its report section."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/benchmarks/hors-v3-preview/summary.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(root=ROOT):
    record = json.loads((root / RECORD).read_text())
    for name, expected in record['sha256'].items():
        if sha(root / name) != expected:
            raise ValueError('HORS-V3 evidence is stale: ' + name)
    for row in record['results']:
        assert row['pixel_match'] and row['color_match'] and row['picture_coverage_complete']
        assert row['sha256'] == sha(root / 'examples/hors_v3_preview/cartridges' / (row['stem'] + '.crt'))
        if row['interactive']:
            bg = row['background_controls']
            assert bg['passed'] and bg['sha256'] == row['sha256']
            assert bg['keys']['passed'] and bg['palette']['passed']
            assert all(v['color_match'] and v['border_background_match'] for v in bg['measurements'].values())
    return record

def tables(record):
    rows = record['results']
    table = ['| Workload | Orientations | Displayed FPS | Frame stream bytes | CRT bytes |',
             '| --- | ---: | ---: | ---: | ---: |']
    for r in rows:
        table.append(f"| {r['label']} | {r['frames']} | {r['display_fps']:.2f} | {r['rom_frame_bytes']:,} | {r['crt_bytes']:,} |")
    interactive = [r for r in rows if r['interactive']]
    values = [[r['display_fps']] + [r['background_controls']['measurements'][k]['display_fps']
              for k in ('steady','auto-50','auto-1')] for r in interactive]
    labels = ['Black, cycling off','Blue, cycling off','Automatic, 50 ticks','Automatic, 1 tick']
    bg = ['| Background mode | Direct FPS | Compact FPS |', '| --- | ---: | ---: |']
    bg += [f'| {label} | {values[0][i]:.2f} | {values[1][i]:.2f} |' for i,label in enumerate(labels)]
    return table, bg

def comparison_section(root=ROOT):
    record = check(root)
    table, bg = tables(record)
    return ['', '## HORS-V3 surfaces and textures', '',
        'Sande’s complete Pretzel mesh, PAL VICE 3.10, 1,504-refresh windows. FPS counts actual display-buffer flips. These standalone workloads are separate from normal PLAY ALL. The V2 metallic row replays identical filled pictures through the unchanged V2 kernel as a comparison harness; V2 does not gain a surface-fill CLI.', '',
        *table, '', '![HORS-V3 FPS and ROM comparison](benchmarks/hors-v3-preview/performance.png)', '',
        'Direct colour bytes remain the speed default. Compact dictionary encoding is optional: smaller streams, additional decoding cost. [Method, limitations and raw evidence](HORS_RENDER_V3_RESULTS.md).', '',
        '### Background controls and performance', '', *bg, '',
        '![Background-control performance](benchmarks/hors-v3-preview/background-performance.png)', '',
        'Interactive controls replace originally black pixels only; other metallic shades are preserved. Default cycling requests 50 PAL ticks between changes; the fastest setting requests one tick but performs at most one change per produced picture. The displayed border follows its buffer’s background unless locked or independently selected.', '']

def charts(record, target):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = [r for r in record['results'] if r['id'] not in ('v3-wire','compact-192')]
    fig, axes = plt.subplots(1,2,figsize=(13.5,6.8))
    for ax,key,title,scale,unit in [(axes[0],'display_fps','Displayed FPS · higher is faster',1,''),
                                 (axes[1],'rom_frame_bytes','Frame stream · smaller uses less ROM',1024,' KiB')]:
        vals=[r[key]/scale for r in rows]
        ax.barh(range(len(rows)),vals,color='#377c62',height=.67)
        ax.invert_yaxis(); ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r['label'] for r in rows] if ax is axes[0] else [])
        ax.set_xlim(0,max(vals)*1.22);ax.set_title(title,loc='left',fontsize=11,pad=14)
        for i,val in enumerate(vals):ax.text(val+max(vals)*.015,i,f'{val:.2f}{unit}',va='center',fontsize=9)
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
        ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    fig.suptitle('HORS-V3 · Sande’s Pretzel',x=.025,ha='left',fontsize=16,fontweight='bold')
    fig.text(.025,.015,'128 orientations · 3,104 triangles · PAL VICE 3.10 · actual display-buffer flips\nV2 metallic replays the same filled pictures in a test harness; its CLI is unchanged.',fontsize=9)
    fig.tight_layout(rect=[0,.07,1,.93])
    for ext in ('png','svg'):fig.savefig(target/('performance.'+ext),dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8))
    for j,r in enumerate(r for r in record['results'] if r['interactive']):
        vals=[r['display_fps']]+[r['background_controls']['measurements'][k]['display_fps'] for k in ('steady','auto-50','auto-1')]
        ys=[i+(j-.5)*.34 for i in range(4)]
        ax.barh(ys,vals,height=.30,label=['Direct colours','Compact dictionary'][j],color=['#377c62','#8c6dad'][j])
        for y,v in zip(ys,vals):ax.text(v+.12,y,f'{v:.2f}',va='center',fontsize=10)
    ax.set_yticks(range(4),['Black, cycling off','Blue, cycling off','Automatic, 50 ticks','Automatic, 1 tick'])
    ax.invert_yaxis();ax.set_xlim(0,16);ax.set_xlabel('Displayed FPS')
    ax.set_title('HORS-V3 metallic interactive: background-control cost',loc='left')
    ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncol=2,frameon=False);fig.tight_layout()
    for ext in ('png','svg'):fig.savefig(target/('background-performance.'+ext),dpi=170)
    plt.close(fig)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path)
    a=p.parse_args();source=a.results.resolve();target=ROOT/'docs/benchmarks/hors-v3-preview'
    record=json.loads((ROOT/RECORD).read_text())
    for row in record['results']:
        stem=row['stem'];cart=ROOT/'examples/hors_v3_preview/cartridges'/(stem+'.crt')
        display=json.loads((source/(stem+'-display.json')).read_text())
        proof=json.loads((source/(stem+'-verification.json')).read_text())
        meta=json.loads(cart.with_name(stem+'-manifest.json').read_text())
        assert display['sha256']==sha(cart)
        assert display['pixel_match'] and display['color_match'] and proof['pixel_match'] and proof['color_match']
        assert display['picture_coverage_complete']
        row.update(display_fps=display['display_fps'],sha256=display['sha256'],crt_bytes=cart.stat().st_size,
            rom_frame_bytes=meta['rom_frame_bytes'],highest_bank=meta['highest_bank'],
            verified_pictures=proof['verified_frames'],evidence_reuse=None)
        oracle=cart.with_name(stem+'-oracle.json')
        if oracle.exists():shutil.copy2(oracle,ROOT/row['oracle'])
        row['oracle_sha256']=sha(ROOT/row['oracle'])
        for suffix in ('-display.json','-verification.json','-controls.json','-background.json'):
            f=source/(stem+suffix)
            if f.exists():shutil.copy2(f,target/'results'/f.name)
        if row['interactive']:
            controls=json.loads((source/(stem+'-controls.json')).read_text())
            assert controls['passed']
            background=json.loads((source/(stem+'-background.json')).read_text())
            assert background['passed'] and background['sha256']==row['sha256']
            row['background_controls']=background
    record.update(experimental=False,target='HORS-V3 in '+(ROOT/'VERSION').read_text().strip(),
                  version=(ROOT/'VERSION').read_text().strip(),evidence_origin='Fresh complete PAL VICE run on the release cartridges')
    record['tests'].pop('complete_release_suite_rerun', None)
    record['tests']['release_suite_report']='docs/benchmarks/release-0.7.7/validation.json'
    charts(record,target)
    table,bg=tables(record)
    doc=ROOT/'docs/HORS_RENDER_V3_RESULTS.md';text=doc.read_text()
    text=re.sub(r'\| Workload \|[^\n]*\n(?:\|[^\n]*\n)+','\n'.join(table)+'\n',text,count=1)
    text=re.sub(r'\| Background mode \|[^\n]*\n(?:\|[^\n]*\n)+','\n'.join(bg)+'\n',text,count=1)
    doc.write_text(text)
    relevant=set(record['sha256'])
    for folder in ('tools','c64','examples/hors_v3_preview','docs/benchmarks/hors-v3-preview'):
        relevant.update(f.relative_to(ROOT).as_posix() for f in (ROOT/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ('.pyc','.md') and f.name!='summary.json')
    record['sha256']={name:sha(ROOT/name) for name in sorted(relevant) if name!=RECORD}
    (ROOT/RECORD).write_text(json.dumps(record,indent=2)+'\n')
    check()
    print('Recorded fresh HORS-V3 evidence for',len(record['results']),'cartridges.')

if __name__=='__main__':main()
