"""Opt-in V4 scene streamer: paged ROM directory, dual-chip packing and pacing.

The v4 rasterisation kernels and v2/v3/v4 builders are preserved. Directory
pages contain seven 256-byte arrays, cached at $4800-$4eff. ROMH banks 1/2
hold up to eight pages (2048 samples). Frames use ROML/ROMH banks 3..63.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from . import __version__
from .cartstream import frame_block, emit_directory
from .cartridge import new_easyflash_image, easyflash_offset, put_easyflash_chip, convert_easyflash, check_easyflash_crt
from .emit import bytes_lines
from .font import bitmap_text, FONT

MAX_SCENE_FRAMES = 2048
RENDERER = 'yunroll-cart-v4-scene'
DIRECTORY_FIELDS = ('bank','source_lo','source_hi','length_lo','length_hi','meta_lo','meta_hi')


def pack_scene_frames(frames, colors=True):
    if not 1 <= len(frames) <= MAX_SCENE_FRAMES:
        raise ValueError(f'scene stream requires 1..{MAX_SCENE_FRAMES} frames')
    image=new_easyflash_image()
    # Keep the original 3-bank RAM bootstrap and reserve ROMH 0..2.
    placements=[(chip,bank) for chip in ('roml','romh') for bank in range(3,64)]
    place=offset=0; directory=[]
    for i,frame in enumerate(frames):
        block,meta=frame_block(frame,colors)
        if offset+len(block)>8192:
            place+=1; offset=0
        if place>=len(placements):
            raise ValueError(f'EasyFlash capacity exhausted at scene frame {i}; increase sample-step or reduce detail')
        chip,bank=placements[place]; address=(0x8000 if chip=='roml' else 0xa000)+offset
        start=easyflash_offset(bank,chip,offset)
        image[start:start+len(block)]=block
        directory.append(dict(frame=i,chip=chip,bank=bank,address=address,bytes=len(block),metadata_bytes=meta,runs=len(frame.records),sha256=hashlib.sha256(block).hexdigest()))
        offset+=len(block)
    for page in range((len(frames)+255)//256):
        records=directory[page*256:(page+1)*256]
        values=[
            [d['bank'] for d in records], [d['address']&255 for d in records],
            [d['address']>>8 for d in records], [d['bytes']&255 for d in records],
            [d['bytes']>>8 for d in records], [d['metadata_bytes']&255 for d in records],
            [d['metadata_bytes']>>8 for d in records],
        ]
        blob=b''.join(bytes(a).ljust(256,b'\0') for a in values)
        start=easyflash_offset(1+page//4,'romh',(page%4)*1792)
        image[start:start+len(blob)]=blob
    return image,directory


def validate_hud(text):
    text=text.upper()
    if not 1<=len(text)<=31:
        raise ValueError('--hud-text must contain 1..31 characters')
    unknown=set(text)-FONT.keys()
    if unknown:
        raise ValueError(f'unsupported HUD characters: {sorted(unknown)}')
    return text


def assemble_scene(root,frames,scene,*,tass,cartconv,outdir,stem,hud_text,frame_ticks=4,tass_args=(),colors=True,color_index=1,intro=False,text_overlay=True,ending=False):
    if not 1<=frame_ticks<=255:
        raise ValueError('--frame-ticks must be 1..255 PAL raster ticks')
    if ending and not intro:raise ValueError('--ending requires --intro')
    hud_text=validate_hud(hud_text)
    root=Path(root);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    work=root/'build'/f'{stem}-stream-scene';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
    # Keep the expensive compilation checkpoint even if ROM packing fails.
    (work/'oracle.json').write_text(json.dumps([asdict(f) for f in frames]))
    image,directory=pack_scene_frames(frames,colors)
    # Reuse the established LUT emitter with a full-size RAM directory page.
    dummy=[dict(bank=0,address=0,bytes=0,metadata_bytes=0)]*256
    emit_directory(gen/'tables.inc',dummy)
    raw_hud=bitmap_text(hud_text)
    (gen/'hud.inc').write_text(f'; {hud_text}\nHUD_STATIC_LEN = {len(raw_hud)}\nhud_static_bitmap:\n'+'\n'.join(bytes_lines(raw_hud))+'\nhud_static_bitmap_end:\n')
    shutil.copyfile(root/'c64/cart/easyflash-stream-v4-scene-helper.asm',gen/'cart-v4-scene-helper.inc')
    src=(root/f'c64/renderer-{RENDERER}.asm').read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(frames)}\nFRAME_TICKS = {frame_ticks}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(colors)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${color_index:X}0',1)
    if not text_overlay:
        src=src.replace('        jsr init_static_hud','').replace('        jsr init_fps_label','').replace('        jsr maybe_update_fps','')
    if intro:
        from .cartintro import emit_intro
        emit_intro(gen/'intro.inc',ending=ending)
        src=src.replace('        ; Per-build foreground/background colour', '        jsr intro_start\n\n        ; Per-build foreground/background colour',1)
        src=src.replace('        lda #0\n        sta frame_index', '        lda #$3b\n        sta $d011\n        lda #0\n        sta frame_index',1)
        if ending:
            if '        inc frame_counter\n        jsr scene_advance_frame' not in src:
                raise ValueError('scene renderer has no finite-playback handoff site')
            src=src.replace('        inc frame_counter\n        jsr scene_advance_frame','''        inc frame_counter
        lda frame_index_hi
        cmp #>(FRAME_COUNT-1)
        bne scene_continue
        lda frame_index
        cmp #<(FRAME_COUNT-1)
        bne scene_continue
scene_last_wait:
        lda ready_slot
        cmp #$ff
        bne scene_last_wait
        lda scene_hold
        bne scene_last_wait
        jmp outro_start
scene_continue:
        jsr scene_advance_frame''',1)
        src+='\n        .include "generated/intro.inc"\n'
    src=src.replace('        .include "generated/hud.inc"','        .include "generated/hud.inc"\n.if * > $1700\n.error "renderer/HUD overlaps LUT"\n.endif')
    asm=work/'main.asm';asm.write_text(src)
    ram=work/'runtime.prg';labels=outdir/f'{stem}.lbl'
    subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(labels),'-o',str(ram),str(asm)],check=True,cwd=root)
    blob=ram.read_bytes();load=int.from_bytes(blob[:2],'little');end=load+len(blob)-2
    if load!=0x0801 or end>(0x9a00 if intro else 0x6000):
        raise ValueError('scene runtime outside bootstrap RAM destination')
    padded=bytearray(0x5800);runtime_end=min(end,0x6000)
    padded[load-0x0800:runtime_end-0x0800]=blob[2:2+runtime_end-load]
    for bank in range(3):
        put_easyflash_chip(image,bank,'roml',bytes(padded[bank*8192:(bank+1)*8192]).ljust(8192,b'\0'))
    boot=work/'boot.bin'
    subprocess.run([tass,*tass_args,'--nostart','-o',str(boot),str(root/'c64/cart/easyflash-stream-v4-scene-boot.asm')],check=True,cwd=root)
    boot_blob=bytearray(boot.read_bytes())
    if intro:
        intro_bytes=blob[2+0x8000-load:2+end-load]
        boot_blob[0x400:0x400+len(intro_bytes)]=intro_bytes
    put_easyflash_chip(image,0,'romh',bytes(boot_blob))
    raw=work/f'{stem}.bin';raw.write_bytes(image)
    crt=outdir/f'{stem}.crt';convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name='DONT LOSE YOUR MARBLES',cwd=root)
    check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=root)
    manifest=dict(format='c643d-easyflash-stream-scene',version=1,toolkit_version=__version__,renderer=RENDERER,name=scene.name,frames=len(frames),vertices=len(scene.mesh.vertices),edges=len(scene.mesh.edges),faces=len(scene.mesh.faces),colors=colors,screen_color=color_index<<4,hud_text=hud_text,text_overlay=text_overlay,intro=intro,ending=ending,frame_index_bits=16,frame_ticks=frame_ticks,target_fps=50/frame_ticks,target_duration_seconds=len(frames)*frame_ticks/50,source_fps=scene.source_fps,sample_step=scene.sample_step,source_frames=[f.source_frame for f in scene.frames],directory_ram_bytes=1792,directory_rom_bytes=((len(frames)+255)//256)*1792,frame_buffer_bytes=8192,metadata_cache_bytes=3072,rom_frame_bytes=sum(d['bytes'] for d in directory),data_bank_capacity_bytes=122*8192,run_count_bits=16,frame_data=directory)
    (outdir/f'{stem}-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'built {crt}\n{len(frames)} frames; {manifest["rom_frame_bytes"]} vector bytes; target {manifest["target_duration_seconds"]:.2f}s at {manifest["target_fps"]:g} FPS',flush=True)
    return crt,manifest


def cmd_build_cart_scene(a):
    from . import cli
    from .blender import export_blend_scene
    from .sceneio import load_scene
    from .pipeline import build_scene_frames
    from .colors import c64_color_index
    if a.ending and not a.intro:raise ValueError('--ending requires --intro')
    if sum(bool(x) for x in (a.blend,a.scene,a.obj,a.svg,a.object))!=1 or not (a.blend or a.scene):
        raise ValueError('v4-scene requires exactly one --blend or --scene input')
    if a.frames is not None or a.rastertime_profiler or a.no_assemble:
        raise ValueError('v4-scene uses authored samples, standard HUD and cartridge assembly')
    if (a.viewport_height or 192)!=192:
        raise ValueError('v4-scene requires the 192-line viewport plus HUD')
    if not 1<=a.frame_ticks<=255:
        raise ValueError('--frame-ticks must be 1..255')
    if a.hud_text:validate_hud(a.hud_text)
    tass=cli.resolve_executable(a.tass,'tass');cartconv=cli.require_cartconv(a.cartconv,verbose=True)
    if not tass or not cartconv:return 2
    outdir=Path(a.output_dir).resolve() if a.output_dir else cli.BUILD
    stem=a.output or Path(a.blend or a.scene).stem+'-'+RENDERER
    if not cli._check_overwrite([outdir/f'{stem}{suffix}' for suffix in ('.crt','.lbl','-manifest.json')],a.overwrite_policy):return 2
    if a.blend:
        export=cli.BUILD/f'{stem}.c643dscene'
        export_blend_scene(a.blend,export,blender=a.blender,frame_start=a.frame_start,frame_end=a.frame_end,sample_step=a.sample_step,root=cli.ROOT,viewport_height=192,max_frames=MAX_SCENE_FRAMES)
    else:export=Path(a.scene)
    scene=load_scene(export)
    color,_,percell=cli._scene_color_policy(scene.mesh,a)
    print(f'compiling {len(scene.frames)} authored scene samples with V4 kernels...',flush=True)
    frames,_=build_scene_frames(scene,visibility_mode='surface' if a.visibility=='auto' else a.visibility,z_tolerance=0.0008 if a.z_tolerance is None else a.z_tolerance,feature_angle=40 if a.feature_angle is None else a.feature_angle,enable_source_colors=percell,fallback_color=c64_color_index(color),height=192,max_frames=MAX_SCENE_FRAMES,max_visible_runs=65535)
    crt,_=assemble_scene(cli.ROOT,frames,scene,tass=tass,cartconv=cartconv,outdir=outdir,stem=stem,hud_text=a.hud_text or scene.name[:31],frame_ticks=a.frame_ticks,tass_args=a.tass_args or (),colors=percell,color_index=c64_color_index(color),intro=a.intro,text_overlay=a.text_overlay,ending=a.ending)
    if a.run:
        vice=cli.resolve_executable(a.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        subprocess.run([vice,*a.vice_args,'-cartcrt',str(crt)],cwd=cli.ROOT,check=False)
    return 0
