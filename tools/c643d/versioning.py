"""One toolkit version source; stamp presentation copies, never old assembly."""
from pathlib import Path
import re


def read_version(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[2]
    version=(root/'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?',version):
        raise ValueError('VERSION must contain a toolkit version such as 0.7.2')
    return version


def stamp_menu_source(source,version):
    """Update version-bearing toolkit title text in a generated assembly copy."""
    return re.sub(r'(TOOLKIT\s+)[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?',
                  lambda match:match[1]+version,source)
