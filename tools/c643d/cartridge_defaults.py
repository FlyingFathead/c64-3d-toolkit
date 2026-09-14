"""Cartridge selection policy; hardware backends remain separate."""
import configparser
from pathlib import Path


def configured_default(settings):
    path=getattr(settings,'config_path',None)
    if path is None:return None
    config=configparser.ConfigParser(interpolation=None)
    config.read(Path(path),encoding='utf-8')
    value=config.get('cartridge_defaults','cart_type',fallback='auto').strip().lower()
    if value not in ('auto','easyflash','gmod3'):
        raise ValueError('cartridge_defaults.cart_type must be auto, easyflash or gmod3')
    return None if value=='auto' else value


def resolve(args, settings):
    """Explicit CLI > universal config > selected renderer's hardware default."""
    # Only commands exposing hardware selection consume this preference.
    # Listing/doctor and preserved legacy demo builders have their own routes.
    if args.command not in ('build','cartridge-smoke','run-cart'):
        return 'easyflash'
    from .renderer_names import canonical_selector, selector_cartridge
    named=selector_cartridge(getattr(args,'renderer',''))
    explicit=getattr(args,'cart_type',None)
    if named and explicit not in (None,named):raise ValueError('Renderer suffix conflicts with --cart-type')
    if explicit is not None:return explicit
    if named:return named
    if args.command=='build' and args.renderer in ('step','bytechunk','yunroll'):
        return 'easyflash'  # These produce resident PRGs, not cartridge images.
    configured=configured_default(settings)
    if configured:return configured
    if args.command=='build' and canonical_selector(args.renderer)=='hors-renderer-v4':
        return 'gmod3'
    if args.command=='run-cart' and Path(args.crt).expanduser().is_file():
        # The container identifies existing images; no guesses from filenames.
        with Path(args.crt).expanduser().open('rb') as handle:header=handle.read(26)
        if len(header)>=24 and header[:16]==b'C64 CARTRIDGE   ' and int.from_bytes(header[22:24],'big')==62:
            return 'gmod3'
    return 'easyflash'
