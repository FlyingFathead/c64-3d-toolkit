#!/usr/bin/env python3
"""Archive superseded bundled carts after applying an update ZIP.

Only the explicit old release filenames below are touched. Local modifications
are preserved alongside the bundled archive with a content-hash suffix.
Safe to run repeatedly, from any working directory.
"""
import argparse
import hashlib
from pathlib import Path


OLD_FILES = tuple(
    stem + suffix
    for stem in ('c643d-demo', 'c643d-demo-v0.6.4',
                 'c643d-demo-v0.6.4-yunroll-cart-v3')
    for suffix in ('.crt', '-cart-manifest.json', '-cart-map.txt')
) + (
    'horse-hifi-stream-validation.json', 'sunflower-hifi-stream-validation.json',
    'horse-hifi-v3-stream-validation.json', 'sunflower-hifi-v3-stream-validation.json',
    'menu-validation.json', 'menu-v3-validation.json',
)


def archive(root, dry_run=False):
    source = Path(root) / 'examples/cart_demos'
    archive_dir = Path(root) / 'examples/old/cart_demos'
    count = 0
    for name in OLD_FILES:
        old = source / name
        if not old.exists():
            continue
        if old.is_symlink() or not old.is_file():
            raise ValueError(f'Refusing non-regular file: {old}')
        content = old.read_bytes()
        target = archive_dir / name
        if target.exists() and target.read_bytes() != content:
            digest = hashlib.sha256(content).hexdigest()
            target = target.with_name(f'{target.stem}-local-{digest}{target.suffix}')
        if target.is_symlink():
            raise ValueError(f'Refusing symlink destination: {target}')
        print(f'{old.relative_to(root)} -> {target.relative_to(root)}')
        if not dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.read_bytes() != content:
                    raise ValueError(f'Archive conflict: {target}')
                old.unlink()  # Identical bytes already preserved at target.
            else:
                old.rename(target)
        count += 1
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    count = archive(Path(__file__).resolve().parents[1], args.dry_run)
    print(f'{count} old files {"would be archived" if args.dry_run else "archived"}.')
