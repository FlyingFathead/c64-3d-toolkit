from __future__ import annotations

import configparser
import os
import platform
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ToolchainSettings:
    tass: str = '64tass'
    vice: str = 'x64sc'
    blender: str = 'blender'
    tass_args: Tuple[str, ...] = ()
    # Development runs should open in a normal window unless the user asks
    # otherwise. VICE uses '+' to disable this boolean resource.
    vice_args: Tuple[str, ...] = ('+VICIIfull',)
    config_path: Optional[Path] = None
    platform_key: str = 'linux'


def platform_key(system: Optional[str] = None) -> str:
    name=(system or platform.system()).lower()
    if name.startswith('darwin') or name.startswith('mac'):
        return 'macos'
    if name.startswith('win'):
        return 'windows'
    return 'linux'


def split_args(value: str, *, windows: bool = False) -> Tuple[str, ...]:
    value=value.strip()
    if not value:
        return ()
    return tuple(shlex.split(value, posix=not windows))


def _section_value(cfg: configparser.ConfigParser, section: str, key: str):
    if not cfg.has_section(section) or key not in cfg[section]:
        return None
    return cfg[section].get(key, raw=True)


def load_toolchain_settings(path: Optional[Path], *, system: Optional[str] = None, require: bool = False) -> ToolchainSettings:
    """Load optional project-local toolchain configuration.

    Precedence inside the file is [toolchain] followed by the current
    platform section ([linux], [macos], or [windows]). Missing files simply
    leave the built-in defaults active unless *require* is True.
    """
    pkey=platform_key(system)
    values={
        'tass':'64tass',
        'vice':'x64sc',
        'blender':'blender',
        'tass_args':(),
        'vice_args':('+VICIIfull',),
    }
    loaded=None
    if path is not None:
        path=Path(path).expanduser()
        if path.exists():
            cfg=configparser.ConfigParser(interpolation=None)
            with path.open('r',encoding='utf-8') as f:
                cfg.read_file(f)
            for section in ('toolchain',pkey):
                for key in ('tass','vice','blender'):
                    raw=_section_value(cfg,section,key)
                    if raw is not None and raw.strip():
                        values[key]=raw.strip().strip('"').strip("'")
                for key in ('tass_args','vice_args'):
                    raw=_section_value(cfg,section,key)
                    if raw is not None:
                        values[key]=split_args(raw,windows=(pkey=='windows'))
            loaded=path.resolve()
        elif require:
            raise FileNotFoundError(f'config file not found: {path}')
    return ToolchainSettings(
        tass=values['tass'], vice=values['vice'], blender=values['blender'],
        tass_args=tuple(values['tass_args']), vice_args=tuple(values['vice_args']),
        config_path=loaded, platform_key=pkey,
    )


def config_request(argv: Sequence[str], root: Path):
    """Find --config/--no-config before argparse rearranges shortcut syntax."""
    env_path=os.environ.get('C643D_CONFIG')
    path=Path(env_path).expanduser() if env_path else root/'config'/'c643d.ini'
    explicit=bool(env_path)
    disabled=False
    i=0
    while i<len(argv):
        arg=argv[i]
        if arg=='--no-config':
            disabled=True
        elif arg.startswith('--config='):
            path=Path(arg.split('=',1)[1]).expanduser(); explicit=True; disabled=False
        elif arg=='--config' and i+1<len(argv):
            path=Path(argv[i+1]).expanduser(); explicit=True; disabled=False; i+=1
        i+=1
    return (None if disabled else path), explicit, disabled


def _is_executable(path: Path) -> bool:
    if not path.is_file():
        return False
    if os.name=='nt':
        return True
    return os.access(str(path),os.X_OK)


def _probe_path(path: Path, tool: str) -> Optional[str]:
    """Accept an executable, supported macOS .app, or distribution directory."""
    path=Path(os.path.expandvars(str(path))).expanduser()
    if _is_executable(path):
        return str(path.resolve())
    if path.is_dir():
        # Official macOS VICE packages have historically shipped tiny .app
        # launcher wrappers as well as a real command-line x64sc binary. If
        # the user gives us x64sc.app, prefer the sibling real binary so CLI
        # arguments and the PRG filename are not swallowed by the wrapper.
        if tool=='vice' and path.suffix.lower()=='.app':
            app_candidates=[
                path.parent/'VICE.app/Contents/Resources/bin/x64sc',
                path.parent/'bin/x64sc',
                path.parent/'tools/x64sc',
                path/'Contents/Resources/bin/x64sc',
                path/'Contents/MacOS/x64sc',
            ]
            for candidate in app_candidates:
                if _is_executable(candidate):
                    return str(candidate.resolve())
        if tool=='blender' and path.suffix.lower()=='.app':
            candidate=path/'Contents/MacOS/Blender'
            if _is_executable(candidate):
                return str(candidate.resolve())
        names=[]
        if tool=='vice':
            names=[
                Path('bin/x64sc'),
                Path('tools/x64sc'),
                Path('x64sc'),
                Path('x64sc.exe'),
                Path('VICE.app/Contents/Resources/bin/x64sc'),
                Path('x64sc.app/Contents/MacOS/x64sc'),
            ]
        elif tool=='tass':
            names=[Path('64tass'),Path('64tass.exe'),Path('bin/64tass'),Path('bin/64tass.exe')]
        else:
            names=[Path('blender'),Path('blender.exe'),Path('Blender.app/Contents/MacOS/Blender')]
        for rel in names:
            candidate=path/rel
            if _is_executable(candidate):
                return str(candidate.resolve())
    return None


