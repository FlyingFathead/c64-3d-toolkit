"""Exact resident regression inputs, kept out of active example folders."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile


def materialize(root):
    root=Path(root);result=[]
    for row in json.loads(gzip.decompress((root/'assets/resident-regression-inputs.json.gz').read_bytes())):
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts: raise ValueError('Unsafe reference path')
        data=bytes.fromhex(row['data'])
        if hashlib.sha256(data).hexdigest()!=row['sha256']: raise ValueError('Resident fixture hash differs')
        dest=root/'build/reference-prgs'/rel
        if not dest.exists() or dest.read_bytes()!=data:
            dest.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(dir=dest.parent,prefix='.reference-')
            try:
                with os.fdopen(fd,'wb') as out: out.write(data)
                os.replace(tmp,dest)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        if row['title'] is not None: result.append((row['title'],dest))
    return tuple(result)
