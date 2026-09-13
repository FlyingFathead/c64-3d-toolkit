#!/usr/bin/env python3
"""Record the exact stable examples which cleanup and installation must preserve."""
import hashlib,json
from pathlib import Path

from c643d.released_examples import is_current_v2_example, is_legacy_cart_output

ROOT=Path(__file__).resolve().parents[1]


def main():
    paths=[]
    for p in (ROOT/'examples').rglob('*'):
        if not p.is_file() or p.suffix not in ('.crt','.lbl','.json','.txt'):continue
        if is_legacy_cart_output(p):continue
        if is_current_v2_example(p,(ROOT/'VERSION').read_text().strip()) or 'color_combo_test' in p.parts or 'hors_v3_preview' in p.parts or 'stanford_dragon' in p.parts or 'saku_2026' in p.parts or 'blender_viewport_test' in p.parts:
            paths.append(p)
    carts=[p for p in paths if p.suffix=='.crt']
    if len(carts)<19:raise ValueError('Expected every stable v2 example to be built')
    index=dict(version=(ROOT/'VERSION').read_text().strip(),renderer='hors-renderer-v3',menu_renderer='hors-render-v2',
        renderers=['hors-render-v2','hors-renderer-v3'], cartridges=len(carts),files=[dict(path=p.relative_to(ROOT).as_posix(),
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)])
    (ROOT/'examples/release-index.json').write_text(json.dumps(index,indent=2)+'\n')
    print('Indexed',len(carts),'stable cartridges and',len(paths),'files')


if __name__=='__main__':main()
