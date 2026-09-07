"""Companion metadata for current carts, with support for older flat bundles."""
from pathlib import Path


def menu_manifest_path(crt):
    crt = Path(crt)
    filename = crt.stem + '-cart-manifest.json'
    current = crt.parent / 'metadata' / filename
    return current if current.is_file() else crt.with_name(filename)
