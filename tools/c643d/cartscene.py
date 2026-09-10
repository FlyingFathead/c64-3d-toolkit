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


def pack_scene_frames(frames, colors=True, *, aliases=None, encoder=frame_block, direct_bytes=False):
    if not 1 <= len(frames) <= MAX_SCENE_FRAMES:
        raise ValueError(f'scene stream requires 1..{MAX_SCENE_FRAMES} frames')
    image=new_easyflash_image()
    # Keep the original 3-bank RAM bootstrap and reserve ROMH 0..2.
    placements=[(chip,bank) for chip in ('roml','romh') for bank in range(3,64)]
    place=offset=0; directory=[]
    for i,frame in enumerate(frames):
        if aliases is not None and aliases[i] != i:
            directory.append(dict(directory[aliases[i]], frame=i, reference_frame=aliases[i]))
            continue
        block,meta=encoder(frame,colors)
        if offset+len(block)>8192:
            place+=1; offset=0
        if place>=len(placements):
            raise ValueError(f'EasyFlash capacity exhausted at scene frame {i}; increase sample-step or reduce detail')
        chip,bank=placements[place]; address=(0x8000 if chip=='roml' else 0xa000)+offset
        start=easyflash_offset(bank,chip,offset)
        image[start:start+len(block)]=block
        directory.append(dict(frame=i,chip=chip,bank=bank,address=address,bytes=len(block),metadata_bytes=meta,runs=len(frame.records),sha256=hashlib.sha256(block).hexdigest()))
        if encoder is not frame_block:
            directory[-1]["encoding"] = "byte-spans" if block[meta+1] & 128 else "vectors"
        offset+=len(block)
    for page in range((len(frames)+255)//256):
        records=directory[page*256:(page+1)*256]
        values=[
            [d['bank'] for d in records], [d['address']&255 for d in records],
            [d['address']>>8 for d in records], [d['bytes']&255 for d in records],
            [(d['bytes']>>8) | (0x80 if direct_bytes and d.get('encoding') == 'byte-spans' else 0) for d in records], [d['metadata_bytes']&255 for d in records],
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


def assemble_scene(root,frames,scene,*,tass,cartconv,outdir,stem,hud_text,frame_ticks=4,tass_args=(),colors=True,color_index=1,intro=False,text_overlay=True,ending=False,renderer=RENDERER,optimize=True,prefer="fps",output_fps=None):
    from .renderer_names import implementation
    renderer=implementation(renderer)
    if renderer not in (RENDERER, "yunroll-cart-v5-scene", "yunroll-cart-v6-scene", "yunroll-cart-v7-scene", "yunroll-cart-v8-scene", "yunroll-cart-v9-scene", "yunroll-cart-v10-scene"):
        raise ValueError("unsupported scene renderer")
    variant = renderer.split("-")[-2]
    if not 1<=frame_ticks<=255:
        raise ValueError('--frame-ticks must be 1..255 PAL raster ticks')
    if ending and not intro:raise ValueError('--ending requires --intro')
    hud_text=validate_hud(hud_text)
    root=Path(root);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    work=root/'build'/f'{stem}-stream-scene';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
    # Keep the expensive compilation checkpoint even if ROM packing fails.
    (work/'oracle.json').write_text(json.dumps([asdict(f) for f in frames]))
    optimization = None
    if variant in ("v5", "v6", "v7", "v8", "v9", "v10") and optimize:
        from .optimize import optimize_frames
        frames, optimization = optimize_frames(frames, color_index<<4)
    joining = None
    if variant in ("v7", "v8", "v9", "v10") and optimize:
        from .runjoin import join_frames
        frames, joining = join_frames(frames)
    clearing = None
    if variant in ("v7", "v8", "v9", "v10") and optimize:
        from .clearplan import selective_clear_frames
        frames, clearing = selective_clear_frames(frames)
    encoder = frame_block
    if variant in ("v8", "v9", "v10"):
        from .bytespan import frame_block as encoder
        if variant == 'v10':
            from .bytespan_v10 import frame_block as encoder
    image,directory=pack_scene_frames(frames,colors,aliases=optimization["picture_references"] if optimization else None,encoder=encoder,direct_bytes=variant in ("v9", "v10"))
    # Reuse the established LUT emitter with a full-size RAM directory page.
    dummy=[dict(bank=0,address=0,bytes=0,metadata_bytes=0)]*256
    emit_directory(gen/'tables.inc',dummy)
    raw_hud=bitmap_text(hud_text)
    (gen/'hud.inc').write_text(f'; {hud_text}\nHUD_STATIC_LEN = {len(raw_hud)}\nhud_static_bitmap:\n'+'\n'.join(bytes_lines(raw_hud))+'\nhud_static_bitmap_end:\n')
    shutil.copyfile(root/f'c64/cart/easyflash-stream-{variant}-scene-helper.asm',gen/f'cart-{variant}-scene-helper.inc')
    src=(root/f'c64/renderer-{renderer}.asm').read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(frames)}\nFRAME_TICKS = {frame_ticks}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(colors)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${color_index:X}0',1)
    if not text_overlay:
        src=src.replace('        jsr init_static_hud','').replace('        jsr init_fps_label','').replace('        jsr maybe_update_fps','')
    if intro:
        from .cartintro import emit_intro
        emit_intro(gen/'intro.inc',ending=ending,build_identity=(__version__, ('hors-render-v1' if variant == 'v10' else f'yunroll-{variant}')+(' (ram)' if prefer == 'ram' else '')) if variant in ('v5', 'v6', 'v7', 'v8', 'v9', 'v10') else None)
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
    if optimization:
        src=src.replace('V5_REUSE_ENABLED = 0', f'V5_REUSE_ENABLED = {int(optimization["duplicate_pictures"] > 0)}')
    from .preferences import apply_preference
    src=apply_preference(src,renderer,prefer)
    if variant in ("v8", "v9", "v10"):
        from .bytespan import configure_source
        src = configure_source(src.replace('V9_BYTE_SPANS', 'V8_BYTE_SPANS'), directory).replace('V8_BYTE_SPANS', 'V9_BYTE_SPANS') if variant in ('v9', 'v10') else configure_source(src, directory)
    if output_fps is not None:
        if variant != 'v10' or not 1 <= output_fps <= 50:
            raise ValueError('output FPS requires V10 and a rate from 1..50')
        base,rem=divmod(50,output_fps)
        if rem:
            src=src.replace('        lda #FRAME_TICKS','        jsr v10_next_hold')
            src=src.replace('        sta scene_hold', '        sta scene_hold\n        sta v10_hold_phase',1)
            src+=f"\nv10_next_hold:\n        lda v10_hold_phase\n        clc\n        adc #{rem}\n        cmp #{output_fps}\n        bcc v10_short_hold\n        sbc #{output_fps}\n        sta v10_hold_phase\n        lda #{base+1}\n        rts\nv10_short_hold:\n        sta v10_hold_phase\n        lda #{base}\n        rts\nv10_hold_phase: .byte 0\n"
    asm=work/'main.asm';asm.write_text(src)
    ram=work/'runtime.prg';labels=outdir/f'{stem}.lbl'
    subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(labels),'-o',str(ram),str(asm)],check=True,cwd=root)
    blob=ram.read_bytes();load=int.from_bytes(blob[:2],'little');end=load+len(blob)-2
    if load!=0x0801 or end>(0x9c00 if variant in ("v5", "v6", "v7", "v8", "v9", "v10") else 0x9a00 if intro else 0x6000):
        raise ValueError('scene runtime outside bootstrap RAM destination')
    padded=bytearray(0x5800);runtime_end=min(end,0x6000)
    padded[load-0x0800:runtime_end-0x0800]=blob[2:2+runtime_end-load]
    for bank in range(3):
        put_easyflash_chip(image,bank,'roml',bytes(padded[bank*8192:(bank+1)*8192]).ljust(8192,b'\0'))
    boot=work/'boot.bin'
    subprocess.run([tass,*tass_args,'--nostart','-o',str(boot),str(root/f'c64/cart/easyflash-stream-{variant}-scene-boot.asm')],check=True,cwd=root)
    boot_blob=bytearray(boot.read_bytes())
    if intro or variant in ("v5", "v6", "v7", "v8", "v9", "v10"):
        intro_bytes=blob[2+0x8000-load:2+end-load]
        boot_blob[0x400:0x400+len(intro_bytes)]=intro_bytes
    put_easyflash_chip(image,0,'romh',bytes(boot_blob))
    raw=work/f'{stem}.bin';raw.write_bytes(image)
    crt=outdir/f'{stem}.crt';convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name=scene.name.replace('_',' ')[:32],cwd=root)
    check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=root)
    manifest=dict(format='c643d-easyflash-stream-scene',version=1,toolkit_version=__version__,renderer=renderer,name=scene.name,frames=len(frames),vertices=len(scene.mesh.vertices),edges=len(scene.mesh.edges),faces=len(scene.mesh.faces),colors=colors,screen_color=color_index<<4,hud_text=hud_text,text_overlay=text_overlay,intro=intro,ending=ending,frame_index_bits=16,frame_ticks=frame_ticks,target_fps=50/frame_ticks,target_duration_seconds=len(frames)*frame_ticks/50,source_fps=scene.source_fps,sample_step=scene.sample_step,source_frames=[f.source_frame for f in scene.frames],directory_ram_bytes=1792,directory_rom_bytes=((len(frames)+255)//256)*1792,frame_buffer_bytes=8192,metadata_cache_bytes=3072,rom_frame_bytes=sum(d['bytes'] for d in directory if 'reference_frame' not in d),data_bank_capacity_bytes=122*8192,run_count_bits=16,frame_data=directory)
    if optimization:
        manifest['optimization']=optimization
        if intro: manifest['build_screen']=dict(version=__version__,renderer=('hors-render-v1' if variant == 'v10' else f'yunroll-{variant}')+(' (ram)' if prefer == 'ram' else ''),ticks=None if variant == 'v10' else 150,skip_key='SPACE',wait_for_space=variant == 'v10')
    if clearing: manifest['clearing']=clearing
    if joining: manifest['joining']=joining
    if output_fps is not None:
        manifest.update(target_fps=output_fps,target_duration_seconds=len(frames)/output_fps,output_fps=output_fps,hold_pattern='fractional PAL refresh accumulator' if 50%output_fps else 'fixed PAL refresh interval')
    if variant in ('v7', 'v8', 'v9', 'v10'): manifest['preference']=prefer
    if variant in ("v8", "v9", "v10"):
        manifest["wire_format"] = ("v10-byte-first-direct-spans" if variant == "v10" else "v9-direct-byte-spans-v8-payload" if variant == "v9" else "v8-adaptive-vectors-byte-spans")
        manifest["byte_span_frames"] = sum(d.get("encoding") == "byte-spans" for d in directory)
    (outdir/f'{stem}-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'built {crt}\n{len(frames)} frames; {manifest["rom_frame_bytes"]} encoded payload bytes; target {manifest["target_duration_seconds"]:.2f}s at {manifest["target_fps"]:g} FPS',flush=True)
    return crt,manifest


def cmd_build_cart_scene(a):
    from . import cli
    from .blender import export_blend_scene
    from .sceneio import load_scene
    from .pipeline import build_scene_frames
    from .colors import c64_color_index
    rate=getattr(a,'blender_output_fps',None)
    if rate is not None:
        if not a.blend or a.renderer != 'yunroll-cart-v10-scene' or not 1<=rate<=50 or a.sample_step!=1:
            raise ValueError('--blender-output-fps requires V10, baked --blend, rate 1..50 and --sample-step 1')
        a.frame_ticks=50//rate
        print(f'Blender output FPS: {rate}; V10 PAL playback target: {rate} FPS (measured FPS may be lower)',flush=True)
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
    stem=a.output or Path(a.blend or a.scene).stem+'-'+getattr(a,'public_renderer',a.renderer)+('-ram' if getattr(a,'prefer','fps') == 'ram' else '')
    if not cli._check_overwrite([outdir/f'{stem}{suffix}' for suffix in ('.crt','.lbl','-manifest.json')],a.overwrite_policy):return 2
    if getattr(a,'public_renderer',None)=='hors-render-v1':a.public_renderer='hors-render-v1-scene'
    if a.blend:
        export=cli.BUILD/f'{stem}.c643dscene'
        export_blend_scene(a.blend,export,blender=a.blender,frame_start=a.frame_start,frame_end=a.frame_end,sample_step=a.sample_step,root=cli.ROOT,viewport_height=192,max_frames=MAX_SCENE_FRAMES,output_fps=rate)
    else:export=Path(a.scene)
    scene=load_scene(export)
    color,_,percell=cli._scene_color_policy(scene.mesh,a)
    print(f'compiling {len(scene.frames)} authored scene samples with {a.renderer} kernels...',flush=True)
    frames,_=build_scene_frames(scene,visibility_mode='surface' if a.visibility=='auto' else a.visibility,z_tolerance=0.0008 if a.z_tolerance is None else a.z_tolerance,feature_angle=40 if a.feature_angle is None else a.feature_angle,enable_source_colors=percell,fallback_color=c64_color_index(color),height=192,max_frames=MAX_SCENE_FRAMES,max_visible_runs=65535)
    builder=assemble_scene
    beta_options={}
    if getattr(a,'public_renderer','').startswith('hors-render-v2-beta1'):
        from .hors_v2 import assemble_scene as builder
        beta_options=dict(draw_gap=getattr(a,'v2_draw_gap',6),batch_budget=getattr(a,'v2_batch_budget',2048))
    if getattr(a,'public_renderer','') in ('hors-render-v2','hors-render-v2-scene'):
        from .hors_v2_stable import assemble_scene as builder
        beta_options=dict(draw_gap=getattr(a,'v2_draw_gap',6),batch_budget=getattr(a,'v2_batch_budget',2048))
    crt,_=builder(cli.ROOT,frames,scene,tass=tass,cartconv=cartconv,outdir=outdir,stem=stem,hud_text=a.hud_text or scene.name[:31],frame_ticks=a.frame_ticks,tass_args=a.tass_args or (),colors=percell,color_index=c64_color_index(color),intro=a.intro,text_overlay=a.text_overlay,ending=a.ending,renderer=a.renderer,prefer=getattr(a,"prefer","fps"),output_fps=rate,**beta_options)
    if a.run:
        vice=cli.resolve_executable(a.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        subprocess.run([vice,*a.vice_args,'-cartcrt',str(crt)],cwd=cli.ROOT,check=False)
    return 0
