#!/usr/bin/env python3
"""Move obsolete examples and generated videos into a ZIP outside the project.

Run after applying the 0.6.7 overlay. Every selected file is archived and
verified before removal. Local edits are preserved; Git's index is untouched.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from .archive_old_carts import OLD_FILES
except ImportError:
    from archive_old_carts import OLD_FILES


VIDEO_SUFFIXES = {'.mp4', '.m4v', '.mov', '.webm', '.mkv', '.avi'}
RC_MENU = re.compile(r'c643d-demo-v0\.6\.7-rc[1-5]-yunroll-cart-v7-all'
                     r'(?:-ram)?(?:\.crt|-cart-manifest\.json|-cart-map\.txt)$')
COMPARISON_FILES = {
    stem + suffix
    for stem in ('c643d-demo-v0.6.5-yunroll-cart-v4-all',
                 'c643d-demo-v0.6.7-rc2-yunroll-cart-v5-all',
                 'c643d-demo-v0.6.7-rc3-yunroll-cart-v6-all')
    for suffix in ('.crt', '-cart-manifest.json', '-cart-map.txt')
}
OLD_REPORTS = {
    'menu-launch-v4-validation.json', 'scroll-menu-validation.json',
    'scroll-menu-preview.png', 'v5-v6-validation.json', 'v6-v7-validation.json',
    'menu-v7-validation.json', 'menu-launch-v7-validation.json',
    'play-all-v7-validation.json', 'menu-launch-rc5-validation.json',
    'play-all-rc5-validation.json', 'play-all-thanks-rc5-validation.json',
    'play-all-thank-you.png',
}


def candidates(root):
    root = Path(root).resolve()
    found = set()
    examples = root / 'examples'
    if examples.is_symlink():
        raise ValueError('Refusing a symlinked examples directory')
    for current, directories, files in os.walk(examples, followlinks=False):
        current = Path(current)
        # Do not traverse or remove symlinks, even inside examples/old.
        for name in directories:
            if (current / name).is_symlink():
                raise ValueError(f'Refusing symlink: {current / name}')
        for name in files:
            path = current / name
            relative = path.relative_to(root)
            legacy = relative.parts[:2] == ('examples', 'old')
            obsolete_menu = current in (examples / 'cart_demos', examples / 'cart_demos/metadata') and (
                name in OLD_FILES or name in COMPARISON_FILES or RC_MENU.fullmatch(name))
            relocated_report = current == examples / 'cart_demos' and name in OLD_REPORTS
            generated = path.suffix.lower() in VIDEO_SUFFIXES or re.search(r'\.blend\d+$', name)
            if legacy or obsolete_menu or relocated_report or generated:
                if path.is_symlink() or not path.is_file():
                    raise ValueError(f'Refusing non-regular file: {path}')
                found.add(relative)
    # Also catch accidentally copied generated videos/backups at the root.
    for path in root.iterdir():
        if path.suffix.lower() in VIDEO_SUFFIXES or re.search(r'\.blend\d+$', path.name):
            if path.is_symlink() or not path.is_file():
                raise ValueError(f'Refusing non-regular file: {path}')
            found.add(path.relative_to(root))
    return sorted(found)


def clean(root, archive_path=None, dry_run=False):
    root = Path(root).resolve()
    paths = candidates(root)
    size = sum((root / p).stat().st_size for p in paths)
    if not paths:
        print('No obsolete files to archive.')
        return dict(files=0, bytes=0, archive=None)
    target = Path(archive_path) if archive_path else root.parent / 'c64-3d-toolkit-legacy-pre-0.6.7.zip'
    target = target.absolute()
    if target.resolve().is_relative_to(root):
        raise ValueError('The archive must be outside the project directory')
    if target.is_symlink():
        raise ValueError('Refusing a symlink archive destination')
    if dry_run:
        for path in paths:
            print(path.as_posix())
        print(f'{len(paths)} files / {size:,} bytes would be archived outside the project.')
        return dict(files=len(paths), bytes=size, archive=str(target))

    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=target.stem + '-', suffix='.zip', dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    digests = {}
    try:
        with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in paths:
                path = root / relative
                digests[relative] = hashlib.sha256(path.read_bytes()).digest()
                archive.write(path, relative.as_posix())
        # Verify the archived bytes and current originals before removing any.
        with ZipFile(temporary) as archive:
            for relative, digest in digests.items():
                if hashlib.sha256(archive.read(relative.as_posix())).digest() != digest:
                    raise ValueError(f'Archive verification failed: {relative}')
                if hashlib.sha256((root / relative).read_bytes()).digest() != digest:
                    raise ValueError(f'File changed while archiving: {relative}; nothing removed')
        try:
            # A hard link publishes the complete file without overwriting an
            # existing archive. Both paths live on the same filesystem.
            os.link(temporary, target)
            temporary.unlink()
        except FileExistsError:
            target = temporary  # Preserve both the existing and new archives.
        for relative, digest in digests.items():
            path = root / relative
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).digest() != digest:
                raise ValueError(f'File changed; kept {relative}. Archive: {target}')
            path.unlink()
        old = root / 'examples/old'
        if old.is_dir():
            for directory, _, _ in os.walk(old, topdown=False):
                try:
                    Path(directory).rmdir()
                except OSError:
                    pass
        print(f'Archived {len(paths)} files / {size:,} bytes to {target}')
        print('Run git add -A when committing to record removal of previously tracked files.')
        return dict(files=len(paths), bytes=size, archive=str(target))
    except BaseException:
        # Keep a completed archive if publication succeeded or removal began.
        if temporary.exists() and target != temporary:
            temporary.unlink()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--archive', type=Path, help='ZIP destination outside the project')
    args = parser.parse_args()
    clean(Path(__file__).resolve().parents[1], args.archive, args.dry_run)
