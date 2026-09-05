"""Uniform-renderer comparison cartridges; canonical vector data, banked frames."""
from pathlib import Path
from dataclasses import dataclass,asdict
import hashlib,json,subprocess
from .cartstream import frame_block,emit_directory
from .cartridge import (new_easyflash_image,easyflash_offset,pack_demo_prgs,
    write_demo_include,assemble_demo_control,assemble_demo_boot,install_demo_boot,
    build_menu_charset,convert_easyflash,check_easyflash_crt)
from .emit import bytes_lines
from .prgframes import extract

@dataclass
class Demo:
    name:str
    frames:list
    colors:bool
    screen:int
    hud:bytes
    source:str
    source_sha256:str


def demos(root):
    from . import cli
    from .pipeline import Camera,fit_scale,build_frames
    from .mesh import transform_mesh
    from .colors import c64_color_index
    from .toolchain import load_toolchain_settings
    out=[]
    for title,path in cli.CARTRIDGE_DEMO_ENTRIES:
        frames,colors,screen,hud,_=extract(path)
        out.append(Demo(title,frames,colors,screen,hud,path.relative_to(root).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest()))
    parser=cli.make_parser(load_toolchain_settings(root/'config/c643d.ini'))
    for name in ('horse_head_hifi','sunflower_torus_hifi'):
        a=parser.parse_args(['build','--object',name,'--frames','128'])
        mesh,label,axis,vis,ztol,angle,color,source,percell,anim,tilt,travel,rise=cli.build_mesh(a)
        cam=Camera(distance=a.camera,focal=a.focal,cx=128,cy=96)
        fit=fit_scale(mesh,128,cam,margin=a.margin,max_scale=a.max_fit_scale,spin_axis=axis,height=192)
        mesh=transform_mesh(mesh,scale=fit)
        print(f'compiling comparison source {label}: 128 frames',flush=True)
        fs,_=build_frames(mesh,128,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=angle,enable_source_colors=percell,fallback_color=c64_color_index(color),height=192,max_visible_runs=65535)
        from .font import bitmap_text
        hud=bytes(bitmap_text(f'{label} V:{len(mesh.vertices):03d} E:{len(mesh.edges):03d}',31))
        path=root/'objects'/f'{name}.obj'
        out.append(Demo(label,fs,percell,c64_color_index(color)<<4,hud,path.relative_to(root).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest()))
    return out


