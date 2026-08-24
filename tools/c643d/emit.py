from __future__ import annotations
from pathlib import Path
from .pipeline import build_xchunk_tables, FrameBuild
from .font import bitmap_text

PTR_BASE=0x1600; PTR_LIMIT=0x1700
CLEAR_BASE=0x4800; CLEAR_LIMIT=0x6000
LINE_BASE=0x8000; LINE_LIMIT=0xC800
XCHUNK_LEVEL_BASE=0x1700; XCHUNK_MASK_BASE=0x1800; XCHUNK_LIMIT=0x2000


def bytes_lines(values, per=16):
    values=list(values); out=[]
    for i in range(0,len(values),per):
        out.append('        .byte '+','.join(f'${v:02x}' for v in values[i:i+per]))
    return out


def emit_hud(path:Path, shape_name:str, verts:int, edges:int):
    label=shape_name.upper().replace('_',' ')
    # 32..39 are reserved by the existing FPS display, so static HUD gets 31 chars max.
    text=f'{label} V:{verts:03d} E:{edges:03d}'
    raw=bitmap_text(text,31)
    lines=[
        '; GENERATED HUD -- bottom-left bitmap row, cells 0..31',
        f'; {text}',
        f'HUD_STATIC_LEN = {len(raw)}',
        'hud_static_bitmap:',
    ]+bytes_lines(raw)+['hud_static_bitmap_end:','']
    path.write_text('\n'.join(lines),encoding='ascii')
    return text


def _choose_overflow_frames(block_sizes:list[int], primary_cap:int, overflow_cap:int):
    """Choose whole frame blocks to place in the low-RAM overflow arena.

    Frame line records are independently addressed through pointer tables, so
    they do not need to be physically consecutive in orientation order. This
    lets us use the otherwise-idle RAM between generated clear data and bitmap
    #2 at $6000 instead of discarding rotation orientations just because the
    main $8000-$c7ff line arena is a few KiB short.
    """
    total=sum(block_sizes)
    need=max(0,total-primary_cap)
    if need==0:return set()
    if need>overflow_cap:return None
    # subset-sum DP; <=48 orientations in normal builds, overflow <= ~6 KiB.
    poss={0:()}
    for i,size in enumerate(block_sizes):
        for cur,items in list(poss.items())[::-1]:
            nxt=cur+size
            if nxt<=overflow_cap and nxt not in poss:
                poss[nxt]=items+(i,)
    candidates=[v for v in poss if v>=need]
    if not candidates:return None
    best=min(candidates)
    return set(poss[best])


