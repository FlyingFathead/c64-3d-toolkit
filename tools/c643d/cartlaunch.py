"""Consistent VICE attachment for the toolkit's read-only EasyFlash demos."""
from pathlib import Path
import subprocess
from .cartridge import inspect_easyflash_crt
from .monitor_logs import vice_monitor_args


def command(vice, crt, args=(), *, clean_settings=False):
    crt = Path(crt).expanduser().resolve()
    if not crt.is_file():
        raise ValueError(f'Cartridge does not exist: {crt}')
    inspect_easyflash_crt(crt)
    # Keep ordinary runs on the user's configuration. Recovery resets resources
    # in this process only; never save these temporary launch settings on exit.
    # Explicit user options can select Warp/fullscreen/NTSC for diagnostics.
    defaults = ['-default'] if clean_settings else []
    # VICE can initialize GTK while processing display options. Select console
    # mode before them, so diagnostics also work without a display server.
    console = ['-console'] if '-console' in args else []
    window = [] if console else ['+VICIIfull']
    options = vice_monitor_args([arg for arg in args if arg != '-console'])
    return [str(vice), *console, *defaults, '-pal', *window, '+warp', '+easyflashcrtwrite', *options,
            '+saveres', '+easyflashcrtwrite', '+cart', '-cartcrt', str(crt)]


def run(vice, crt, args=(), *, clean_settings=False, cwd=None):
    argv = command(vice, crt, args, clean_settings=clean_settings)
    print('+', ' '.join(argv), flush=True)
    return subprocess.run(argv, cwd=cwd, check=False).returncode
