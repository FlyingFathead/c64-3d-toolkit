"""Stable v2 integration; beta1 wire format and drawing instructions are preserved.

All builds use isolated assembly copies. Old explicit names keep old behavior.
Host integration swaps are serialized; use processes for parallel compilation.
"""
from contextlib import contextmanager
from copy import copy
from dataclasses import replace
from pathlib import Path
from threading import RLock
import json
import shutil
import tempfile

from .hors_v2 import spans, patch_helper
from .optimize import picture_bytes

NAME = 'hors-render-v2'
WIRE_FORMAT = 'hors-v2-batched-literal-spans-1'
_lock = RLock()


def encoder(gap=6, batch_budget=2048):
    """Same v2 wire bytes, without building an unused size-limited vector stream."""
    if gap<1 or batch_budget<1: raise ValueError('v2 gap and batch budget must be positive')
    def encode(frame, colors=True):
        if len(frame.clear_spans)>255 or (colors and len(frame.color_spans)>255):
            raise ValueError(f'v2 metadata span count exceeds one byte: {len(frame.clear_spans)} clear spans, {len(frame.color_spans) if colors else 0} colour spans (maximum 255 each per frame). This is not an animation-length limit; use --renderer hors-renderer-v3 for compact clear/shared colour metadata')
        data=bytearray([len(frame.clear_spans)])
        for span in frame.clear_spans: data.extend(span)
        if colors:
            data.append(len(frame.color_spans))
            for span in frame.color_spans: data.extend(span)
        meta=len(data)
        if meta>1024: raise ValueError(f'v2 metadata is {meta} bytes and exceeds its 1 KiB cache per frame; fewer animation frames do not reduce this limit')
        bitmap=picture_bytes(frame)[:7680];runs=spans(bitmap,gap)
        data.extend((0x8000|len(runs)).to_bytes(2,'little'))
        planned=0;proof=bytearray(7680)
        for i,(offset,values) in enumerate(runs):
            planned+=180+15*len(values)
            flush=i+1==len(runs) or planned+180+15*len(runs[i+1][1])>batch_budget
            data.extend((offset&255,(offset>>8)|(128 if flush else 0),len(values)))
            data.extend(values);proof[offset:offset+len(values)]=values
            if flush: planned=0
        if proof!=bitmap: raise AssertionError('v2 host bitmap proof failed')
        if len(data)>8192: raise ValueError('v2 literal picture exceeds one 8 KiB bank; use another candidate')
        return bytes(data),meta
    return encode


@contextmanager
def staged(root, *, scene=False):
    root = Path(root)
    with _lock, tempfile.TemporaryDirectory(prefix='hors-v2-stable-') as td:
        stage = Path(td)
        shutil.copytree(root/'c64', stage/'c64')
        suffix = '-scene' if scene else ''
        helper = stage/f'c64/cart/easyflash-stream-v10{suffix}-helper.asm'
        helper.write_text(patch_helper(helper.read_text()))
        runtime = stage/f'c64/renderer-yunroll-cart-v10{suffix}.asm'
        text = runtime.read_text()
        first = text.index('* = $4f00\nv3_entry_lo:')
        last = text.index('* = $9a00' if scene else '* = $5c00', first)
        runtime.write_text(text[:first]+'v3_entry_lo = $4f00 ; v2 direct-only\n'+text[last:])
        yield stage


def save_builds(stage, root):
    for path in (stage/'build').iterdir():
        shutil.copytree(path, Path(root)/'build'/path.name, dirs_exist_ok=True)


def describe(manifest, gap, budget):
    if manifest['byte_span_frames'] != manifest['frames']:
        raise ValueError('v2 requires every frame to use direct byte spans')
    manifest.update(renderer=NAME, wire_format=WIRE_FORMAT,
        encoding_choice=dict(gap=gap, batch_budget=budget),
        implementation='hors-render-v2-beta1 drawing kernel',
        previous_picture_dependency=False, vector_fallback=False,
        extra_reserved_RAM_bytes=0, reclaimed_vector_dispatch_range=[0x4f00,0x5000],
        batch_budget_is_host_cost_model_not_hard_measured_bound=True)
    if 'build_screen' in manifest:
        manifest['build_screen']['renderer']=NAME+(' (ram)' if manifest.get('preference')=='ram' else '')


@contextmanager
def identity():
    """Only change identification text, retaining the native SPACE-start code."""
    from . import buildscreen, cartintro
    old_screen, old_intro, old_title = buildscreen.build_screen_lines, cartintro.emit_intro, buildscreen.menu_title_lines
    def screen(version, renderer, **kw):
        lines = old_screen(version, renderer, **kw)
        old = buildscreen.screen_codes(renderer)
        new = buildscreen.screen_codes(renderer.replace('hors-render-v1',NAME))
        from .emit import bytes_lines
        before, after = '\n'.join(bytes_lines(old)), '\n'.join(bytes_lines(new))
        return '\n'.join(lines).replace(before, after).split('\n')
    def intro(*args, **kw):
        # emit_intro calls build_screen_lines, so the same text substitution applies.
        return old_intro(*args, **kw)
    buildscreen.build_screen_lines=screen
    cartintro.emit_intro=intro
    buildscreen.menu_title_lines=lambda version, renderer:old_title(version,NAME)
    try: yield
    finally:
        buildscreen.build_screen_lines, cartintro.emit_intro, buildscreen.menu_title_lines=old_screen, old_intro, old_title


