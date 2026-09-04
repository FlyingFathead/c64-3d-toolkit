#!/usr/bin/env python3
"""Safely migrate pre-0.6.2 flat example artifacts into per-example directories.

Default is a dry run. Pass --apply to perform moves/removals. Existing destination
files are never overwritten: identical duplicates are removed from the old
location, while differing files are left in place with a warning.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXAMPLES=ROOT/'examples'

# Known pre-0.6.2 files that are intentionally superseded at the new location.
# We only remove them automatically when the old file is byte-exact, so local
# user edits are never discarded.
SUPERSEDED_OLD_HASHES={
    'examples/blender/examples.json': '11845e817013de15d67acfdf9877204c37f75cf35cc276cd08534288e86318bc',
    'examples/blender/falling_cubes_c64.py': '5a61b922e7b8cac0e41b5aedf809940e570eb47a80e023d582c95fa4b03c650e',
    'examples/blender/falling_cubes_full.py': 'bfc0f76613f156d1006fead6c1b72a88fb1b74ecc5e9aaad24444a156dde3cc5',
}

# Redundant historical aliases. v0.6.2 keeps their hashes in the legacy reference
# set but does not ship duplicate PRG bytes under these ambiguous names.
DEPRECATED_FLAT_HASHES={
    'space_horse_spin.prg': '2d30225116b63afb20ed2699ce3c49c50de506fac22487825ff5d8c5477ba46b',
    'space_horse_crawl.prg': '0c9536fa38b3192db59f00ea6b4e8dc686a66ae04404b083f61c8b577259f196',
}

FLAT_MAP={
    'cube.prg':'cube/cube.prg',
    'cube_no_overlay.prg':'cube/cube_no_overlay.prg',
    'cube_rastertime_profiler.prg':'cube/cube_rastertime_profiler.prg',
    'torus.prg':'torus/torus.prg',
    'torus_no_overlay.prg':'torus/torus_no_overlay.prg',
    'torus_rastertime_profiler.prg':'torus/torus_rastertime_profiler.prg',
    'torus_dense.prg':'torus_dense/torus_dense.prg',
    'torus_dense_no_overlay.prg':'torus_dense/torus_dense_no_overlay.prg',
    'torus_dense_rastertime_profiler.prg':'torus_dense/torus_dense_rastertime_profiler.prg',
    'sphere.prg':'sphere/sphere.prg',
    'sphere_no_overlay.prg':'sphere/sphere_no_overlay.prg',
    'sphere_rastertime_profiler.prg':'sphere/sphere_rastertime_profiler.prg',
    'horse_head.prg':'horse_head/horse_head.prg',
    'horse_head_no_overlay.prg':'horse_head/horse_head_no_overlay.prg',
    'horse_head_rastertime_profiler.prg':'horse_head/horse_head_rastertime_profiler.prg',
    'sunflower_torus.prg':'sunflower_torus/sunflower_torus.prg',
    'sunflower_torus_no_overlay.prg':'sunflower_torus/sunflower_torus_no_overlay.prg',
    'sunflower_torus_rastertime_profiler.prg':'sunflower_torus/sunflower_torus_rastertime_profiler.prg',
    'sunflower_torus_color.prg':'sunflower_torus/sunflower_torus_color.prg',
    'sunflower_torus_color_no_overlay.prg':'sunflower_torus/sunflower_torus_color_no_overlay.prg',
    'sunflower_torus_color_rastertime_profiler.prg':'sunflower_torus/sunflower_torus_color_rastertime_profiler.prg',
    'space_horse_spin_color.prg':'space_horse_spin/space_horse_spin_color.prg',
    'space_horse_spin_color_no_overlay.prg':'space_horse_spin/space_horse_spin_color_no_overlay.prg',
    'space_horse_spin_color_rastertime_profiler.prg':'space_horse_spin/space_horse_spin_color_rastertime_profiler.prg',
    'space_horse_crawl_color.prg':'space_horse_crawl/space_horse_crawl_color.prg',
    'space_horse_crawl_color_no_overlay.prg':'space_horse_crawl/space_horse_crawl_color_no_overlay.prg',
    'space_horse_crawl_color_rastertime_profiler.prg':'space_horse_crawl/space_horse_crawl_color_rastertime_profiler.prg',
    'falling_cubes_c64_color-yunroll.prg':'blender_falling_cubes/falling_cubes_c64_color-yunroll.prg',
    'falling_cubes_c64_color-yunroll_no_overlay.prg':'blender_falling_cubes/falling_cubes_c64_color-yunroll_no_overlay.prg',
    'falling_cubes_c64_color-yunroll_rastertime_profiler.prg':'blender_falling_cubes/falling_cubes_c64_color-yunroll_rastertime_profiler.prg',
    'falling_cubes_c64-yunroll.prg':'blender_falling_cubes/falling_cubes_c64-yunroll.prg',
    'falling_cubes_c64-yunroll_no_overlay.prg':'blender_falling_cubes/falling_cubes_c64-yunroll_no_overlay.prg',
    'falling_cubes_c64-yunroll_rastertime_profiler.prg':'blender_falling_cubes/falling_cubes_c64-yunroll_rastertime_profiler.prg',
}


def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def migrate(src:Path,dst:Path,apply:bool)->tuple[int,int,int]:
    if not src.exists(): return (0,0,0)
    if dst.exists():
        if src.is_file() and dst.is_file():
            src_hash=digest(src); dst_hash=digest(dst)
            if src_hash==dst_hash:
                print(f'IDENTICAL  {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}')
                if apply: src.unlink()
                return (0,1,0)
            rel=src.relative_to(ROOT).as_posix()
            if SUPERSEDED_OLD_HASHES.get(rel)==src_hash:
                print(f'SUPERSEDED {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}')
                if apply: src.unlink()
                return (0,1,0)
        print(f'CONFLICT   {src.relative_to(ROOT)} != {dst.relative_to(ROOT)} (left untouched)')
        return (0,0,1)
    print(f'MOVE       {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}')
    if apply:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(src),str(dst))
    return (1,0,0)


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--apply',action='store_true',help='perform the migration (default: dry run)')
    args=ap.parse_args()
    moved=removed=conflicts=0
    for src_name,expected_hash in DEPRECATED_FLAT_HASHES.items():
        src=EXAMPLES/src_name
        if not src.exists():
            continue
        if src.is_file() and digest(src)==expected_hash:
            print(f'DEPRECATED {src.relative_to(ROOT)} (duplicate historical alias)')
            if args.apply: src.unlink()
            removed+=1
        else:
            print(f'CONFLICT   {src.relative_to(ROOT)} differs from known duplicate alias (left untouched)')
            conflicts+=1
    for src_name,dst_name in FLAT_MAP.items():
        a,b,c=migrate(EXAMPLES/src_name,EXAMPLES/dst_name,args.apply); moved+=a; removed+=b; conflicts+=c
    old=EXAMPLES/'blender'; new=EXAMPLES/'blender_falling_cubes'
    if old.is_dir():
        for src in sorted(old.iterdir()):
            a,b,c=migrate(src,new/src.name,args.apply); moved+=a; removed+=b; conflicts+=c
        if args.apply:
            try: old.rmdir(); print(f'REMOVED    {old.relative_to(ROOT)}/ (empty)')
            except OSError: pass
    print(f'\nsummary: {moved} moved, {removed} identical old copies removable, {conflicts} conflicts')
    if not args.apply: print('dry run only; re-run with --apply to perform the migration')
    return 2 if conflicts else 0

if __name__=='__main__': raise SystemExit(main())
