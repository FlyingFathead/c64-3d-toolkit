#!/usr/bin/env python3
"""Build the three-part HiFi exhibition cart without Blender or external history."""
import argparse,hashlib
from pathlib import Path
from c643d import cli,cartuniform,__version__
from c643d.cartframes import load_menu_reference
from c643d.toolchain import load_toolchain_settings
from compare_renderers import load_scene_references


def main(argv=None):
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--prefer',choices=('fps','ram'),default='fps')
    p.add_argument('--renderer',choices=('hors-render-v1','hors-render-v2'),default='hors-render-v2')
    a=p.parse_args(argv)
    frames,scene,ref=load_scene_references(root)['horse-sunflower']
    path=root/'assets/comparison-scene-vector-reference.json.gz'
    authored=cartuniform.Demo('HORSE AND SUNFLOWER',frames,ref['colors'],ref['screen_color'],
        b'',str(path.relative_to(root)),hashlib.sha256(path.read_bytes()).hexdigest(),
        frame_ticks=ref['frame_ticks'],finite=True,show_hud=False)
    sources=load_menu_reference(root)
    sources=[authored]+[next(d for d in sources if d.name==name)
                       for name in ('SUNFLOWER TORUS HIFI','HORSE HEAD HIFI')]
    parser=cli.make_parser(load_toolchain_settings(root/'config/c643d.ini'))
    args=parser.parse_args(['cart-demos','--stream-renderer',a.renderer,
        '--prefer',a.prefer,'--play-all-seconds','10','--tass',a.tass,'--cartconv',a.cartconv,
        '--output',f'c643d-hifi-v{__version__}-{a.renderer}'+('-ram' if a.prefer=='ram' else ''),
        '--output-dir',str(root/'examples/cart_hifi'),'--overwrite-policy','allow'])
    return cartuniform.build(args,sources=sources,reel=True)

if __name__=='__main__':main()