def emit_tables(path:Path, frames:list[FrameBuild], renderer:str, candidate_edges:int):
    nframes=len(frames)
    ptr_end=PTR_BASE+nframes*4
    if ptr_end>PTR_LIMIT:
        raise RuntimeError(f'frame pointer tables reach ${ptr_end:04x}, limit ${PTR_LIMIT:04x}; reduce --frames')

    # Clear blocks live contiguously at $4800. Pointer arrays are deliberately
    # kept out of this arena so the remaining bytes below $6000 can be used as
    # a second line-record arena for complex imported meshes.
    clear_blob=[]; clear_addrs=[]; cur=CLEAR_BASE
    for fr in frames:
        clear_addrs.append(cur); block=[len(fr.clear_spans)]
        for span in fr.clear_spans:block.extend(span)
        clear_blob.extend(block); cur+=len(block)
    clear_data_end=cur
    if clear_data_end>CLEAR_LIMIT:
        raise RuntimeError(f'clear tables reach ${clear_data_end:04x}, limit ${CLEAR_LIMIT:04x}')

    # Build independent per-orientation line blocks. The primary arena is the
    # historical $8000-$c7ff range. Overflow whole frame blocks may be packed
    # directly after the clear data and before bitmap #2 at $6000.
    line_blocks=[]
    for fr in frames:
        block=[len(fr.records)]
        for rec in fr.records:block.extend(rec)
        line_blocks.append(block)
    sizes=[len(b) for b in line_blocks]
    primary_cap=LINE_LIMIT-LINE_BASE
    overflow_base=clear_data_end
    overflow_cap=CLEAR_LIMIT-overflow_base
    overflow_frames=_choose_overflow_frames(sizes,primary_cap,overflow_cap)
    if overflow_frames is None:
        total=sum(sizes)
        combined=primary_cap+overflow_cap
        pseudo_end=LINE_BASE+max(0,total-overflow_cap)
        raise RuntimeError(
            f'line tables need {total} bytes; available {combined} bytes '
            f'(${LINE_BASE:04x}-${LINE_LIMIT-1:04x} plus ${overflow_base:04x}-${CLEAR_LIMIT-1:04x}); '
            f'equivalent primary reach ${pseudo_end:04x}; reduce --frames or mesh detail')

    line_addrs=[0]*nframes; primary_blob=[]; overflow_blob=[]
    pcur=LINE_BASE; ocur=overflow_base
    for i,block in enumerate(line_blocks):
        if i in overflow_frames:
            line_addrs[i]=ocur; overflow_blob.extend(block); ocur+=len(block)
        else:
            line_addrs[i]=pcur; primary_blob.extend(block); pcur+=len(block)
    if pcur>LINE_LIMIT or ocur>CLEAR_LIMIT:
        raise RuntimeError('internal line-table arena packing overflow')

    clear_lo=[a&255 for a in clear_addrs]; clear_hi=[a>>8 for a in clear_addrs]
    line_lo=[a&255 for a in line_addrs]; line_hi=[a>>8 for a in line_addrs]

    counts=[len(f.records) for f in frames]; pixels=[f.raw_pixels for f in frames]; uniq=[f.unique_pixels for f in frames]
    clears=[sum(s[2]*8 for s in f.clear_spans) for f in frames]; spans=[len(f.clear_spans) for f in frames]
    mism=[m for f in frames for m in f.dda_mismatches] or [0]
    lines=['; GENERATED FILE -- do not hand-edit.',f'; renderer={renderer}; orientations={nframes}; candidate edges={candidate_edges}',
           f'; runs/frame min={min(counts)} max={max(counts)} avg={sum(counts)/nframes:.1f}',
           f'; pixels/frame min={min(pixels)} max={max(pixels)} avg={sum(pixels)/nframes:.1f}',
           f'; unique pixels/frame min={min(uniq)} max={max(uniq)} avg={sum(uniq)/nframes:.1f}',
           f'; clear bytes/frame min={min(clears)} max={max(clears)} avg={sum(clears)/nframes:.1f}',
           f'; line arenas: primary={len(primary_blob)} bytes overflow={len(overflow_blob)} bytes','']

    fast_stats=None
    if renderer in ('bytechunk','yunroll'):
        levels,masks=build_xchunk_tables()
        lines += [f'* = ${XCHUNK_LEVEL_BASE:04x}','xchunk_levels:']+bytes_lines(levels)+['',f'* = ${XCHUNK_MASK_BASE:04x}']
        for i,t in enumerate(masks):lines += ['',f'xchunk_mask{i}:']+bytes_lines(t)
        lines += ['', 'generated_xchunk_end = *','']
        if XCHUNK_MASK_BASE+8*256>XCHUNK_LIMIT:raise RuntimeError('xchunk LUT overflow')
        chunks=pix=ops=0
        from .pipeline import decode_record_points
        for fr in frames:
            for rec in fr.records:
                if ((rec[3]>>6)&1):continue
                pts=decode_record_points(rec); groups=[]; curg=[]; prev=None
                for pt in pts:
                    cell=pt[0]>>3
                    if prev is None or cell==prev:curg.append(pt)
                    else:groups.append(curg);curg=[pt]
                    prev=cell
                if curg:groups.append(curg)
                for g in groups:
                    if len(g)==8 and (g[0][0]&7)==0:
                        chunks+=1;pix+=8
                        ops += len({((y>>3)*320+(x>>3)*8+(y&7)) for x,y in g})
        fast_stats=(chunks,pix,ops)

    # Pointer tables live in the reserved gap at $1600-$16ff, safely above renderer+HUD source data.
    lines += [f'* = ${PTR_BASE:04x}','','frame_clear_ptr_lo:']+bytes_lines(clear_lo)
    lines += ['','frame_clear_ptr_hi:']+bytes_lines(clear_hi)
    lines += ['','frame_line_ptr_lo:']+bytes_lines(line_lo)
    lines += ['','frame_line_ptr_hi:']+bytes_lines(line_hi)+['','generated_ptr_end = *','']

    lines += [f'* = ${CLEAR_BASE:04x}','','frame_clear_data:']+bytes_lines(clear_blob)
    lines += ['','generated_clear_data_end = *','']
    if overflow_blob:
        lines += [f'* = ${overflow_base:04x}','','frame_line_overflow_data:']+bytes_lines(overflow_blob)
        lines += ['','generated_line_overflow_end = *','']
    lines += [f'* = ${LINE_BASE:04x}','','frame_line_data:']+bytes_lines(primary_blob)
    lines += ['','generated_line_primary_end = *','']
    path.write_text('\n'.join(lines),encoding='ascii')

    stats={
        'frames':nframes,'candidate_edges':candidate_edges,'runs_min':min(counts),'runs_max':max(counts),'runs_avg':sum(counts)/nframes,
        'pixels_min':min(pixels),'pixels_max':max(pixels),'pixels_avg':sum(pixels)/nframes,
        'unique_min':min(uniq),'unique_max':max(uniq),'unique_avg':sum(uniq)/nframes,
        'clear_min':min(clears),'clear_max':max(clears),'clear_avg':sum(clears)/nframes,
        'clear_table_bytes':len(clear_blob),'line_table_bytes':sum(sizes),
        'line_primary_bytes':len(primary_blob),'line_overflow_bytes':len(overflow_blob),
        'dda_mismatch_max':max(mism),'dda_mismatch_avg':sum(mism)/len(mism)
    }
    if fast_stats:
        c,p,o=fast_stats; stats.update(xchunks=c,xchunk_pixels=p,xchunk_ops=o,xchunk_reduction=(1-o/p)*100 if p else 0)
    return stats
