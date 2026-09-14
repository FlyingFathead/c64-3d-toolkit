#!/usr/bin/env python3
"""Install/check/repair Python requirements in the interpreter running this file."""
import argparse
from pathlib import Path
import subprocess
import sys
from tools.c643d import dependencies


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='check only; never install')
    p.add_argument('--repair', action='store_true', help='force reinstall without the pip cache')
    profile=p.add_mutually_exclusive_group()
    profile.add_argument('--svg', dest='svg', action='store_true', help='full installation including SVG (default)')
    profile.add_argument('--core', dest='svg', action='store_false', help='explicit minimal installation without SVG support')
    p.set_defaults(svg=True)
    a = p.parse_args(argv)
    if a.check and a.repair:
        p.error('--check and --repair are mutually exclusive')
    if a.check:
        return 0 if dependencies.check(a.svg, verbose=True, stream=sys.stdout) else 2
    root = Path(__file__).resolve().parent
    requirement = root / ('requirements.txt' if a.svg else 'requirements-core.txt')
    print('Installing for Python: ' + sys.executable, flush=True)
    cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(requirement)]
    if a.repair:
        cmd += ['--force-reinstall', '--no-cache-dir']
    try:
        result = subprocess.run(cmd, cwd=root, check=False)
    except OSError as exc:
        print('error: could not start pip: ' + str(exc), file=sys.stderr)
        return 2
    if result.returncode:
        print('error: dependency installation failed; see pip output above.', file=sys.stderr)
        print('Linux: use a virtual environment (see docs/INSTALLATION.md). No system Python override is used.', file=sys.stderr)
        return 2
    # Import only after pip completes, in a fresh process for repaired libraries.
    return subprocess.run([sys.executable, str(Path(__file__).resolve()), '--check'] + ([] if a.svg else ['--core']), check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
