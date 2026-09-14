"""Preserve VICE logs in ignored storage and keep generated logs out of Git."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def _new_log(root, label='monitor'):
    directory = Path(root).resolve() / 'logs'
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    fd, name = tempfile.mkstemp(prefix=f'{label}-{stamp}-', suffix='.log', dir=directory)
    os.close(fd)
    return Path(name)


def _digest(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
        return digest.digest()


def archive_monitor_log(source, root):
    """Copy, verify, then remove a stale log; never overwrite an earlier copy."""
    source = Path(source)
    if source.is_symlink():
        raise OSError(f'Refusing to rotate a symbolic-link monitor log: {source}')
    if not source.exists():
        return None
    before = source.stat()
    target = _new_log(root)
    try:
        with source.open('rb') as src, target.open('wb') as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        after = source.stat()
        identity = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        if identity(before) != identity(after) or _digest(source) != _digest(target):
            raise OSError(f'Monitor log changed during archival; original retained: {source}')
        source.unlink()
    except OSError:
        # Retain any partial copy for diagnosis; the source is never removed
        # until its complete copy has been verified.
        raise
    return target


def archive_root_monitor(root=ROOT):
    return archive_monitor_log(Path(root) / 'monitor.log', root)


def vice_monitor_args(args=(), *, root=ROOT):
    """Keep an explicit diagnostic filename; otherwise allocate an ignored log."""
    options = list(args)
    if '-monlogname' in options:
        index = options.index('-monlogname')
        if index + 1 == len(options):
            raise ValueError('-monlogname requires a filename')
        name = options[index + 1]
    else:
        name = str(_new_log(root, 'vice-monitor'))
    # VICE opens the file immediately at -monlog. Select its name first,
    # including after resource resets, before any logging can be enabled.
    result = (['-console'] if '-console' in options else []) + ['-monlogname', name]
    for arg in options:
        if arg == '-console':
            continue
        result.append(arg)
        if arg == '-default':
            result += ['-monlogname', name]
    return result


def untrack_monitor_logs(root=ROOT):
    """Archive working/index copies of tracked monitor.log files before untracking."""
    root = Path(root).resolve()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root)
    names = sorted({os.fsdecode(n) for n in tracked.split(b'\0')
                    if n and Path(os.fsdecode(n)).name == 'monitor.log'})
    for name in names:
        staged = subprocess.check_output(['git', 'show', ':' + name], cwd=root)
        backup = _new_log(root, 'monitor-index')
        with backup.open('wb') as stream:
            stream.write(staged)
            stream.flush()
            os.fsync(stream.fileno())
        if backup.read_bytes() != staged:
            raise OSError(f'Could not verify staged monitor log backup: {name}')
        archive_monitor_log(root / name, root)
        subprocess.run(['git', 'rm', '--cached', '--force', '--', name], cwd=root, check=True)
    return names