def _existing_candidates(paths: Iterable[Path]):
    for p in paths:
        try:
            if _is_executable(p):
                yield str(p.resolve())
        except OSError:
            continue


def platform_candidates(tool: str, *, system: Optional[str] = None, home: Optional[Path] = None, env=None):
    """Return likely executable locations for the current host.

    PATH is always checked first by resolve_executable(); these are fallbacks
    for common native package layouts, especially macOS VICE bundles.
    """
    pkey=platform_key(system)
    home=Path.home() if home is None else Path(home)
    env=os.environ if env is None else env
    out=[]
    if pkey=='macos':
        if tool=='tass':
            out.extend([Path('/opt/homebrew/bin/64tass'),Path('/usr/local/bin/64tass')])
        elif tool=='vice':
            out.extend([Path('/opt/homebrew/bin/x64sc'),Path('/usr/local/bin/x64sc')])
            roots=[Path('/Applications'),home/'Applications',home/'Downloads']
            for root in roots:
                out.extend([
                    root/'x64sc.app/Contents/MacOS/x64sc',
                    root/'VICE.app/Contents/Resources/bin/x64sc',
                    root/'VICE/tools/x64sc',
                ])
                if root.exists():
                    for pat in (
                        'vice*/bin/x64sc',
                        'vice*/tools/x64sc',
                        'vice*/x64sc.app/Contents/MacOS/x64sc',
                        'vice*/VICE.app/Contents/Resources/bin/x64sc',
                    ):
                        out.extend(sorted(root.glob(pat)))
        else:
            out.extend([
                Path('/Applications/Blender.app/Contents/MacOS/Blender'),
                home/'Applications/Blender.app/Contents/MacOS/Blender',
                Path('/opt/homebrew/bin/blender'),Path('/usr/local/bin/blender'),
            ])
    elif pkey=='windows':
        pf=Path(env.get('ProgramFiles','C:/Program Files'))
        pf86=Path(env.get('ProgramFiles(x86)','C:/Program Files (x86)'))
        local=Path(env.get('LOCALAPPDATA',str(home/'AppData/Local')))
        if tool=='tass':
            out.extend([
                pf/'64tass/64tass.exe',pf86/'64tass/64tass.exe',
                local/'Programs/64tass/64tass.exe',
            ])
        elif tool=='vice':
            for base in (pf,pf86,local/'Programs'):
                out.extend([base/'VICE/x64sc.exe',base/'VICE/bin/x64sc.exe'])
        else:
            for base in (pf/'Blender Foundation',pf86/'Blender Foundation',local/'Programs'):
                if base.exists():
                    out.extend(sorted(base.glob('Blender*/blender.exe'),reverse=True))
    else:
        name={'tass':'64tass','vice':'x64sc','blender':'blender'}[tool]
        out.extend([Path('/usr/local/bin')/name,Path('/usr/bin')/name,home/'.local/bin'/name])
    # Preserve order while removing duplicates.
    seen=set(); unique=[]
    for p in out:
        s=str(p)
        if s not in seen:
            seen.add(s); unique.append(p)
    return unique


def resolve_executable(spec: str, tool: str, *, system: Optional[str] = None) -> Optional[str]:
    """Resolve executable name/path with cross-platform fallbacks."""
    spec=os.path.expandvars(os.path.expanduser(str(spec).strip().strip('"').strip("'")))
    if not spec:
        return None
    # Explicit paths/directories/.app bundles are probed directly.
    pathish=(os.sep in spec or (os.altsep and os.altsep in spec) or Path(spec).is_absolute() or spec.lower().endswith('.app'))
    if pathish:
        return _probe_path(Path(spec),tool)
    found=shutil.which(spec)
    if found:
        return str(Path(found).resolve())
    default_names={
        'tass':{'64tass','64tass.exe'},
        'vice':{'x64sc','x64sc.exe'},
        'blender':{'blender','blender.exe'},
    }[tool]
    if spec.lower() not in default_names:
        return None
    for candidate in _existing_candidates(platform_candidates(tool,system=system)):
        return candidate
    return None


def command(executable: str, args: Sequence[str], tail: Sequence[str] = ()):
    return [executable,*list(args),*list(tail)]
