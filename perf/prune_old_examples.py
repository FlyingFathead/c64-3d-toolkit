#!/usr/bin/env python3
"""Move obsolete generated examples completely outside the Git checkout."""
import hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FOLDERS=('cart_demos','cart_marbles','cart_horse_and_sunflower')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=ROOT.resolve();archive=root.parent/'c64-3d-toolkit-history'
    if (root/'VERSION').read_text().strip()not in ('0.7.0','0.7.1'):raise SystemExit('Expected VERSION 0.7.0 or 0.7.1')
    version=(root/'VERSION').read_text().strip()
    current=root/'examples/cart_marbles/marbles-hors-render-v1-16fps-force-bytes.crt'
    if not current.is_file():raise SystemExit('Main Marbles cart missing; apply examples-cleanup-03 first')
    paths=[]
    for name in FOLDERS:
        folder=root/'examples'/name
        history=folder/'history'
        if history.exists():paths.extend(p for p in history.rglob('*') if p.is_file())
        # Catch older versioned outputs left at top level by earlier upgrades.
        for p in folder.rglob('*'):
            if not p.is_file() or 'history' in p.relative_to(folder).parts:continue
            if (name=='cart_demos' and version=='0.7.1' and p.name.startswith('c643d-demo-v0.7.0-')) or 'yunroll-cart-v' in p.name or (name=='cart_marbles' and p.name.startswith('dont_lose_your_marbles-hors-render-v1-')):
                paths.append(p)
    hifi=root/'examples/hifi_showcase'
    if hifi.exists():
        paths.extend(p for p in hifi.rglob('*') if p.is_file()
                     and p.name != 'README.md'
                     and not p.name.startswith('horse_head_hifi-hors-render-v1'))
    planned=[]
    for p in sorted(set(paths)):
        if p.is_symlink():raise SystemExit(f'Unexpected symlink: {p}')
        rel=p.relative_to(root);dest=archive/rel
        if dest.exists() and sha(dest)!=sha(p):dest=archive/'local-modified'/sha(p)/rel
        if dest.exists() and sha(dest)!=sha(p):raise SystemExit(f'Archive collision: {dest}')
        planned.append((p,dest,p.stat().st_size))
    total=sum(n for _,_,n in planned)
    for p,dest,_ in planned:
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():p.unlink() # An identical external copy was verified.
        else:shutil.move(p,dest)
    for folder in [root/'examples'/n for n in FOLDERS]+[hifi]:
        if not folder.exists():continue
        for d in sorted((p for p in folder.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
            if not any(d.iterdir()):d.rmdir()
        if folder==hifi and not any(folder.iterdir()):folder.rmdir()
    print(f'Removed {len(planned)} obsolete files ({total/1024/1024:.2f} MiB) from the checkout.')
    print(f'External archive: {archive}')
    print('Current cartridges, Blender sources and renderer implementations retained.')
    print('Use git add -A when preparing your commit to record the removals.')
if __name__=='__main__':main()
