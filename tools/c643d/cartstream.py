"""Independent yunroll-cart-v2 single-frame EasyFlash streamer.

ROML banks 0..2: boot-time RAM image. Bank 0 ROMH: native reset.
ROML banks 3..63: complete bank-contained frames, no all-frame RAM tables.
The frame directory (7 bytes/frame) stays in $4800-$4eff. The current frame
uses $a000-$bfff; three <=1KiB clear/colour caches use $5000-$5bff.
"""
from __future__ import annotations
import hashlib,json,shutil,subprocess
from pathlib import Path
from .cartridge import new_easyflash_image, easyflash_offset, put_easyflash_chip, convert_easyflash, check_easyflash_crt
from .emit import bytes_lines,emit_hud
from .pipeline import build_xchunk_tables

MAX_FRAMES=255
FIRST_DATA_BANK=3
FRAME_CAP=8192
META_CAP=1024

def frame_block(frame,colors=True):
    if len(frame.clear_spans)>255 or len(frame.color_spans)>255:
        raise ValueError('V2 clear/colour span counters remain 8-bit (maximum 255 each)')
    if len(frame.records)>65535:raise ValueError('V2 visible-run counter exceeds 65535')
    meta=bytearray([len(frame.clear_spans)])
    for s in frame.clear_spans:meta.extend(s)
    if colors:
        meta.append(len(frame.color_spans))
        for s in frame.color_spans:meta.extend(s)
    if len(meta)>META_CAP:raise ValueError(f'frame metadata {len(meta)} exceeds {META_CAP}-byte per-slot cache')
    block=meta+len(frame.records).to_bytes(2,'little')
    for rec in frame.records:block.extend(rec)
    if len(block)>FRAME_CAP:raise ValueError(f'frame block {len(block)} exceeds {FRAME_CAP}-byte staging buffer')
    return bytes(block),len(meta)

def pack_frames(frames,colors=True,*,chip="roml",first_bank=FIRST_DATA_BANK):
    if not 1<=len(frames)<=MAX_FRAMES:raise ValueError('V2 currently supports 1..255 frames per cartridge')
    image=new_easyflash_image();bank=first_bank;offset=0;directory=[]
    if chip not in ("roml","romh") or not 0<=first_bank<64:raise ValueError("invalid cartridge data placement")
    base=0x8000 if chip=="roml" else 0xa000
    for i,frame in enumerate(frames):
        block,meta=frame_block(frame,colors)
        if offset+len(block)>FRAME_CAP:bank+=1;offset=0
        if bank>=64:raise ValueError('EasyFlash ROML capacity exceeded; reduce frame count or detail')
        start=easyflash_offset(bank,chip,offset);image[start:start+len(block)]=block
        directory.append(dict(frame=i,bank=bank,address=base+offset,bytes=len(block),metadata_bytes=meta,runs=len(frame.records),sha256=hashlib.sha256(block).hexdigest()))
        offset+=len(block)
    return image,directory

def emit_directory(path,directory):
    lines=['; Generated cart-v2 LUT and directory. No complete animation in RAM.','* = $1700','xchunk_levels:']
    levels,masks=build_xchunk_tables();lines+=bytes_lines(levels)
    for i,table in enumerate(masks):lines += [f'* = ${0x1800+i*256:04x}',f'xchunk_mask{i}:']+bytes_lines(table)
    lines += ['.if * > $2000','.error "LUT overlaps bitmap"','.endif','* = $4800']
    arrays={
        'cart_bank':[d['bank'] for d in directory],
        'cart_source_lo':[d['address']&255 for d in directory],
        'cart_source_hi':[d['address']>>8 for d in directory],
        'cart_length_lo':[d['bytes']&255 for d in directory],
        'cart_length_hi':[d['bytes']>>8 for d in directory],
        'cart_meta_lo':[d['metadata_bytes']&255 for d in directory],
        'cart_meta_hi':[d['metadata_bytes']>>8 for d in directory],
    }
    for name,values in arrays.items():lines += [name+':']+bytes_lines(values)
    lines += ['.if * > $5000','.error "directory overlaps metadata cache"','.endif']
    path.write_text('\n'.join(lines)+'\n')