def assemble_scene(root, frames, scene, *, draw_gap=6, batch_budget=2048, **kwargs):
    from . import cartscene
    with staged(root, scene=True) as stage, identity():
        old_pack=cartscene.pack_scene_frames
        def pack(items, colors=True, **options):
            options.update(encoder=encoder(draw_gap,batch_budget),direct_bytes=True)
            return old_pack(items,colors,**options)
        cartscene.pack_scene_frames=pack
        try:
            kwargs['renderer']='yunroll-cart-v10-scene'
            crt, manifest=cartscene.assemble_scene(stage,frames,scene,**kwargs)
        finally: cartscene.pack_scene_frames=old_pack
        save_builds(stage,root)
    describe(manifest,draw_gap,batch_budget)
    manifest['runtime_work']=f"build/{kwargs['stem']}-stream-{'scene' if 'scene' in manifest['format'] else 'v10'}"
    (Path(kwargs['outdir'])/(kwargs['stem']+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    return crt,manifest


def assemble_cartridge(root, frames, mesh, *, draw_gap=6, batch_budget=2048, **kwargs):
    from . import cartstream
    with staged(root) as stage:
        old_pack=cartstream.pack_frames
        def pack(items, colors=True, **options):
            options['encoder']=encoder(draw_gap,batch_budget)
            return old_pack(items,colors,**options)
        cartstream.pack_frames=pack
        try:
            kwargs['renderer']='yunroll-cart-v10'
            # Preserve the original callable even while cmd_build_object redirects it.
            crt,manifest=_object_assembler(stage,frames,mesh,**kwargs)
        finally: cartstream.pack_frames=old_pack
        save_builds(stage,root)
    describe(manifest,draw_gap,batch_budget)
    manifest['runtime_work']=f"build/{kwargs['stem']}-stream-{'scene' if 'scene' in manifest['format'] else 'v10'}"
    (Path(kwargs['outdir'])/(kwargs['stem']+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    return crt,manifest


from .cartstream import assemble_cartridge as _object_assembler


def cmd_build_object(a):
    from . import cartstream
    with _lock:
        old=cartstream.assemble_cartridge
        cartstream.assemble_cartridge=lambda *args,**kw:assemble_cartridge(*args,
            draw_gap=getattr(a,'v2_draw_gap',6),batch_budget=getattr(a,'v2_batch_budget',2048),**kw)
        try: return cartstream.cmd_build_cart_v2(a)
        finally: cartstream.assemble_cartridge=old


def prepare_menu(root, renderer, tass, tass_args=(), sources=None, prefer='fps',
                 work_prefix='stable-hors-v2', frame_encoders=None, prepare=None):
    from . import cartuniform
    prepare=prepare or cartuniform.prepare
    if sources is None: sources=cartuniform.demos(root)
    with staged(root) as stage:
        entries,image,info,used,first_free=prepare(stage,'yunroll-cart-v10',tass,tass_args,
            sources=sources,prefer=prefer,work_prefix=work_prefix,
            frame_encoders=frame_encoders or {d.name:encoder(3,2048) for d in sources})
        for entry in info: describe(entry,3,2048)
        save_builds(stage,root)
        entries=[(name,Path(root)/path.relative_to(stage)) for name,path in entries]
    return entries,image,info,used,first_free


def build_menu(a, *, sources=None, reel=False, frame_encoders=None):
    from . import cli,cartuniform,__version__
    root=cli.ROOT
    if sources is None: sources=cartuniform.demos(root)
    if not reel and not getattr(a,'color_combo_test',False) and getattr(a,'color_controls',True):
        sources=[replace(d,color_controls=True) for d in sources]
    options=copy(a)
    options.stream_renderer='hors-render-v1'
    options.cartridge_name=getattr(a, 'cartridge_name', None) or f'C643D {__version__} HORS V2 {a.prefer.upper()}'
    options.output=options.output or f'c643d-demo-v{__version__}-{NAME}-all'+('-ram' if a.prefer=='ram' else '')
    if not a.output and getattr(a,'legacy_cart',False):options.output+='-legacy'
    options.output_dir=str(Path(a.output_dir).resolve() if a.output_dir else root/'examples/cart_demos')
    with staged(root) as stage, identity():
        # Menu UI text only; the renderer and controls keep their instruction bytes.
        for filename in ('easyflash-demo-scroll-runtime-v10.asm','easyflash-hifi-reel-runtime.asm'):
            path=stage/'c64/cart'/filename
            text=path.read_text().replace('HORS-V1','HORS-V2')
            text=text.replace('    .text "ALL DEMOS: CART V"\n    .byte $30+RENDERER_VERSION',
                              '    .text "ALL DEMOS: HORS V2"')
            path.write_text(text)
        oldroot,oldcart=cli.ROOT,cli.CART
        oldprepare=cartuniform.prepare
        def prepare(*args,**kw):
            kw['work_prefix']='stable-'+options.output
            return oldprepare(*args,**kw)
        cartuniform.prepare=prepare
        cli.ROOT,cli.CART=stage,stage/'c64/cart'
        try:
            code=cartuniform.build(options,sources=sources,reel=reel,
                frame_encoders=frame_encoders or {d.name:encoder(3,2048) for d in sources})
        finally:
            cli.ROOT,cli.CART=oldroot,oldcart
            cartuniform.prepare=oldprepare
        if code: return code
        save_builds(stage,root)
    path=Path(options.output_dir)/'metadata'/(options.output+'-cart-manifest.json')
    manifest=json.loads(path.read_text())
    for entry in manifest['streamed_entries']: describe(entry,3,2048)
    manifest.update(public_renderer=NAME,stream_renderer=NAME)
    manifest['build_screen']['renderer']=NAME+(' (ram)' if a.prefer=='ram' else '')
    if reel: manifest['reel']['source_scene']=manifest['reel']['source_scene'].replace('hors-render-v1','hors-render-v2')
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    return 0
