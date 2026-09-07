#!/usr/bin/env python3
"""Build the three V5 examples from the released V4 vector samples.

No Blender installation or physics rebake is needed. The default menu input is a checksum-verified compressed vector reference;
--reference-multi also accepts an archived V4 CRT and its matching manifest.
For new Blender exports use c643d.py cart-stream --renderer yunroll-cart-v5-scene.
"""
import argparse,hashlib,json
from pathlib import Path
from c643d import cli,cartuniform,cartscene,__version__
from c643d.cartframes import load_uniform_sources,load_scene_source,load_menu_reference
from c643d.toolchain import load_toolchain_settings


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--reference-multi',type=Path,help='optional original V4 CRT; defaults to the compact shipped vector reference')
    p.add_argument('--reference-marbles',type=Path,default=root/'examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt')
    a=p.parse_args()
    tass=cli.resolve_executable(a.tass,'tass');conv=cli.require_cartconv(a.cartconv,verbose=True)
    if not tass or not conv:raise ValueError('64tass and cartconv are required')
    sources=load_uniform_sources(root,a.reference_multi) if a.reference_multi else load_menu_reference(root)
    reference_multi=a.reference_multi or root/'assets/v4-menu-vector-reference.json.gz'
    parser=cli.make_parser(load_toolchain_settings(root/'config/c643d.ini'))
    args=parser.parse_args(['cart-demos','--stream-renderer','yunroll-cart-v5',
                           '--tass',tass,'--cartconv',conv,'--overwrite-policy','allow'])
    cartuniform.build(args,sources=sources)
    frames,scene,reference=load_scene_source(a.reference_marbles)
    for hud in (True,False):
        stem='dont_lose_your_marbles-yunroll-cart-v5-scene'+('' if hud else '-clean')
        cartscene.assemble_scene(root,frames,scene,tass=tass,cartconv=conv,
            outdir=root/'examples/cart_marbles',stem=stem,hud_text=reference['hud_text'],
            frame_ticks=reference['frame_ticks'],colors=reference['colors'],color_index=reference['screen_color']>>4,
            intro=True,ending=True,text_overlay=hud,renderer='yunroll-cart-v5-scene')
    record=dict(toolkit_version=__version__,renderer='yunroll-cart-v5',
        references={str(path.relative_to(root) if path.is_relative_to(root) else path):hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (reference_multi.resolve(),a.reference_marbles.resolve())},
        note='Rebuilt exact released vector samples; no Blender re-export or physics rebake.')
    (root/'build/v5-example-provenance.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
