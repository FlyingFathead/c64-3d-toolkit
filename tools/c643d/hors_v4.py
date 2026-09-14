"""HORS-V4: the V3 picture core with the independent GMod3 cartridge backend.

Previous renderers and explicit EasyFlash builds use their preserved modules.
Version four denotes the larger-cart runtime/loader architecture, not a new
triangle rasterizer or a promise of a fixed FPS improvement.
"""
NAME='hors-renderer-v4'
ALIASES=(NAME,'hors-render-v4','hors-v4','hors-v4-gmod3','hors-v4-ef')
DEFAULT_CARTRIDGE='gmod3'


def build(args):
    from .cartridge_defaults import resolve
    args.cart_type=resolve(args,None)
    if args.cart_type=='easyflash':
        from .hors_v4_easyflash import build as build_easyflash
        return build_easyflash(args)
    from .gmod3_cli import build as build_gmod3
    args.requested_renderer=NAME
    args.renderer='hors-renderer-v3'
    return build_gmod3(args)
