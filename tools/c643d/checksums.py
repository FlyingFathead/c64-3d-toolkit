from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def load_checksum_manifest(path: str | Path) -> dict:
    p=Path(path)
    data=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema')!=1:
        raise ValueError(f'unsupported PRG checksum manifest: {p}')
    sets=data.get('reference_sets')
    if not isinstance(sets,dict) or not sets:
        raise ValueError(f'PRG checksum manifest has no reference_sets: {p}')
    return data


def reference_set(data: dict, name: str | None=None) -> tuple[str,dict]:
    selected=name or data.get('default_reference_set')
    if not selected:
        raise ValueError('PRG checksum manifest has no default_reference_set')
    sets=data['reference_sets']
    if selected not in sets:
        raise ValueError(f'unknown PRG checksum reference set {selected!r}; available: {", ".join(sets)}')
    ref=sets[selected]
    if not isinstance(ref,dict) or not isinstance(ref.get('files'),dict):
        raise ValueError(f'invalid PRG checksum reference set: {selected}')
    return selected,ref


def compare_prg(path: str | Path, ref: dict, *, filename: str | None=None) -> dict:
    p=Path(path)
    key=filename or p.name
    actual_sha=sha256_file(p)
    actual_size=p.stat().st_size
    expected=ref.get('files',{}).get(key)
    if expected is None:
        status='ABSENT'
        expected_sha=None
        expected_size=None
    else:
        expected_sha=str(expected.get('sha256','')).lower()
        expected_size=int(expected.get('size',-1))
        status='MATCHING' if actual_sha==expected_sha and actual_size==expected_size else 'CHANGED'
    return {
        'filename':key,'status':status,
        'actual_sha256':actual_sha,'actual_size':actual_size,
        'expected_sha256':expected_sha,'expected_size':expected_size,
    }
