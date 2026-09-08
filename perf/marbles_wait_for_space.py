#!/usr/bin/env python3
"""Remove startup timeout from the accepted Marbles cart, without rebuilding."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEM='marbles-hors-render-v1-16fps-force-bytes'
ORIGINAL='ab46a6a8052879f33b78fce422b8e131da8dfdfe74950328d3286f99855e0b58'
PATTERN=bytes.fromhex('a296ad01dc2910f018ad12d0c9faf0f2ad01dc2910f00aad12d0c9fad0f2cad0e1')
def patch(data):
    b=bytearray(data)
    canonical=bytearray(b);canonical[32:64]=b"DON'T LOSE YOUR MARBLES".ljust(32,b'\0')
    done=PATTERN[:-3]+bytes.fromhex('1890e1')
    if canonical.count(done)==1:
        canonical[canonical.index(done)+30:canonical.index(done)+33]=bytes.fromhex('cad0e1')
        if hashlib.sha256(canonical).hexdigest()==ORIGINAL:return bytes(b)
    if hashlib.sha256(canonical).hexdigest()!=ORIGINAL:
        raise ValueError('Expected the accepted 16 FPS force-bytes cart; no files changed')
    if b.count(PATTERN)!=1:raise ValueError('Startup loop signature mismatch')
    b[b.index(PATTERN)+30:b.index(PATTERN)+33]=bytes.fromhex('1890e1')
    return bytes(b)
def main():
    d=ROOT/'examples/cart_marbles';p=d/(STEM+'.crt')
    original=p.read_bytes();updated=patch(original)
    meta=d/(STEM+'-manifest.json');manifest=json.loads(meta.read_text()) if meta.exists() else None
    if updated!=original:
        backup=ROOT.parent/'c64-3d-toolkit-history'/'examples/cart_marbles/history/startup-auto';backup.mkdir(parents=True,exist_ok=True)
        saved=backup/p.name
        if saved.exists() and saved.read_bytes()!=original:raise ValueError('Backup conflict; no files changed')
        saved.write_bytes(original)
        temp=p.with_suffix('.crt.tmp');temp.write_bytes(updated);temp.replace(p)
    if manifest is not None:
        manifest.setdefault('build_screen',{}).update(ticks=None,wait_for_space=True,skip_key='SPACE')
        manifest['startup_patch']='SPACE required; original animation payload unchanged'
        meta.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Marbles now waits indefinitely for SPACE before the intro. No rerender performed.')
if __name__=='__main__':main()
