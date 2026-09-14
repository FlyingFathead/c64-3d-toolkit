#!/usr/bin/env python3
"""Save a numbered cumulative source checkpoint without overwriting an archive."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

try:
    from .compile_release import source_files
except ImportError:
    from compile_release import source_files

ROOT=Path(__file__).resolve().parents[1]


def checkpoint(root, destination, *, baseline=None, full=False, completed=(), pending=(), validation=()):
    root=Path(root).resolve();destination=Path(destination).expanduser().resolve()
    if destination==root or root in destination.parents:
        raise ValueError('Checkpoint destination must be outside the checkout')
    version=(root/'VERSION').read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]+',version):raise ValueError('Invalid VERSION filename component')
    destination.mkdir(parents=True,exist_ok=True)
    prior=[]
    for p in destination.glob('c64-3d-toolkit-*-cp*.zip'):
        match=re.search(r'-cp(\d+)-',p.name)
        if match:prior.append(int(match.group(1)))
    number=max(prior,default=0)+1
    prefix=f'c64-3d-toolkit-v{version}-cp{number:03d}'
    old={};baseline_sha=None
    if baseline is not None:
        baseline=Path(baseline)
        baseline_sha=hashlib.sha256(baseline.read_bytes()).hexdigest()
        with zipfile.ZipFile(baseline) as z:
            roots=[n[:-len('VERSION')] for n in z.namelist() if n=='VERSION' or n=='c64-3d-toolkit/VERSION']
            if len(roots)!=1:raise ValueError('Baseline must have one toolkit root with VERSION')
            anchor=roots[0]
            old={n[len(anchor):]:hashlib.sha256(z.read(n)).hexdigest()
                 for n in z.namelist() if n.startswith(anchor) and not n.endswith('/')}
    full=full or baseline is None
    current={p.relative_to(root).as_posix():p for p in source_files(root)}
    hashes={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in current.items()}
    included={n:p for n,p in current.items() if full or old.get(n)!=hashes[n]}
    # Deleted files are explicitly recorded; applying an overlay never deletes automatically.
    deleted=sorted(n for n in old if n not in current and not any(
        part in ('build','logs','.git','__pycache__','.pytest_cache','comparison-tests') for part in Path(n).parts)
        and n!='config/c643d.ini' and Path(n).suffix not in ('.zip','.pyc'))
    kind='full' if full else 'incremental'
    target=destination/f'{prefix}-{kind}.zip'
    status=dict(checkpoint=number,version=version,kind=kind,created_utc=datetime.now(timezone.utc).isoformat(),
        baseline_sha256=baseline_sha,completed=list(completed),pending=list(pending),validation=list(validation),
        deleted_paths=deleted,files={n:hashes[n] for n in included},
        apply='Extract from the parent of c64-3d-toolkit. Incrementals are cumulative against the named baseline. Review deleted_paths manually.')
    # Exclusive creation is intentional: concurrent runs cannot overwrite a previous checkpoint.
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n,p in sorted(included.items()):z.write(p,'c64-3d-toolkit/'+n)
        z.writestr(f'c64-3d-toolkit/docs/checkpoints/{prefix}.json',json.dumps(status,indent=2)+'\n')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(f'{digest}  {target.name}\n')
    return target,status


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--baseline-zip',type=Path)
    p.add_argument('--full',action='store_true',help='save a full source snapshot, even with a baseline')
    p.add_argument('--done',action='append',default=[])
    p.add_argument('--pending',action='append',default=[])
    p.add_argument('--validation',action='append',default=[],help='record actual check results; this command does not run tests')
    a=p.parse_args(argv)
    try:
        target,status=checkpoint(ROOT,a.destination,baseline=a.baseline_zip,full=a.full,
            completed=a.done,pending=a.pending,validation=a.validation)
    except (OSError,ValueError,zipfile.BadZipFile) as exc:
        p.error(str(exc))
    print(f'Saved {target.name}: {len(status["files"])} files, {target.stat().st_size} bytes')
    print(target)
    if status['deleted_paths']:print('Review deleted_paths in the checkpoint record before applying.')
    return 0

if __name__=='__main__':sys.exit(main())
