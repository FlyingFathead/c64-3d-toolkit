"""Opt-in build entry point for a bounded fixed-picture renderer contest."""
from .toolchain import ToolchainSettings, resolve_executable


def validate(args, settings=None):
    from .cli import make_parser
    if not args.scene or args.blend:
        raise ValueError('The contest currently requires --scene with an exported .c643dscene; export .blend first')
    if args.contest_out is None:
        raise ValueError('Use --contest-out with a new directory outside the checkout')
    from .cartridge_defaults import resolve
    hardware = resolve(args, settings or ToolchainSettings())
    if hardware not in (None,'auto','easyflash') or 'gmod3' in args.renderer:
        raise ValueError('The contest currently selects an EasyFlash scene winner only; use manual selection for GMod3')
    if settings is not None:
        standard=ToolchainSettings()
        for key in ('tass_args','vice_args'):
            if getattr(args,key,None) is None and getattr(settings,key)!=getattr(standard,key):
                raise ValueError('The fixed-protocol contest does not accept configured '+key+'; use --no-config or manual selection')
    defaults=make_parser(ToolchainSettings()).parse_args(['build','--scene',args.scene])
    allowed={'scene','renderer','renderer_selection','cart_type','config','no_config',
             'contest_out','contest_workers','contest_capture','contest_vice_data',
             'tass','cartconv','vice','blender','blender_color_space','overwrite_policy'}
    changed=[key for key,value in vars(args).items() if not key.startswith('_') and key not in allowed
             and value!=getattr(defaults,key,None)]
    if changed:
        flags=', '.join('--'+key.replace('_','-') for key in changed)
        raise ValueError('This fixed-picture contest uses the exported scene and default playback; unsupported overrides: '
                         +flags+'. Use --renderer-selection manual for this build; overrides are never silently ignored')


def run(args, settings=None):
    validate(args, settings)
    import sys
    from pathlib import Path
    tools_path=str(Path(__file__).resolve().parents[1])
    if tools_path not in sys.path:sys.path.insert(0,tools_path)
    import optimizer_profiler
    argv=[args.scene,'--out',str(args.contest_out),'--workers',str(args.contest_workers)]
    for key in ('tass','cartconv','vice'):
        executable=resolve_executable(getattr(args,key),key)
        if not executable:raise ValueError('Executable not found: '+getattr(args,key))
        argv+=['--'+key,executable]
    if args.contest_vice_data:argv+=['--vice-data',str(args.contest_vice_data)]
    if args.contest_capture:argv+=['--capture']
    print('Renderer contest: full original-core chart and all native scene backends; fixed pictures. Native EasyFlash candidates compete at four-refresh hold.',flush=True)
    return optimizer_profiler.main(argv)
