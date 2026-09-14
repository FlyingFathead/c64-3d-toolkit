"""Independent GMod3 collection builder: menu, runtime reload and packed pictures."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from . import __version__, gmod3_image as image
from .gmod3_catalog import frames_for, mesh_for, read_json
from .gmod3_v3 import assemble_cartridge
from .gmod3_paging import configure as paging
from .hors_v3 import encoding_plan
from .hors_v3_help import help_pages, packed_help
from .buildscreen import screen_codes
from .emit import bytes_lines
from .demo_colors import once

TITLE = 'Demo Cart v3.0: GMod3 All-in-One'
STEM = 'demo-cart-v3.0-gmod3-all-in-one'


def collection_help(source, row):
    pages=[[
        'Demo Cart v3.0                 pg 1/2 >', 'GMod3 All-in-One help',
        'STOP / F1  collection menu', 'N / P    next / previous demo',
        'C        next Dragon shade / wire', 'SHIFT+H  open / close help',
        'SPACE    close help', 'CURSOR / JOY1/2 L/R  direction',
        '+ / - / 0   speed up / down / reset', 'F2       reset presentation',
        'F3       foreground / source palette', 'F4       next background',
        'F5       background cycle on / off', 'F6 / F7  slower / faster cycle',
        'F8       border black / follow', 'CTRL+F7  independent border',
        'Even F-keys = SHIFT + odd F-key',
    ],[
        'Demo Cart v3.0                 pg 2/2 <', 'GMod3 All-in-One help',
        'SHIFT+S  stars on / off', '1/2/3    stars reset / more / less',
        '4        light / full stars', 'SHIFT+I  model info on / off',
        'SHIFT+F  FPS and speed text on / off', 'SHIFT+U  all HUD text on / off',
        '5        exhibition on / off', '6        sequential / random',
        '7/8      interval -/+5s (5..60s)',
    ]]
    if row['mode_frames']:
        pages[1] += ['SAKU PRESENTATIONS:', 'SHIFT+T/W solid on white, stars off',
            'SHIFT+G  gradient + stars', 'SHIFT+R  spin / crawl',
            'SHIFT+B  white card / gradient', 'SHIFT+O  outline / gradient']
    pages[1] += ['LEFT/RIGHT pages. STOP returns to menu.']
    packed,offsets=packed_help(pages)
    start=source.index('hp_packed:\n')+len('hp_packed:\n');end=source.index('.if * > $c400',start)
    source=source[:start]+'\n'.join(bytes_lines(packed))+f'\nhp_page_lo: .byte <hp_packed,<({offsets[1]}+hp_packed)\nhp_page_hi: .byte >hp_packed,>({offsets[1]}+hp_packed)\n'+source[end:]
    return source


def runtime_hook(row, interactive, directory_bank):
    def transform(source):
        if interactive:
            # F1 remains distinct from Shift+F1 (F2 presentation reset).
            source=once(source,'v3_shifted:\n        lda #0\n        beq v3_key_done\n        jmp v3_reset',
                'v3_shifted:\n        lda #0\n        bne collection_reset\n        jmp $a600\ncollection_reset:\n        jmp v3_reset')
            # Collection owns RUN/STOP, including slow-playback and help polls.
            # Reuse the existing scans; no extra idle-path CIA reads.
            source=once(source, '        bne hp_stop_return\n        jmp hp_open',
                '        bne hp_stop_return\n        jmp $a600')
            source=once(source, '        bne sd_stop_released\n        jsr hp_open',
                '        bne sd_stop_released\n        jmp $a600')
            source=once(source, 'hp_space_read:\n        and #$90',
                'hp_space_read:\n        cmp #$80\n        bcs collection_help_space\n        jmp $a600\ncollection_help_space:\n        and #$90')
            source=collection_help(source,row)
        if interactive and row['screen_color']&15:
            # Map the source background colour, preserving black foregrounds
            # in the original colour-combination demos.
            background=row['screen_color']&15
            first=source.index('v3_prepare_background:\n');last=source.index('v3_prepare_slot:\n',first)
            replacement=f"""v3_prepare_background:
        lda v3_background
        cmp v3_lut_last
        beq v3_prepare_slot
        sta v3_lut_last
        ldy #0
