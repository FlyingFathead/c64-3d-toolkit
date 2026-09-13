"""Uniform-renderer comparison cartridges; canonical vector data, banked frames."""
from pathlib import Path
from .cartlaunch import run as run_cartridge
from dataclasses import dataclass,asdict
import hashlib,json,subprocess
from .cartstream import frame_block,emit_directory
from .cartridge import (new_easyflash_image,easyflash_offset,pack_demo_prgs,
    write_demo_include,assemble_demo_control,assemble_demo_boot,install_demo_boot,
    build_menu_charset,convert_easyflash,check_easyflash_crt,cart_write_method)
from .emit import bytes_lines
from .prgframes import extract
from .colors import configure_asm_colors

@dataclass
class Demo:
    name:str
    frames:list
    colors:bool
    screen:int
    hud:bytes
    source:str
    source_sha256:str
    frame_ticks:int=1
    finite:bool=False
    show_hud:bool=True
    border:int=0
    interactive_colors:bool=False
    color_controls:bool=False


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


def prepare(root,renderer,tass,tass_args=(),sources=None,prefer="fps",work_prefix="uniform",frame_encoders=None,frame_pipeline=None,runtime_pipeline=None):
    from .renderer_names import implementation
    renderer=implementation(renderer)
    if renderer not in ('yunroll-cart-v2','yunroll-cart-v3','yunroll-cart-v4','yunroll-cart-v5','yunroll-cart-v6','yunroll-cart-v7', 'yunroll-cart-v8', 'yunroll-cart-v9', 'yunroll-cart-v10'):raise ValueError('unsupported uniform renderer')
    root=Path(root);variant=renderer.rsplit('-',1)[1];out=root/f'build/{work_prefix}-{variant}{"-ram" if prefer == "ram" else ""}';out.mkdir(parents=True,exist_ok=True)
    sources=demos(root) if sources is None else sources
    # Each RAM bootstrap fits in three ROML banks. ROMH 0=boot, 1=menus,
    # 2=menu directory/helpers. Remaining chips form a common frame-data pool.
    first_free_roml=1+3*len(sources)
    if first_free_roml>64:raise ValueError('too many three-bank runtime entries')
    arenas=[(b,'romh') for b in range(3,64)]+[(b,'roml') for b in range(first_free_roml,64)]
    image=new_easyflash_image();slot=offset=0;entries=[];info=[]
    for index,demo in enumerate(sources):
        optimization = None
        original_frames = demo.frames
        if variant in ("v5", "v6", "v7", "v8", "v9", "v10"):
            from .optimize import optimize_frames
            from dataclasses import replace
            frames, optimization = optimize_frames(demo.frames, demo.screen)
            demo = replace(demo, frames=frames)
        joining = None
        if variant in ("v7", "v8", "v9", "v10"):
            from .runjoin import join_frames
            from dataclasses import replace
            frames, joining = join_frames(demo.frames)
            demo = replace(demo, frames=frames)
        clearing = None
        if variant in ("v7", "v8", "v9", "v10"):
            from .clearplan import selective_clear_frames
            from dataclasses import replace
            frames, clearing = selective_clear_frames(demo.frames)
            demo = replace(demo, frames=frames)
        if frame_pipeline is not None:
            demo = frame_pipeline(demo)
        encoder = frame_block
        if variant in ("v8", "v9", "v10"):
            from .bytespan import frame_block as encoder
            if variant == 'v10':
                from .bytespan_v10 import frame_block as encoder
        if frame_encoders is not None:
            encoder = frame_encoders.get(demo.name, encoder)
        directory=[]
        for fi,f in enumerate(demo.frames):
            alias=optimization["picture_references"][fi] if optimization else fi
            if alias != fi:
                directory.append(dict(directory[alias],frame=fi,reference_frame=alias))
                continue
            block,meta=encoder(f,demo.colors)
            if offset+len(block)>8192:slot+=1;offset=0
            if slot>=len(arenas):raise ValueError('uniform demo frames exceed EasyFlash capacity; samples were not reduced')
            bank,chip=arenas[slot];addr=(0x8000 if chip=='roml' else 0xa000)+offset
            pos=easyflash_offset(bank,chip,offset);image[pos:pos+len(block)]=block
            directory.append(dict(frame=fi,bank=bank,chip=chip,address=addr,bytes=len(block),metadata_bytes=meta,runs=len(f.records),sha256=hashlib.sha256(block).hexdigest()))
            if encoder is not frame_block:
                directory[-1]["encoding"] = "byte-spans" if block[meta+1] & 128 else "vectors"
            offset+=len(block)
        work=out/f'{index:02d}';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
        emit_directory(gen/'tables.inc',directory,direct_bytes=variant in ('v9', 'v10'))
        (gen/'hud.inc').write_text(f'HUD_STATIC_LEN = {len(demo.hud)}\nhud_static_bitmap:\n'+'\n'.join(bytes_lines(demo.hud))+'\nhud_static_bitmap_end:\n')
        helper=(root/f'c64/cart/easyflash-stream-{variant}-helper.asm').read_text()
        needle='        lda cart_source_hi,x\n        sta STREAM_HI'
        helper=helper.replace(needle,needle+'\n        cmp #$a0\n        lda #$06\n        adc #0\n        sta cart_selected_mode',1)
        helper=helper.replace('        lda #$06\n        sta $de02','        lda cart_selected_mode\n        sta $de02')
        helper=helper.replace('cart_cache_hi:', 'cart_selected_mode: .byte 0\ncart_cache_hi:')
        (gen/f'cart-{variant}-helper.inc').write_text(helper)
        src=(root/f'c64/renderer-{renderer}.asm').read_text().replace('FRAME_COUNT = 48',f'FRAME_COUNT = {len(demo.frames)}',1).replace('COLORS_ENABLED = 0',f'COLORS_ENABLED = {int(demo.colors)}',1)
        src=configure_asm_colors(src,demo.screen>>4,demo.screen&15,demo.border)
        if demo.interactive_colors:
            from .colorcombos import configure_combo_runtime
            src=configure_combo_runtime(src)
        if demo.color_controls:
            from .demo_colors import configure_runtime
            src=configure_runtime(src,demo.border)
        src=src.replace('        .include "generated/hud.inc"','        .include "generated/hud.inc"\n.if * > $1700\n.error "renderer/HUD overlaps LUT"\n.endif')
        if optimization:
            src=src.replace('V5_REUSE_ENABLED = 0', f'V5_REUSE_ENABLED = {int(optimization["duplicate_pictures"] > 0)}')
        from .preferences import apply_preference
        src=apply_preference(src,renderer,prefer)
        if variant in ("v8", "v9", "v10"):
            from .bytespan import configure_source
            src = configure_source(src.replace('V9_BYTE_SPANS', 'V8_BYTE_SPANS'), directory).replace('V8_BYTE_SPANS', 'V9_BYTE_SPANS') if variant in ('v9', 'v10') else configure_source(src, directory)
        if demo.frame_ticks != 1 or demo.finite or not demo.show_hud:
            from .hifireel import configure_scene_runtime
            src = configure_scene_runtime(src, demo)
        if runtime_pipeline is not None:
            src = runtime_pipeline(src,demo)
        asm=work/'main.asm';asm.write_text(src);prg=work/'runtime.prg'
        subprocess.run([tass,*tass_args,'--cbm-prg','--vice-labels','-l',str(work/'runtime.lbl'),'-o',str(prg),str(asm)],check=True,cwd=root,stdout=subprocess.DEVNULL)
        blob=prg.read_bytes();load=int.from_bytes(blob[:2],'little')
        if load!=0x0801 or len(blob)-2>3*8192 or load+len(blob)-2>(0x6000 if variant in ("v5", "v6", "v7", "v8", "v9", "v10") else 0x5000):raise ValueError('uniform runtime exceeds three-bank RAM layout')
        # Fixed three-bank reservation gives every version identical frame addresses.
        entries.append((demo.name,prg))
        (work/'oracle.json').write_text(json.dumps([asdict(f) for f in original_frames]))
        info.append(dict(name=demo.name,renderer=renderer,frames=len(demo.frames),colors=demo.colors,screen_color=demo.screen,border_color=demo.border,source=demo.source,source_sha256=demo.source_sha256,work=work.relative_to(root).as_posix(),rom_frame_bytes=sum(x['bytes'] for x in directory if 'reference_frame' not in x),frame_data=directory))
        if demo.interactive_colors:info[-1]['interactive_colors']=dict(foreground_key='F3',background_key='F4 / SHIFT+F3',border_follows_background=True,reset_on_entry=True)
        if demo.color_controls:
            from .demo_colors import metadata
            info[-1]['color_controls']=metadata(not demo.colors)
        if optimization: info[-1]["optimization"]=optimization
        if clearing: info[-1]["clearing"]=clearing
        if joining: info[-1]["joining"]=joining
        if variant in ("v7", "v8", "v9", "v10"): info[-1]["preference"]=prefer
        if variant in ("v8", "v9", "v10"):
            info[-1]["wire_format"] = ("v10-byte-first-direct-spans" if variant == "v10" else "v9-direct-byte-spans-v8-payload" if variant == "v9" else "v8-adaptive-vectors-byte-spans")
            info[-1]["byte_span_frames"] = sum(d.get("encoding") == "byte-spans" for d in directory)
    return entries,image,info,arenas[:slot+1],first_free_roml


