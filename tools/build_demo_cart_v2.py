#!/usr/bin/env python3
"""Build a separate Demo Cart 2.0 preview, with v1 or v2 beta."""
from pathlib import Path
from dataclasses import asdict
import argparse
import hashlib
import json
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--renderer',choices=['hors-render-v1','hors-render-v2-beta1','hors-render-v2'],default='hors-render-v2')
    ap.add_argument('--output-dir',type=Path,default=ROOT/'examples/cart_demos_v2')
    ap.add_argument('--tass',default='64tass');ap.add_argument('--cartconv',default='cartconv')
    ap.add_argument('--gap',type=int,default=6);ap.add_argument('--batch-budget',type=int,default=2048)
    ap.add_argument('--prefer',choices=['fps','ram'],default='fps')
    ap.add_argument('--policy',type=Path,default=ROOT/'examples/cart_demos_v2/encoding-policy.json',help='Measured per-scene encoding choices, guarded by source hash')
    ap.add_argument('--water',nargs='+',choices=['ripples_lite','cross_swell','liquid_floor'],default=['ripples_lite'],help='Selected complete water loops; default Ripples Lite. Capacity failures never reduce samples.')
    a=ap.parse_args()
    from c643d import cli, cartuniform, buildscreen
    from c643d.hors_v2 import encoder,patch_helper
    from c643d.sceneio import load_scene
    from c643d.pipeline import build_scene_frames
    from c643d.font import bitmap_text
    from c643d.emit import bytes_lines
    from c643d.toolchain import load_toolchain_settings
    a.output_dir=a.output_dir.resolve();a.output_dir.mkdir(parents=True,exist_ok=True)
    cases=[('COLOUR CUBE 24','examples/autotune/colour-cube.c643dscene'),
           ('COLOUR TORUS 18','examples/autotune/colour-torus.c643dscene')]
    cases += [(title,'examples/cart_demos_v2/scenes/'+slug+'.c643dscene') for title,slug in
              [('TWIST TUNNEL','twist-tunnel'),('RIBBON DANCE','ribbon-dance'),('ORBITAL CUBES','orbital-cubes'),('WAVE LATTICE','wave-lattice')]]
    a.water=list(dict.fromkeys(a.water))
    for water in a.water:
        cases.append((water.replace('_',' ').upper(),'examples/cart_demos_v2/scenes/'+water+'.c643dscene'))
    sources=[]
    for title,path in cases:
        scene=load_scene(ROOT/path)
        print('Compiling',title,len(scene.frames),'samples',flush=True)
        colour=title not in ('RIPPLES LITE','CROSS SWELL','LIQUID FLOOR')
        width=256 if '/autotune/' in path else 320
        frames,_=build_scene_frames(scene,visibility_mode='surface',z_tolerance=.0008,feature_angle=40,
            enable_source_colors=colour,fallback_color=1,width=width,height=192,max_frames=255,max_visible_runs=65535)
        for frame in frames:
            spans=[]
            for lo,hi,count in frame.clear_spans:
                offset=lo+(hi<<8)
                while count:
                    n=min(32,count);spans.append((offset&255,offset>>8,n));offset+=8*n;count-=n
            frame.clear_spans=spans
        sources.append(cartuniform.Demo(title,frames,colour,0x10,bytes(bitmap_text(title,31)),path,
            hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
    beta=a.renderer in ('hors-render-v2-beta1','hors-render-v2')
    stable=a.renderer=='hors-render-v2'
    policy=json.loads(a.policy.read_text()) if beta else {'scenes':{}}
    choices={}
    for demo in sources:
        choice=policy.get('scenes',{}).get(demo.name,{})
        if choice and choice['source_sha256']!=demo.source_sha256:
            raise ValueError('Encoding policy source changed for '+demo.name+'; rerun the scene search')
        choices[demo.name]={'gap':choice.get('gap',a.gap),'batch_budget':choice.get('batch_budget',a.batch_budget)}
    stem='demo-cart-2-preview-'+('hors-v2' if stable else 'hors-v2-beta1' if beta else 'hors-v1')+('-ram' if a.prefer=='ram' else '')
    suffix='' if a.water==['ripples_lite'] else '-'+ '-'.join(a.water).replace('_','-')
    stem+=suffix
    worktag=f'demo-cart-v2-{a.renderer}-{a.prefer}'+suffix
    parser=cli.make_parser(load_toolchain_settings(ROOT/'config/c643d.ini'))
    options=parser.parse_args(['cart-demos','--stream-renderer','hors-render-v1','--output',stem,
        '--output-dir',str(a.output_dir),'--tass',a.tass,'--cartconv',a.cartconv,'--menu-style','demoscene','--prefer',a.prefer])
    options.overwrite_policy='allow'
    oldroot,oldcart=cli.ROOT,cli.CART
    oldtitle,oldscreen=buildscreen.menu_title_lines,buildscreen.build_screen_lines
    try:
        with tempfile.TemporaryDirectory(prefix='demo-cart-2-') as td:
            stage=Path(td);shutil.copytree(ROOT/'c64',stage/'c64')
            if beta:
                helper=stage/'c64/cart/easyflash-stream-v10-helper.asm'
                helper.write_text(patch_helper(helper.read_text()))
                runtime=stage/'c64/renderer-yunroll-cart-v10.asm';text=runtime.read_text()
                first=text.index('* = $4f00\nv3_entry_lo:');last=text.index('* = $5c00',first)
                runtime.write_text(text[:first]+'v3_entry_lo = $4f00 ; byte-only beta\n'+text[last:])
            # Presentation changes are applied equally to the A/B builds.
            menu=stage/'c64/cart/easyflash-demo-scroll-runtime-v10.asm'
            text=menu.read_text()
            text=text.replace('    .text "ALL DEMOS: CART V"\n    .byte $30+RENDERER_VERSION',
                              '    .text "'+('HORS V2' if stable else 'HORS V2 BETA' if beta else 'HORS V1')+f' - {len(sources)} SCENES"')
            menu.write_text(text)
            title='HORS V2' if stable else 'HORS V2 BETA' if beta else 'HORS V1'
            buildscreen.menu_title_lines=lambda version,_renderer:['title_default:',*bytes_lines(buildscreen.screen_codes('DEMO CART 2 '+version+' '+title)),'    .byte 0']
            # Keep the native SPACE-start path and exact control instructions.
            def screen(version, renderer, **kw):
                lines=oldscreen(version,renderer,**kw)
                start=lines.index('build_screen_text_renderer:')+1
                end=lines.index('build_screen_text_github:')
                old=buildscreen.screen_codes(renderer)
                new=buildscreen.screen_codes(('hors-render-v2' if stable else 'hors-render-v2 beta' if beta else 'hors-render-v1').ljust(len(old)))
                if len(new)!=len(old):
                    # Same byte length keeps the existing screen-copy loop valid.
                    new=buildscreen.screen_codes(('HORS V2' if stable else 'HORS V2 BETA' if beta else 'HORS V1').ljust(len(old)))
                lines[start:end]=bytes_lines(new)
                return lines
            buildscreen.build_screen_lines=screen
            cli.ROOT=stage;cli.CART=stage/'c64/cart'
            encoders={name:encoder(c['gap'],c['batch_budget']) for name,c in choices.items()} if beta else None
            code=cartuniform.build(options,sources=sources,frame_encoders=encoders)
            if code:raise RuntimeError('Demo cart builder did not complete')
            # Keep generated symbols/oracles beside other ignored build products.
            for path in (stage/'build').iterdir():
                name=worktag if path.name.startswith('uniform-') else path.name
                shutil.copytree(path,ROOT/'build'/name,dirs_exist_ok=True)
            metadata=a.output_dir/'metadata'/f'{stem}-cart-manifest.json'
            manifest=json.loads(metadata.read_text())
            for entry in manifest['streamed_entries']:
                parts=Path(entry['work']).parts
                entry['work']='/'.join(('build',worktag,*parts[2:]))
                entry['renderer']=a.renderer
                if beta:
                    if entry['byte_span_frames']!=entry['frames']:raise ValueError('Beta menu requires every picture to use direct spans')
                    entry['wire_format']='hors-v2-batched-literal-spans-1'
                    entry['encoding_choice']=choices[entry['name']]
            manifest.update(public_renderer=a.renderer,stream_renderer=a.renderer,
                note='Demo Cart 2.0 preview: six new scenes plus selected complete water loops; separate from the frozen release comparison dataset.',
                preview=dict(version=1,draw_gap=a.gap if beta else None,batch_budget=a.batch_budget if beta else None,
                             sample_counts=[len(s.frames) for s in sources],new_dataset=True,water=a.water))
            manifest['build_screen']['renderer']=a.renderer
            metadata.write_text(json.dumps(manifest,indent=2)+'\n')
    finally:
        cli.ROOT,cli.CART=oldroot,oldcart
        buildscreen.menu_title_lines,buildscreen.build_screen_lines=oldtitle,oldscreen
    print('Ready:',a.output_dir/(stem+'.crt'))


if __name__=='__main__':
    main()