gmod3_palette_loop:
        tya
        and #15
        cmp #{background}
        bne gmod3_palette_low
        lda v3_background
gmod3_palette_low:
        sta v3_lut_high
        tya
        lsr a
        lsr a
        lsr a
        lsr a
        cmp #{background}
        bne gmod3_palette_high
        lda v3_background
gmod3_palette_high:
        asl a
        asl a
        asl a
        asl a
        ora v3_lut_high
        sta v3_color_lut,y
        iny
        bne gmod3_palette_loop
"""
            source=source[:first]+replacement+source[last:]
            source=source.replace('        lda v3_background\n        beq v3_color_copy\n',
                f'        lda v3_background\n        cmp #{background}\n        beq v3_color_copy\n')
        if interactive:
            source=source.replace('v3_border_mode: .byte 1','v3_border_mode: .byte 2',1)
            source=source.replace('v3_custom_border: .byte 0',f'v3_custom_border: .byte {row["border_color"]}',1)
        source=paging(source,pages=row['frames']//128 if row['frames']>255 else 1,
            directory_bank=directory_bank or 0,interactive=interactive,target_fps=row.get('target_fps'))
        source=once(source,'frame_begin:\n','frame_begin:\n        jsr $a500\n')
        if not interactive:
            source+='''
* = $2400
.logical $c600
collection_drain:
        lda ready_slot
        cmp #$ff
        bne collection_drain
        lda tick_counter
collection_last_refresh:
        cmp tick_counter
        beq collection_last_refresh
'''
            if row.get('target_fps'):
                source+='collection_last_hold:\n        lda gp_hold\n        bne collection_last_hold\n'
            source+='''        jmp $a600
.here
* = $2500
collection_drain_copy:
        ldx #0
collection_drain_copy_loop:
        lda $2400,x
        sta $c600,x
        inx
        bne collection_drain_copy_loop
        rts
'''
            source=once(source,'        sei\n        cld\n','        sei\n        cld\n        jsr collection_drain_copy\n')
        # Full SAKU controls retain explicit Shift+G = stars on. Reset and boot
        # default to stars off in this collection.
        if row['mode_frames']:
            start=source.index('fx_reset:\n');end=source.index('fx_',start+len('fx_reset:\n')) if False else source.index('        rts',start)
            section=source[start:end]
            section=section.replace('        lda #1\n        sta fx_enabled','        lda #0\n        sta fx_enabled')
            source=source[:start]+section+source[end:]
        return source
    return transform


def layout(rows, cache, interactive):
    rows=copy.deepcopy(rows)
    rows.sort(key=lambda r:(0 if r['mode_frames'] else 1 if r['name'].startswith('DRAGON ') else 2,r['id']))
    if not interactive:
        expanded=[]
        for row in rows:
            if row['mode_frames']:
                for mode,name in enumerate(('SOLID SPIN','GRADIENT SPIN','SOLID CRAWL','GRADIENT CRAWL','CARD SPIN','CARD CRAWL','OUTLINE SPIN','OUTLINE CRAWL')):
                    item=copy.deepcopy(row); item.update(name='SAKU '+name,mode_frames=0,variants=[],frames=30,
                        slice=[mode*30,(mode+1)*30],screen_color=0x11 if mode in (0,2) else 0x10)
                    expanded.append(item)
            else:expanded.append(row)
        rows=expanded
    cursor=1
    for index,row in enumerate(rows):
        row['index']=index;row['runtime_bank']=cursor;cursor+=3
        row['directory_bank']=cursor if row['frames']>255 else None
        if row['directory_bank'] is not None:cursor+=1
        row['first_bank']=cursor
        frames=frames_for(cache,row)
        if 'slice' in row:frames=frames[slice(*row['slice'])]
        planned,encoder,*_=encoding_plan(frames,row['colors'],row['screen_color'])
        offset=0;total=0;bank=cursor
        for frame in planned:
            block,_=encoder(frame,row['colors']);total+=len(block)
            if offset+len(block)>8192:bank+=1;offset=0
            offset+=len(block)
        cursor=bank+1
        row.update(last_bank=bank,data_banks=bank-row['first_bank']+1,encoded_bytes=total,
            allocated_kib=(cursor-row['runtime_bank'])*8)
    if cursor>2048:raise ValueError(f'Collection needs {cursor*8} KiB, exceeds 16384 KiB; all samples retained')
    return rows,cursor


def menu_sources(root, rows, occupied, interactive, work, tass):
    gen=Path(work);gen.mkdir(parents=True,exist_ok=True)
    (gen/'collection-config.inc').write_text(f'ENTRY_COUNT = {len(rows)}\nINTERACTIVE = {int(interactive)}\n')
    lines=[]
    arrays={'runtime_lo':[r['runtime_bank']&255 for r in rows], 'runtime_hi':[r['runtime_bank']>>8 for r in rows]}
    dragons=[r['index'] for r in rows if r['name'].startswith('DRAGON ')]
    if interactive:
        arrays['shade_next']=[dragons[(dragons.index(i)+1)%len(dragons)] if i in dragons else 255 for i in range(len(rows))]
    else:
        arrays['sample_lo']=[r['frames']&255 for r in rows];arrays['sample_hi']=[r['frames']>>8 for r in rows]
    for name,values in arrays.items():lines+=[name+':',*bytes_lines(values)]
    pages=(len(rows)+14)//15
    for part,op in [('lo','<'),('hi','>')]:lines += [f'screen_{part}: .byte '+','.join(f'{op}screen_{i}' for i in range(pages))]
    (gen/'collection-tables.inc').write_text('\n'.join(lines)+'\n')
    lines=[]
    for page in range(pages):
        text=[' '*40 for _ in range(25)]
        def center(row,s):
            if len(s)>40:raise ValueError('Menu label exceeds 40 columns')
            text[row]=s.center(40)
        center(0,'Demo Cart v3.0')
        center(1,'GMod3 All-in-One'+(' / benchmark' if not interactive else ''))
        center(2,f'HORS-V4-GMOD3 | {len(rows)} entries | page {page+1}/{pages}')
        for i,r in enumerate(rows[page*15:page*15+15]):
            name=r['name'][:30]
            text[4+i]=f'{r["index"]+1:02d} {name:<30} {r["frames"]:4d}  '[:40].ljust(40)
        center(19,'CURSOR: choose | SPACE: start')
        center(20,'STOP/F1 menu | N/P demos | C shades' if interactive else 'Automatic full-loop benchmark sequence')
        center(21,'SHIFT+H help | stars initially off' if interactive else 'No input polling or starfield')
        center(22,'cart type: GMod3')
        center(23,f'used: {occupied*8} KiB | free: {16384-occupied*8} KiB')
        codes=screen_codes(''.join(text))+[32]*24
        lines += [f'screen_{page}:',*bytes_lines(codes)]
    (gen/'collection-screens.inc').write_text('\n'.join(lines)+'\n')
    shutil.copyfile(Path(root)/'c64/gmod3/collection.asm',gen/'collection.asm')
    subprocess.run([str(tass),'--nostart','--vice-labels','-l',str(gen/'collection.lbl'),'-o',str(gen/'collection.bin'),str(gen/'collection.asm')],check=True)
    return (gen/'collection.bin').read_bytes()


def build(root, *, tass, cartconv, outdir, interactive=True, only=None):
    root=Path(root).resolve();outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    cache=root/'build/gmod3-catalog';rows=read_json(cache/'catalog.json')
    if only is not None:rows=[r for r in rows if r['id'] in only]
    rows,occupied=layout(rows,cache,interactive)
    stem=STEM+('' if interactive else '-benchmark')
    work=root/'build'/stem;work.mkdir(parents=True,exist_ok=True)
    cart=image.new_image(16)
    boot=menu_sources(root,rows,occupied,interactive,work,tass);image.put_bank(cart,0,boot)
    entries=[]
    for row in rows:
        entry_stem=f'{stem}-{row["index"]:02d}'
        frames=frames_for(cache,row)
        if 'slice' in row:frames=frames[slice(*row['slice'])]
        print(f'Building {row["index"]+1}/{len(rows)}: {row["name"]}',flush=True)
        crt,manifest=assemble_cartridge(root,frames,mesh_for(row),tass=tass,cartconv=cartconv,
            outdir=work/'entries',stem=entry_stem,size_mib=16,first_bank=row['first_bank'],
            colors=row['colors'],color_index=row['screen_color']>>4,background_color=row['screen_color']&15,
            border_color=row['border_color'],interactive=interactive,collection=True,renderer_name='hors-renderer-v4',
            include_starfield=interactive,starfield_profile='light',mode_frames=row['mode_frames'],
            presentation_variants=row['variants'],occlusion_bounds=row['occlusion_bounds'] if interactive else None,
            page_frames=128 if row['frames']>255 else 0,directory_bank=row['directory_bank'],
            source_transform=runtime_hook(row,interactive,row['directory_bank']))
        raw=(root/manifest['runtime_work']/(entry_stem+'.bin')).read_bytes()
        for n in range(3):image.put_bank(cart,row['runtime_bank']+n,raw[(n+1)*8192:(n+2)*8192])
        for bank in range(row['first_bank'],row['last_bank']+1):image.put_bank(cart,bank,raw[bank*8192:(bank+1)*8192])
        if row['directory_bank'] is not None:
            bank=row['directory_bank'];image.put_bank(cart,bank,raw[bank*8192:(bank+1)*8192])
        if manifest['highest_bank']!=row['last_bank']:raise ValueError('Collection preflight/assembly mismatch')
        labels=outdir/'metadata'/('interactive' if interactive else 'benchmark')/f'{row["index"]:02d}.lbl'
        labels.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(crt.with_suffix('.lbl'),labels)
        manifest.update(collection_entry=row['index'],collection_name=TITLE,cartridge_capacity=None)
        row['runtime']=manifest;row['labels']=labels.relative_to(outdir).as_posix()
        entries.append(row)
        # Standalone intermediate CRTs are not deliverables.
        crt.unlink(); (root/manifest['runtime_work']/(entry_stem+'.bin')).unlink()
        print(f'Entry used: {row["allocated_kib"]} KiB | collection used: {(row["last_bank"]+1)*8} KiB | remaining: {16384-(row["last_bank"]+1)*8} KiB',flush=True)
    crt=outdir/(stem+'.crt');container=image.convert(image=cart,raw=work/(stem+'.bin'),crt=crt,cartconv=cartconv,name='DEMO CART V3.0 GMOD3 ALL-IN-ONE',cwd=root)
    report=dict(title=TITLE,renderer='hors-renderer-v4',renderer_label='hors-v4-gmod3',cartridge='GMod3',interactive=interactive,
        capacity_kib=16384,used_kib=occupied*8,free_kib=16384-occupied*8,allocated_banks=occupied,
        accounting='allocated 8 KiB banks including bootstrap, each runtime, paging and data padding',
        entries=entries,container=container,starfield_default='disabled',
        keymap={'RUN/STOP (Esc in VICE)':'collection menu','F1':'collection menu','N/P':'next/previous entry','C':'next Dragon shade or wireframe','Shift+H':'help'} if interactive else {},
        collection_labels='metadata/'+stem+'.lbl')
    shutil.copyfile(work/'collection.lbl',outdir/'metadata'/(stem+'.lbl'))
    (outdir/(stem+'-manifest.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(f'{TITLE}: {len(rows)} entries; used {occupied*8} KiB; free {16384-occupied*8} KiB',flush=True)
    return crt,report