def default_output_dir(root, renderer):
    """Keep retired comparison methods out of the active demo folder."""
    folder = 'examples/old/cart_demos' if renderer in ('yunroll-cart-v2','yunroll-cart-v3') else 'examples/cart_demos'
    return Path(root) / folder



# ONLY use normal PLAY ALL for A/B comparisons between methods and versions.
# Use the same seconds value on both carts. F5 MUST NOT be used for benchmarking.
# These durations belong ONLY to F5 internal demo mode for exhibitions.
# F5 must never be used as the benchmark reference.
def play_all_durations(entries, seconds, renderer):
    """V8 F5 exhibition holds; normal PLAY ALL uses the uniform duration."""
    return [15 if renderer in ('yunroll-cart-v8', 'yunroll-cart-v9', 'yunroll-cart-v10') and seconds == 10 and
            entry['name'] in ('HORSE HEAD HIFI', 'SUNFLOWER TORUS HIFI') else seconds
            for entry in entries]


def build(a, *, sources=None, reel=False,frame_encoders=None):
    if a.stream_renderer == 'hors-render-v2':
        from .hors_v2_stable import build_menu
        return build_menu(a,sources=sources,reel=reel,frame_encoders=frame_encoders)
    print('fps locking: not set')
    from . import cli,__version__
    tass=cli.resolve_executable(a.tass,'tass');cartconv=cli.require_cartconv(a.cartconv,verbose=True)
    if not tass or not cartconv:raise ValueError('64tass and cartconv are required')
    from .renderer_names import implementation, public_name
    public_renderer=public_name(a.stream_renderer)
    renderer=implementation(a.stream_renderer);variant=renderer.rsplit('-',1)[1]
    legacy_cart=getattr(a,'legacy_cart',False)
    prefer=getattr(a,'prefer','fps')
    seconds=getattr(a,'play_all_seconds',10)
    color_combo=getattr(a,'color_combo_test',False)
    color_controls=bool(sources) and all(d.color_controls for d in sources)
    if not 1 <= seconds <= 255: raise ValueError('--play-all-seconds must be 1..255')
    if variant not in ('v7', 'v8', 'v9', 'v10') and seconds != 10: raise ValueError('--play-all-seconds requires V7, V8 or V9')
    if prefer == 'ram' and variant not in ('v7', 'v8', 'v9', 'v10'): raise ValueError('--prefer ram requires V7, V8 or V9')
    root=cli.ROOT;out=Path(a.output_dir).resolve() if a.output_dir else default_output_dir(root,renderer);out.mkdir(parents=True,exist_ok=True)
    stem=a.output or f'c643d-demo-v{__version__}-{public_renderer}-all'+('-ram' if prefer == 'ram' else '')
    if not a.output and legacy_cart:stem+='-legacy'
    metadata=out/'metadata';metadata.mkdir(parents=True,exist_ok=True)
    paths=[out/f'{stem}.crt',metadata/f'{stem}-cart-manifest.json',metadata/f'{stem}-cart-map.txt']
    if not cli._check_overwrite(paths,a.overwrite_policy):return 2
    entries,frame_image,stream_info,used,first_free=prepare(root,renderer,tass,a.tass_args or (),sources=sources,prefer=prefer,
        **({"work_prefix":"hifi"} if reel else {}),**({"frame_encoders":frame_encoders} if frame_encoders is not None else {}))
    image,plans,manifest=pack_demo_prgs(entries,source_root=root)
    if any(p.banks!=3 for p in plans) or manifest['highest_bank_used']!=first_free-1:raise ValueError('runtime bank reservation differs from planned frame pool')
    for b,chip in used:
        pos=easyflash_offset(b,chip);image[pos:pos+8192]=frame_image[pos:pos+8192]
    work=root/'build'/f'{stem}-cartridge-demo';gen=work/'generated';gen.mkdir(parents=True,exist_ok=True)
    write_demo_include(gen/'cart-demo-data.inc',plans)
    from .buildscreen import menu_title_lines
    (gen/'menu-title.inc').write_text('\n'.join(menu_title_lines(__version__, public_renderer))+'\n')
    if color_combo:
        from .buildscreen import screen_codes
        (gen/'menu-title.inc').write_text('\n'.join(['title_default:',*bytes_lines(screen_codes('COLOR COMBO TEST')),'    .byte 0'])+'\n')
    if variant in ('v5', 'v6', 'v7', 'v8', 'v9', 'v10'):
        from .buildscreen import build_screen_lines
        (gen/'build-screen.inc').write_text('\n'.join(build_screen_lines(__version__, ('hors-render-v1' if variant == 'v10' else f'yunroll-{variant}')+(' (ram)' if prefer == 'ram' else ''),hifi_reel=variant == 'v10' and not reel))+'\n')
        if color_combo:
            # A three-second, SPACE-skippable title, then automatic normal PLAY ALL.
            (gen/'build-screen.inc').write_text('\n'.join(build_screen_lines(__version__,'COLOR COMBO TEST'))+'\n')
    if variant in ('v7', 'v8', 'v9', 'v10'):
        from .buildscreen import play_all_thanks_lines
        (gen/'play-all-thanks.inc').write_text('\n'.join(play_all_thanks_lines(__version__))+'\n')
    if variant in ('v8', 'v9', 'v10'):
        durations = play_all_durations(stream_info, seconds, renderer)
        (gen/'play-all-durations.inc').write_text('play_all_durations:\n'+ '\n'.join(bytes_lines(durations))+'\n')
    hifi_indices = [next((i for i,e in enumerate(stream_info) if e['name'] == name), 255)
                    for name in ('HORSE HEAD HIFI', 'SUNFLOWER TORUS HIFI')]
    if variant == 'v10':
        with (gen/'play-all-durations.inc').open('a') as f:
            f.write(f'HIFI_HORSE_INDEX = {hifi_indices[0]}\nHIFI_FLOWER_INDEX = {hifi_indices[1]}\n')
    runtimes={};shared={}
    from .versioning import stamp_menu_source
    menu_source=root/('c64/cart/easyflash-hifi-reel-runtime.asm' if reel else f'c64/cart/easyflash-demo-scroll-runtime-{variant}.asm' if variant in ('v8', 'v9', 'v10') else 'c64/cart/easyflash-demo-scroll-runtime.asm')
    versioned_menu=work/'menu-runtime.asm'
    menu_text=stamp_menu_source(menu_source.read_text(),__version__)
    if color_combo:
        from .colorcombos import configure_combo_menu
        menu_text=configure_combo_menu(menu_text)
    versioned_menu.write_text(menu_text)
    for i,style in enumerate(cli.DEMO_MENU_STYLE_ORDER):
        binpath=work/f'{stem}-runtime-{style}.bin';whole=work/f'{stem}-menu-{style}-whole.bin'
        subprocess.run([tass,*(a.tass_args or ()),'-I',str(gen),'-D','VICE_DEBUGCART=0','-D','AUTO_LAUNCH=255','-D',f'MENU_STYLE={i}','-D',f'RENDERER_VERSION={int(variant[1:])}','-D',f'PLAY_ALL_SECONDS={seconds}','-b','--vice-labels','-l',str(work/f'{stem}-runtime-{style}.lbl'),'-L',str(work/f'{stem}-runtime-{style}.lst'),'-o',str(whole),str(versioned_menu)],check=True,cwd=root,stdout=subprocess.DEVNULL)
        data=whole.read_bytes()
        if len(data)!=4096:raise ValueError('scroll menu must occupy $c000-$cfff')
        shared[style]=data[:2048];binpath.write_bytes(data[2048:]);runtimes[style]=binpath

    control=work/f'{stem}-control.bin';boot=work/f'{stem}-romh0.bin';font=work/f'{stem}-menu-font.bin';font.write_bytes(build_menu_charset())
    control_source=cli.CART/(f'easyflash-demo-control-{variant}.asm' if variant in ('v8', 'v9', 'v10') else 'easyflash-demo-control-v7.asm' if variant == 'v7' else 'easyflash-demo-control.asm')
    if color_controls:
        from .demo_colors import configure_control_source
        local_control=work/'color-control.asm'
        local_control.write_text(configure_control_source(control_source.read_text()))
        control_source=local_control
    assemble_demo_control(tass=tass,tass_args=a.tass_args or (),source=control_source,output=control,labels=work/f'{stem}-control.lbl',listing=work/f'{stem}-control.lst',cwd=root)
    assemble_demo_boot(tass=tass,tass_args=a.tass_args or (),source=cli.CART/('easyflash-demo-boot.asm' if legacy_cart else 'easyflash-menu-boot.asm'),output=boot,labels=work/f'{stem}-boot.lbl',listing=work/f'{stem}-boot.lst',cwd=root)
    install_demo_boot(image,boot.read_bytes(),runtimes[a.menu_style].read_bytes(),control=control.read_bytes(),style_runtimes=[runtimes[s].read_bytes() for s in cli.DEMO_MENU_STYLE_ORDER],menu_font=font.read_bytes())
    for i,style in enumerate(cli.DEMO_MENU_STYLE_ORDER):
        pos=easyflash_offset(2,'romh',i*2048);image[pos:pos+2048]=shared[style]
    manifest.update(version=__version__,public_renderer=public_renderer,stream_renderer=renderer,uniform_renderer=True,streamed_entries=stream_info,menu_style=a.menu_style,menu_styles=list(cli.DEMO_MENU_STYLE_ORDER),menu_visible_rows=10,frame_chips_used=[dict(bank=b,chip=c) for b,c in used],note='Every entry uses the selected stream renderer. Canonical PRG vector tables preserve original sampling; HiFi uses 128 orientations.')
    if variant in ('v5', 'v6', 'v7', 'v8', 'v9', 'v10'): manifest['build_screen']=dict(version=__version__,renderer=('hors-render-v1' if variant == 'v10' else f'yunroll-{variant}')+(' (ram)' if prefer == 'ram' else ''),ticks=150,skip_key='SPACE')
    if variant in ('v7', 'v8', 'v9', 'v10'):
        manifest['preference']=prefer
        manifest['play_all']=dict(seconds=seconds,ticks_per_second=50,default_selection=True,position='above-list',skip_key='SPACE',exit_keys=['RUN/STOP','F1'],loop=True,start='first-visible-picture')
        if variant in ('v8', 'v9', 'v10'):
            manifest['exhibition'] = dict(key='F5', entry_seconds=durations, loop=True, start='first-visible-picture', normal_play_all_unchanged=True)
        manifest['play_all']['thank_you']=dict(seconds=10,ticks=500,exit_key='F1',version=__version__,position='after-last-demo',next='first-demo')
    if variant == 'v10':
        manifest['build_screen'].update(ticks=None, wait_for_space=True)
    if reel:
        manifest['reel'] = dict(order=[e['name'] for e in stream_info],
            scene_complete=True, scene_frames=len(sources[0].frames),
            scene_frame_ticks=sources[0].frame_ticks, spinner_seconds=10,
            thanks_seconds=10, loop=True, startup='SPACE',
            source_scene='examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene.crt')
        manifest.pop('exhibition', None)
        manifest['play_all']['position'] = 'automatic-reel'
    if variant == 'v10':
        manifest['build_screen'].update(ticks=None, wait_for_space=True)
        if not reel and 255 not in hifi_indices:
            manifest['hifi_reel'] = dict(key='F4', entries=hifi_indices,
                entry_seconds=10, thanks_seconds=10, title_seconds=10, title_skip_key='SPACE',
                exit_key='F1', loop=True, advertised=False)
    manifest.update(runtime_data_banks_used=first_free-1,highest_runtime_bank_used=first_free-1,
        highest_bank_used=max([first_free-1]+[bank for bank,chip in used]),
        data_banks_used=len(set(range(1,first_free))|{bank for bank,chip in used}),
        shared_menu_load='$c000',shared_menu_size=2048)
    if color_combo:
        manifest['color_combo_test']=dict(title='COLOR COMBO TEST',entries=len(stream_info),automatic_start=True,border_matches_background=True)
        manifest['build_screen'].update(ticks=150,wait_for_space=False,title='COLOR COMBO TEST')
        manifest['play_all'].pop('thank_you',None)
        manifest['play_all'].update(position='automatic',between_rounds='immediate-wrap')
        manifest.pop('exhibition',None)
        manifest['note']='Four monochrome colour pairs using preserved classic geometry; automatic normal PLAY ALL; F3/F4 colour cycling.'
    manifest['cart_write_method']=cart_write_method(legacy_cart)
    raw=work/f'{stem}.bin';raw.write_bytes(image);crt=out/f'{stem}.crt'
    title=('COLOR COMBO TEST' if color_combo else f'C643D {__version__} ALL {variant.upper()}' if legacy_cart else getattr(a, 'cartridge_name', None) or f'C643D {__version__} {public_renderer.upper()} {prefer.upper()}')
    convert_easyflash(cartconv=cartconv,raw=raw,crt=crt,name=title,cwd=root,legacy_cart=legacy_cart);check_easyflash_crt(cartconv=cartconv,crt=crt,cwd=root,legacy_cart=legacy_cart)
    (metadata/f'{stem}-cart-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (metadata/f'{stem}-cart-map.txt').write_text('Uniform '+renderer+' cartridge\nBank 0: boot/control/font; ROMH 1: menus; ROMH 2: menu directory/helpers\n'+''.join(f'{x["name"]}: {x["frames"]} frames, {x["rom_frame_bytes"]} stream bytes\n' for x in stream_info)+'Frame chips: '+', '.join(f'{b}:{c}' for b,c in used)+'\n')
    print(f'built {crt}\nall {len(plans)} entries: {renderer}; 10-row scrolling menu; {sum(x["rom_frame_bytes"] for x in stream_info)} frame bytes',flush=True)
    if a.run:
        vice=cli.resolve_executable(a.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        run_cartridge(vice, crt, a.vice_args or (), clean_settings=getattr(a, 'vice_clean_settings', False), cwd=root)
    return 0
