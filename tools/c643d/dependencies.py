"""Read our requirement files and check imports before loading build modules.

This bootstrap deliberately uses only the standard library. The checked-in
files use numeric >= and < bounds; unsupported syntax fails visibly instead
of silently dropping a requirement. pip remains responsible for installation.
"""
import importlib
from importlib import metadata
from pathlib import Path
import re
import shlex
import sys

ROOT = Path(__file__).resolve().parents[2]
MODULES = {'numpy': 'numpy', 'pillow': 'PIL.Image', 'cairosvg': 'cairosvg', 'defusedxml': 'defusedxml.ElementTree'}


def requirements(svg=False, root=ROOT):
    found = {}
    def read(path):
        for raw in path.read_text().splitlines():
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            if line.startswith('-r '):
                read(path.parent / line[3:].strip())
                continue
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)((?:(?:>=|<)[0-9.]+)(?:,(?:>=|<)[0-9.]+)*)?', line)
            if not match or match[1].lower() not in MODULES:
                raise ValueError('Unsupported dependency declaration: ' + line)
            found[match[1].lower()] = (match[1], match[2] or '')
    read(Path(root) / ('requirements.txt' if svg else 'requirements-core.txt'))
    return list(found.values())


def satisfies(version, bounds):
    match = re.match(r'^(\d+(?:\.\d+)*)(.*)$', version)
    if not match:
        return False
    actual = tuple(map(int, match[1].split('.')))
    prerelease = bool(re.match(r'(?:a|b|rc|\.dev)', match[2]))
    for op, value in re.findall(r'(>=|<)([0-9.]+)', bounds):
        wanted = tuple(map(int, value.split('.')))
        width = max(len(actual), len(wanted))
        a = actual + (0,) * (width - len(actual))
        b = wanted + (0,) * (width - len(wanted))
        if op == '>=' and (a < b or (a == b and prerelease)):
            return False
        if op == '<' and a >= b:
            return False
    return True


def inspect(svg=False):
    rows = []
    for name, bounds in requirements(svg):
        try:
            version = metadata.version(name)
            if not satisfies(version, bounds):
                raise RuntimeError('installed ' + version + '; requires ' + name + bounds)
            importlib.import_module(MODULES[name.lower()])
            rows.append(dict(name=name, requirement=name+bounds, ok=True, version=version))
        except metadata.PackageNotFoundError:
            rows.append(dict(name=name, requirement=name+bounds, ok=False, reason='not installed in this Python'))
        except Exception as exc:
            rows.append(dict(name=name, requirement=name+bounds, ok=False, reason=str(exc)))
    return rows


def python_command(arguments):
    parts = [sys.executable, *arguments]
    if sys.platform == 'win32':
        return '& ' + ' '.join("'" + p.replace("'", "''") + "'" for p in parts)
    return shlex.join(parts)


def installer_command(svg=False):
    return python_command([str(ROOT/'setup-python.py')])


def check(svg=False, verbose=False, stream=None):
    stream = stream or sys.stderr
    try:
        rows = inspect(svg)
    except (OSError, ValueError) as exc:
        print('error: cannot read Python requirements: ' + str(exc), file=stream)
        print('Restore requirements.txt, requirements-core.txt and requirements-svg.txt from the toolkit release.', file=stream)
        return False
    failed = [r for r in rows if not r['ok']]
    if verbose or failed:
        print('Python dependencies: ' + sys.executable, file=stream)
        for row in rows:
            if verbose or not row['ok']:
                print('  ' + row['requirement'] + ': ' + (row.get('version', 'OK') if row['ok'] else row['reason']), file=stream)
    if failed:
        print('error: required Python libraries are missing, too old or unable to load.', file=stream)
        print('Run the dependency installer with this same Python, then retry:', file=stream)
        if sys.platform == 'win32':
            print('In PowerShell (the command below uses the exact failing Python):', file=stream)
        print('  ' + installer_command(svg), file=stream)
        print('Or install the reported packages directly:', file=stream)
        print('  ' + python_command(['-m','pip','install',*[r['requirement'] for r in failed]]), file=stream)
        print('Use --repair if already installed but broken. See docs/INSTALLATION.md.', file=stream)
        if svg:
            print('CairoSVG also needs the native Cairo library; see docs/SVG_PIPELINE.md.', file=stream)
    return not failed
