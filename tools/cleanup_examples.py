#!/usr/bin/env python3
"""Archive known old prebuilt examples outside the checkout after v2 installation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def cleanup(root=ROOT, *, archive=None, apply=False):
    root=Path(root).resolve()
    archive=Path(archive or root.parent/'c64-3d-toolkit-history'/'pre-hors-v2').resolve()
    if archive==root or root in archive.parents: raise ValueError('Archive must be outside the checkout')
    index=json.loads((root/'examples/release-index.json').read_text())
    # Check every replacement before moving even the first old file.
    for row in index['files']:
        path=root/row['path']
        if not path.is_file() or digest(path)!=row['sha256']:
            raise ValueError('Replacement missing or modified: '+row['path']+'; rebuild the release/index first')
    plan=[]
    for name in json.loads((root/'assets/legacy-example-files.json').read_text()):
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='examples': raise ValueError('Invalid archive path')
        source=root/rel
        if not source.exists():continue
        if source.is_symlink() or any(p.is_symlink() for p in source.parents if p!=root): raise ValueError('Symlink in archive source')
        sha=digest(source);dest=archive/rel
        if dest.exists() and digest(dest)!=sha: dest=archive/'local-modified'/sha/rel
        if dest.exists() and digest(dest)!=sha: raise ValueError('Archive collision: '+str(dest))
        plan.append((source,dest,sha))
    for source,dest,sha in plan:
        if apply:
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copy2(source,dest)
            if digest(dest)!=sha: raise ValueError('Archive verification failed: '+str(dest))
            source.unlink()
    print(('Archived' if apply else 'Would archive'),len(plan),'known old example files to',archive)
    return len(plan)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path)
    p.add_argument('--apply',action='store_true',help='Move files after validating replacements; default shows the plan count')
    a=p.parse_args();cleanup(archive=a.archive,apply=a.apply)


if __name__=='__main__':main()