def prepare(root,renderer,tass,tass_args=()):
    if renderer not in ('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4'):raise ValueError('unsupported uniform renderer')
    root=Path(root);variant=renderer.rsplit('-',1)[1];out=root/f'build/uniform-{variant}';out.mkdir(parents=True,exist_ok=True)
    sources=demos(root)
    # Each RAM bootstrap fits in three ROML banks. ROMH 0=boot, 1=menus,
    # 2=menu directory/helpers. Remaining chips form a common frame-data pool.
    first_free_roml=1+3*len(sources)
    if first_free_roml>64:raise ValueError('too many three-bank runtime entries')
    arenas=[(b,'romh') for b in range(3,64)]+[(b,'roml') for b in range(first_free_roml,64)]
    image=new_easyflash_image();slot=offset=0;entries=[];info=[]
    for index,demo in enumerate(sources):
        directory=[]
        for fi,f in enumerate(demo.frames):
            block,meta=frame_block(f,demo.colors)
            if offset+len(block)>8192:slot+=1;offset=0
            if slot>=len(arenas):raise ValueError('uniform demo frames exceed EasyFlash capacity; samples were not reduced')
            bank,chip=arenas[slot];addr=(0x8000 if chip=='roml' else 0xa000)+offset
            pos=easyflash_offset(bank,chip,offset);image[pos:pos+len(block)]=block
            directory.append(dict(frame=fi,bank=bank,chip=chip,address=addr,bytes=len(block),metadata_bytes=meta,runs=len(f.records),sha256=hashlib.sha256(block).hexdigest()))
            offset+=len(block)
        work=out/f'{index:02d}';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
        emit_directory(gen/'tables.inc',directory)
        (gen/'hud.inc').write_text(f'HUD_STATIC_LEN = {len(demo.hud)}\nhud_static_bitmap:\n'+'\n'.join(bytes_lines(demo.hud))+'\nhud_static_bitmap_end:\n')
        helper=(root/f'c64/cart/easyflash-stream-{variant}-helper.asm').read_text()
        needle='        lda cart_source_hi,x\n        sta STREAM_HI'
        helper=helper.replace(needle,needle+'\n        cmp #$a0\n        lda #$06\n        adc #0\n        sta cart_selected_mode',1)
        helper=helper.replace('        lda #$06\n        sta $de02','        lda cart_selected_mode\n        sta $de02')
        helper=helper.replace('cart_cache_hi:', 'cart_selected_mode: .byte 0\ncart_cache_hi:')
        (gen/f'cart-{variant}-helper.inc').write_text(helper)
        src=(root/f'c64/renderer-{renderer}.asm').read_text().replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(demo.frames)}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(demo.colors)}',1).replace('SCREEN_COLOR = $10',f'SCREEN_COLOR = ${demo.screen:02x}',1)
        src=src.replace('        .include "generated/hud.inc"','        .include "generated/hud.inc"\n.if * > $1700\n.error "renderer/HUD overlaps LUT"\n.endif')
        asm=work/'main.asm';asm.write_text(src);prg=work/'runtime.prg'
        subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(work/'runtime.lbl'),'-o',str(prg),str(asm)],check=True,cwd=root,stdout=subprocess.DEVNULL)
        blob=prg.read_bytes();load=int.from_bytes(blob[:2],'little')
        if load!=0x0801 or len(blob)-2>3*8192 or load+len(blob)-2>0x5000:raise ValueError('uniform runtime exceeds three-bank RAM layout')
        # Fixed three-bank reservation gives every version identical frame addresses.
        entries.append((demo.name,prg))
        (work/'oracle.json').write_text(json.dumps([asdict(f) for f in demo.frames]))
        info.append(dict(name=demo.name,renderer=renderer,frames=len(demo.frames),colors=demo.colors,screen_color=demo.screen,source=demo.source,source_sha256=demo.source_sha256,work=work.relative_to(root).as_posix(),rom_frame_bytes=sum(x['bytes'] for x in directory),frame_data=directory))
    return entries,image,info,arenas[:slot+1],first_free_roml


