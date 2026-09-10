"""Opt-in hors-render-v2 beta 1: independent full pictures, bounded map batches.

The beta requires every frame to use literal byte spans. It does not reclaim
memory when a vector fallback is needed; such candidates fail explicitly.
"""
from pathlib import Path
import json, shutil, tempfile
from .optimize import picture_bytes
from .cartstream import frame_block as vector_block

BETA_NAME='hors-render-v2-beta1'


def spans(bitmap, gap):
    ranges=[]
    for offset,value in enumerate(bitmap):
        if value:
            if ranges and offset-ranges[-1][1]<=gap and offset-ranges[-1][0]<255:
                ranges[-1][1]=offset
            else:ranges.append([offset,offset])
    return [(lo,bitmap[lo:hi+1]) for lo,hi in ranges]


def encoder(gap=6, batch_budget=2048):
    if gap<1 or batch_budget<1:raise ValueError('v2 gap and batch budget must be positive')
    def encode(frame,colors=True):
        original,meta=vector_block(frame,colors)
        if meta>1024:raise ValueError('v2 metadata exceeds its 1 KiB cache')
        bitmap=picture_bytes(frame)[:7680];runs=spans(bitmap,gap)
        output=bytearray(original[:meta]);output.extend((0x8000|len(runs)).to_bytes(2,'little'))
        planned_cost=0;proof=bytearray(7680)
        for i,(offset,data) in enumerate(runs):
            planned_cost+=180+15*len(data)
            flush=i+1==len(runs) or planned_cost+180+15*len(runs[i+1][1])>batch_budget
            output.extend((offset&255,(offset>>8)|(128 if flush else 0),len(data)));output.extend(data)
            proof[offset:offset+len(data)]=data
            if flush:planned_cost=0
        if proof!=bitmap:raise AssertionError('v2 host bitmap proof failed')
        if len(output)>8192:raise ValueError('v2 literal picture exceeds one 8 KiB bank; use another candidate')
        return bytes(output),meta
    return encode


def patch_helper(source):
    marker='.if V9_BYTE_SPANS\n* = $4080'
    if source.count(marker)!=1:raise ValueError('Unsupported mapping-helper layout')
    extra='''
; v2 owns the former vector dispatch low-byte page; all frames must be direct.
* = $4f00
hors_v2_extension_start:
hors_v2_span_finished:
        dec lines_remaining
        bne hors_v2_more_spans
        dec lines_remaining+1
        beq hors_v2_picture_done
hors_v2_more_spans:
        lda hors_v2_span_flags
        bmi hors_v2_release
        jmp hors_v2_span_mapped
hors_v2_release:
        jsr v9_map_off
        jmp v9_span
hors_v2_picture_done:
        jmp v9_map_off
hors_v2_span_flags: .byte $80
hors_v2_extension_end:
.if * > $5000
.error "hors-render-v2 extension overlaps metadata cache"
.endif
'''
    source=source.replace(marker,'.if V9_BYTE_SPANS\n'+extra+'\n* = $4080')
    source=source.replace('v9_span:\n        jsr v9_map_on\n','v9_span:\n        jsr v9_map_on\nhors_v2_span_mapped:\n')
    old='        lda (STREAM_LO),y\n        clc\n        adc draw_base_hi'
    if source.count(old)!=1:raise ValueError('Unsupported direct-span header')
    source=source.replace(old,'        lda (STREAM_LO),y\n        sta hors_v2_span_flags\n        and #$1f\n        clc\n        adc draw_base_hi')
    old='''        jsr v9_map_off
        dec lines_remaining
        bne v9_span
        dec lines_remaining+1
        bne v9_span
v9_bytes_done:'''
    if source.count(old)!=1:raise ValueError('Unsupported direct-span tail')
    return source.replace(old,'        jmp hors_v2_span_finished\nv9_bytes_done:')


def assemble_scene(root,frames,scene,*,draw_gap=6,batch_budget=2048,**kwargs):
    """Build in a staged source tree; existing v1 source files remain unchanged.

    Run concurrent builds in separate processes, as the autotune CLI does.
    """
    from . import cartscene
    if kwargs.get('intro') or kwargs.get('ending'):
        raise ValueError('hors-render-v2 beta1 currently supports standalone looping scenes; intro/ending integration is not enabled')
    root=Path(root);out=Path(kwargs['outdir']);stem=kwargs['stem']
    original_pack=cartscene.pack_scene_frames;encode=encoder(draw_gap,batch_budget)
    def pack(items,colors=True,**options):
        options.update(encoder=encode,direct_bytes=True)
        image,directory=original_pack(items,colors,**options)
        if not all(d.get('encoding')=='byte-spans' for d in directory):
            raise ValueError('v2 requires all frames to be direct byte spans')
        return image,directory
    with tempfile.TemporaryDirectory(prefix='hors-v2-') as td:
        stage=Path(td);shutil.copytree(root/'c64',stage/'c64')
        helper=stage/'c64/cart/easyflash-stream-v10-scene-helper.asm';helper.write_text(patch_helper(helper.read_text()))
        source=stage/'c64/renderer-yunroll-cart-v10-scene.asm';text=source.read_text()
        first=text.index('* = $4f00\nv3_entry_lo:');last=text.index('* = $9a00',first)
        text=text[:first]+'v3_entry_lo = $4f00 ; unavailable in byte-only v2\n'+text[last:];source.write_text(text)
        kwargs['renderer']='hors-render-v1-scene'
        cartscene.pack_scene_frames=pack
        try:crt,manifest=cartscene.assemble_scene(stage,frames,scene,**kwargs)
        finally:cartscene.pack_scene_frames=original_pack
        # Preserve the compiler oracle and runtime bytes for ordinary verification.
        workname=f'{stem}-stream-scene';saved=root/'build'/workname
        saved.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(stage/'build'/workname,saved,dirs_exist_ok=True)
    manifest.update(renderer=BETA_NAME,wire_format='hors-v2-batched-literal-spans-1',
        beta={'version':1,'draw_gap':draw_gap,'batch_cost_budget':batch_budget,
              'previous_picture_dependency':False,'vector_fallback':False,
              'mapping_release_flag':'bit 7 of destination offset high byte',
              'reclaimed_vector_dispatch_range':[0x4f00,0x5000],
              'extra_reserved_RAM_bytes':0,
              'batch_budget_is_host_cost_model_not_hard_measured_bound':True})
    (out/f'{stem}-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return crt,manifest
