"""GMod3 CLI dispatch; preserved EasyFlash execution stays in its own branch."""
import json
from pathlib import Path
import subprocess

from .gmod3_image import CAPACITIES_MIB, inspect_crt


def add_flags(parser, *, build=False, settings=None):
    from .cartridge_defaults import configured_default
    try:
        default = configured_default(settings)
    except ValueError as exc:
        parser.error(str(exc))
    parser.add_argument('--cart-type', choices=('easyflash', 'gmod3'), default=None,
                        help='cartridge hardware; CLI overrides [cartridge_defaults] cart_type, then renderer default')
    if build:
        parser.add_argument('--gmod3-size-mib', type=int, choices=CAPACITIES_MIB,
                            help='GMod3 flash capacity; default 2 MiB; requires --cart-type gmod3')
        parser.add_argument('--gmod3-first-bank', type=int,
                            help='diagnostic data-bank placement; default 4; requires --cart-type gmod3')


def command(vice, crt, args=(), *, clean_settings=False):
    path = Path(crt).expanduser().resolve()
    inspect_crt(path)
    console = ['-console'] if '-console' in args else []
    options = [a for a in args if a != '-console']
    return [str(vice), *console, *(['-default'] if clean_settings else []), '-pal',
        *([] if console else ['+VICIIfull']), '+warp', *options,
        '+saveres', '+gmod3flashwrite', '+cart', '-cartcrt', str(path)]


def run(a):
    from .cli import resolve_executable, ROOT
    vice = resolve_executable(a.vice, 'vice')
    if not vice:
        raise ValueError('VICE not found')
    return subprocess.run(command(vice, a.crt, a.vice_args,
        clean_settings=a.vice_clean_settings), cwd=ROOT, check=False).returncode


def build(a):
    from . import gmod3_surface
    if a.renderer not in ('hors-renderer-v3','hors-render-v3'):
        raise ValueError('GMod3 requires HORS-V3 or HORS-V4; older renderer backends remain EasyFlash')
    from .gmod3_options import normalize
    normalize(a)
    if a.interactive_cart:
        if a.blend or a.scene or a.animation not in (None,'spin'):
            raise ValueError('--interactive-cart requires an object/SVG spin or SVG presentation modes; authored scenes use automatic playback')
        if a.output and Path(a.output).suffix and Path(a.output).suffix.lower()!='.crt':
            raise ValueError('--interactive-cart output must be a .crt file or extensionless basename')
    if a.blend or a.scene:
        from .gmod3_scene import build
        return build(a)
    if a.gmod3_first_bank is not None and a.gmod3_first_bank<4:
        raise ValueError('GMod3 banks 0..3 are reserved for boot/runtime')
    return gmod3_surface.cmd_build(a)


def smoke(a):
    from . import cli
    from .gmod3_probe import build as build_probe
    if a.legacy_cart or a.gmod3_first_bank is not None or a.output:
        raise ValueError('GMod3 probe uses capacity-labelled filenames; select --output-dir')
    tass, conv = cli.resolve_executable(a.tass, 'tass'), cli.require_cartconv(a.cartconv)
    if not tass or not conv:
        raise ValueError('64tass and cartconv are required')
    out = Path(a.output_dir).resolve() if a.output_dir else cli.BUILD/'gmod3-probes'
    size = a.gmod3_size_mib or 16
    if not cli._check_overwrite([out/f'gmod3-probe-{size}m.crt'], a.overwrite_policy):
        return 2
    a.crt = build_probe(cli.ROOT, out, tass=tass, cartconv=conv, size_mib=size)
    return run(a) if a.run else 0