def build(a):
    from . import cli,__version__
    tass=cli.resolve_executable(a.tass,'tass');cartconv=cli.require_cartconv(a.cartconv,verbose=True)
    if not tass or not cartconv:raise ValueError('64tass and cartconv are required')
    renderer=a.stream_renderer;variant=renderer.rsplit('-',1)[1]
    root=cli.ROOT;out=Path(a.output_dir).resolve() if a.output_dir else cli.CART_DEMOS;out.mkdir(parents=True,exist_ok=True)
    stem=a.output or f'c643d-demo-v{__version__}-{renderer}-all'
    paths=[out/f'{stem}{s}' for s in ('.crt','-cart-manifest.json','-cart-map.txt')]
    if not cli._check_overwrite(paths,a.overwrite_policy):return 2
    entries,frame_image,stream_info,used,first_free=prepare(root,renderer,tass,a.tass_args or ())
    image,plans,manifest=pack_demo_prgs(entries,source_root=root)
    if any(p.banks!=3 for p in plans) or manifest['highest_bank_used']!=first_free-1:raise ValueError('runtime bank reservation differs from planned frame pool')
    for b,chip in used:
        pos=easyflash_offset(b,chip);image[pos:pos+8192]=frame_image[pos:pos+8192]
    work=root/'build'/f'{stem}-cartridge-demo';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
    write_demo_include(gen/'cart-demo-data.inc',plans)
    runtimes={};shared={}
    for i,style in enumerate(cli.DEMO_MENU_STYLE_ORDER):
        binpath=work/f'{stem}-runtime-{style}.bin';whole=work/f'{stem}-menu-{style}-whole.bin'
        subprocess.run([tass,*(a.tass_args or ()),'-I',str(gen),'-D','VICE_DEBUGCART=0','-D','AUTO_LAUNCH=255','-D',f'MENU_STYLE={i}','-D',f'RENDERER_VERSION={int(variant[1:])}','-b','--vice-labels','-l',str(work/f'{stem}-runtime-{style}.lbl'),'-L',str(work/f'{stem}-runtime-{style}.lst'),'-o',str(whole),str(root/'c64/cart/easyflash-demo-scroll-runtime.asm')],check=True,cwd=root,stdout=subprocess.DEVNULL)
        data=whole.read_bytes()
        if len(data)!=4096:raise ValueError('scroll menu must occupy $c000-$cfff')
        shared[style]=data[:2048];binpath.write_bytes(data[2048:]);runtimes[style]=binpath
    control=work/f'{stem}-control.bin';boot=work/f'{stem}-romh0.bin';font=work/f'{stem}-menu-font.bin';font.write_bytes(build_menu_charset())
    assemble_demo_control(tass=tass,tass_args=a.tass_args or (),source=cli.CART/'easyflash-demo-control.asm',output=control,labels=work/f'{stem}-control.lbl',listing=work/f'{stem}-control.lst',cwd=root)
    assemble_demo_boot(tass=tass,tass_args=a.tass_args or (),source=cli.CART/'easyflash-demo-boot.asm',output=boot,labels=work/f'{stem}-boot.lbl',listing=work/f'{stem}-boot.lst',cwd=root)
    install_demo_boot(image,boot.read_bytes(),runtimes[a.menu_style].read_bytes(),control=control.read_bytes(),style_runtimes=[runtimes[s].read_bytes() for s in cli.DEMO_MENU_STYLE_ORDER],menu_font=font.read_bytes())
    for i,style in enumerate(cli.DEMO_MENU_STYLE_ORDER):
        pos=easyflash_offset(2,'romh',i*2048);image[pos:pos+2048]=shared[style]
    manifest.update(version=__version__,stream_renderer=renderer,uniform_renderer=True,streamed_entries=stream_info,menu_style=a.menu_style,menu_styles=list(cli.DEMO_MENU_STYLE_ORDER),menu_visible_rows=10,frame_chips_used=[dict(bank=b,chip=c) for b,c in used],note='Every entry uses the selected stream renderer. Canonical PRG vector tables preserve original sampling; HiFi uses 128 orientations.')
    manifest.update(runtime_data_banks_used=first_free-1,highest_runtime_bank_used=first_free-1,
        highest_bank_used=max([first_free-1]+[bank for bank,chip in used]),
        data_banks_used=len(set(range(1,first_free))|{bank for bank,chip in used}),
        shared_menu_load='$c000',shared_menu_size=2048)
    raw=work/f'{stem}.bin';raw.write_bytes(image);crt=out/f'{stem}.crt'
    convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name=f'C643D {__version__} ALL {variant.upper()}',cwd=root);check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=root)
    (out/f'{stem}-cart-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/f'{stem}-cart-map.txt').write_text('Uniform '+renderer+' cartridge\nBank 0: boot/control/font; ROMH 1: menus; ROMH 2: menu directory/helpers\n'+''.join(f'{x["name"]}: {x["frames"]} frames, {x["rom_frame_bytes"]} stream bytes\n' for x in stream_info)+'Frame chips: '+', '.join(f'{b}:{c}' for b,c in used)+'\n')
    print(f'built {crt}\nall {len(plans)} entries: {renderer}; 10-row scrolling menu; {sum(x["rom_frame_bytes"] for x in stream_info)} frame bytes',flush=True)
    if a.run:
        vice=cli.resolve_executable(a.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        subprocess.run([vice,*(a.vice_args or ()),'-cartcrt',str(crt)],check=False,cwd=root)
    return 0