def assemble_cartridge(root,frames,mesh,*,tass,cartconv,outdir,stem,tass_args=(),color_index=1,colors=True,renderer="yunroll-cart-v2"):
    if renderer not in ('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4'):raise ValueError('unsupported stream renderer')
    variant=renderer.rsplit('-',1)[1]
    root=Path(root);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    work=root/'build'/f'{stem}-stream-{variant}';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
    image,directory=pack_frames(frames,colors)
    emit_directory(gen/'tables.inc',directory)
    emit_hud(gen/'hud.inc',mesh.name,len(mesh.vertices),len(mesh.edges))
    shutil.copyfile(root/f'c64/cart/easyflash-stream-{variant}-helper.asm',gen/f'cart-{variant}-helper.inc')
    src=(root/f'c64/renderer-{renderer}.asm').read_text()
    src=src.replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(frames)}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(colors)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${color_index:X}0',1)
    src=src.replace('        .include "generated/hud.inc"','        .include "generated/hud.inc"\n.if * > $1700\n.error "renderer and HUD overlap LUT"\n.endif')
    asm=work/'main.asm';asm.write_text(src)
    ram=work/'runtime.prg';labels=outdir/f'{stem}.lbl'
    subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(labels),'-o',str(ram),str(asm)],check=True,cwd=root)
    blob=ram.read_bytes();load=int.from_bytes(blob[:2],'little');end=load+len(blob)-2
    if load!=0x0801 or end>0x5000:raise ValueError('runtime outside bootstrap RAM destination')
    padded=bytearray(0x4800);padded[load-0x0800:end-0x0800]=blob[2:]
    for bank in range(3):put_easyflash_chip(image,bank,'roml',bytes(padded[bank*8192:(bank+1)*8192]).ljust(8192,b'\0'))
    boot=work/'boot.bin'
    subprocess.run([tass,*tass_args,'--nostart','-o',str(boot),str(root/'c64/cart/easyflash-stream-v2-boot.asm')],check=True,cwd=root)
    put_easyflash_chip(image,0,'romh',boot.read_bytes())
    raw=work/f'{stem}.bin';raw.write_bytes(image)
    crt=outdir/f'{stem}.crt';convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name=f'C643D STREAM {variant.upper()}',cwd=root)
    check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=root)
    manifest=dict(format='c643d-easyflash-stream-v2',version=1,renderer=renderer,name=mesh.name,frames=len(frames),vertices=len(mesh.vertices),edges=len(mesh.edges),faces=len(mesh.faces),colors=colors,screen_color=color_index<<4,directory_ram_bytes=len(frames)*7,frame_buffer_bytes=FRAME_CAP,metadata_cache_bytes=3*META_CAP,rom_frame_bytes=sum(d['bytes'] for d in directory),highest_bank=max(d['bank'] for d in directory),run_count_bits=16,frame_data=directory)
    (outdir/f'{stem}-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Retain a reproducible host oracle for emulator comparison, outside final outputs.
    from dataclasses import asdict
    (work/'oracle.json').write_text(json.dumps([asdict(f) for f in frames]))
    print(f'built {crt}\nframes: {len(frames)}; visible runs {min(d["runs"] for d in directory)}..{max(d["runs"] for d in directory)}\nROM frame data: {manifest["rom_frame_bytes"]} bytes; directory RAM: {len(frames)*7} bytes; fixed frame/cache RAM: 11264 bytes\nROML data banks: {FIRST_DATA_BANK}..{manifest["highest_bank"]}',flush=True)
    return crt,manifest

def cmd_build_cart_v2(a):
    from . import cli
    from .pipeline import Camera,fit_scale,build_frames
    from .mesh import transform_mesh
    from .colors import c64_color_index
    if a.blend or a.scene:
        raise ValueError('V2 currently accepts generated spins and OBJ/SVG presets; scene-stream support is a later extension')
    if not a.text_overlay or a.rastertime_profiler:
        raise ValueError('V2 currently uses the standard HUD; no-overlay/profiler variants are not implemented')
    tass=cli.resolve_executable(a.tass,'tass');cartconv=cli.require_cartconv(a.cartconv,verbose=True)
    if not tass or not cartconv:return 2
    mesh,label,axis,vis,ztol,angle,color,source,percell,anim,tilt,travel,rise=cli.build_mesh(a)
    n=a.frames if a.frames is not None else 192
    if not 1<=n<=MAX_FRAMES:raise ValueError('V2 requires 1..255 frames')
    height=cli._viewport_height(a)
    if height!=192:raise ValueError('V2 currently requires a 192-line viewport with the standard HUD')
    cam=Camera(distance=a.camera,focal=a.focal,cx=128,cy=96)
    scale=fit_scale(mesh,n,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=axis,animation=anim,animation_tilt=tilt,animation_travel=travel,animation_rise=rise,height=height) if not a.no_auto_fit else 1
    mesh=transform_mesh(mesh,scale=scale)
    print(f'compiling {label}: {n} streamed frames, fit {scale:.4f}',flush=True)
    frames,_=build_frames(mesh,n,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=angle,animation=anim,animation_tilt=tilt,animation_travel=travel,animation_rise=rise,enable_source_colors=percell,fallback_color=c64_color_index(color),height=height,max_visible_runs=65535)
    outdir=Path(a.output_dir).resolve() if a.output_dir else cli.BUILD
    stem=a.output or label.lower().replace(' ','_')+'-'+a.renderer
    if not cli._check_overwrite([outdir/f'{stem}.crt',outdir/f'{stem}.lbl',outdir/f'{stem}-manifest.json'],a.overwrite_policy):return 2
    crt,_=assemble_cartridge(cli.ROOT,frames,mesh,tass=tass,cartconv=cartconv,outdir=outdir,stem=stem,tass_args=a.tass_args,color_index=c64_color_index(color),colors=percell,renderer=a.renderer)
    if a.run:
        vice=cli.resolve_executable(a.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        subprocess.run([vice,*a.vice_args,'-cartcrt',str(crt)],check=False,cwd=cli.ROOT)
    return 0


def prepare_menu_streams(root,*,tass,cartconv,tass_args=(),renderer="yunroll-cart-v2"):
    """Build two 128-frame menu entries, with frame records in ROMH banks 2+.

    Existing menu boot/style ROMH banks 0 and 1 remain reserved. Only each
    streamer's RAM bootstrap PRG is fed to the established ROML PRG packer.
    It applies the normal menu-return IRQ shim to these new entries too.
    """
    import math
    from . import cli
    from .toolchain import load_toolchain_settings
    from .pipeline import Camera,fit_scale,build_frames
    from .mesh import transform_mesh
    from .colors import c64_color_index
    if renderer not in ('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4'):raise ValueError('unsupported stream renderer')
    variant=renderer.rsplit('-',1)[1]
    root=Path(root);out=root/f'build/menu-stream-{variant}';out.mkdir(parents=True,exist_ok=True)
    image=new_easyflash_image();entries=[];info=[];bank=2
    parser=cli.make_parser(load_toolchain_settings(root/'config/c643d.ini'))
    for name in ('horse_head_hifi','sunflower_torus_hifi'):
        a=parser.parse_args(['build','--object',name,'--frames','128'])
        mesh,label,axis,vis,ztol,angle,color,source,percell,anim,tilt,travel,rise=cli.build_mesh(a)
        cam=Camera(distance=a.camera,focal=a.focal,cx=128,cy=96)
        fitted=fit_scale(mesh,128,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=axis,height=192)
        mesh=transform_mesh(mesh,scale=fitted)
        print(f'compiling menu stream {label}: 128 frames',flush=True)
        frames,_=build_frames(mesh,128,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=angle,enable_source_colors=percell,fallback_color=c64_color_index(color),height=192,max_visible_runs=65535)
        part,directory=pack_frames(frames,percell,chip='romh',first_bank=bank)
        last=directory[-1]['bank']
        for b in range(bank,last+1):
            off=easyflash_offset(b,'romh');image[off:off+8192]=part[off:off+8192]
        work=out/name;gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
        emit_directory(gen/'tables.inc',directory);emit_hud(gen/'hud.inc',label,len(mesh.vertices),len(mesh.edges))
        # ROMH is visible at A000 in 16K mode. Writes to the same A000 window
        # go to underlying RAM; after hiding ROM the complete frame is readable.
        helper=(root/f'c64/cart/easyflash-stream-{variant}-helper.asm').read_text().replace('lda #$06\n        sta $de02','lda #$07\n        sta $de02')
        (gen/f'cart-{variant}-helper.inc').write_text(helper)
        src=(root/f'c64/renderer-{renderer}.asm').read_text().replace('FRAME_COUNT = 48','FRAME_COUNT = 128',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(percell)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${c64_color_index(color):X}0',1)
        src=src.replace('        .include "generated/hud.inc"','        .include "generated/hud.inc"\n.if * > $1700\n.error "renderer and HUD overlap LUT"\n.endif')
        asm=work/'main.asm';asm.write_text(src);prg=work/'runtime.prg'
        subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(work/'runtime.lbl'),'-o',str(prg),str(asm)],check=True,cwd=root)
        entries.append((label,prg))
        from dataclasses import asdict
        (work/'oracle.json').write_text(json.dumps([asdict(f) for f in frames]))
        info.append(dict(name=label,frames=128,chip='romh',first_bank=bank,last_bank=last,rom_frame_bytes=sum(d['bytes'] for d in directory),frame_data=directory,screen_color=c64_color_index(color)<<4))
        bank=last+1
    return entries,image,info
