"""Check every indexed release CRT through the real shared VICE launcher."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--vice', required=True)
    p.add_argument('--vice-data', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--only', help='Optional substring of the indexed cartridge path')
    a = p.parse_args()
    root = a.root.resolve()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / 'tools'))
    from c643d.cartlaunch import command
    from c643d.cartridge import inspect_easyflash_crt
    index = json.loads((root / 'examples/release-index.json').read_text())
    carts = [r for r in index['files'] if r['path'].endswith('.crt')]
    if a.only:
        carts = [r for r in carts if a.only in r['path']]
    assert carts, 'No matching cartridges'

    def check(row):
        crt = root / row['path']
        original = hashlib.sha256(crt.read_bytes()).hexdigest()
        assert original == row['sha256']
        info = inspect_easyflash_crt(crt, require_metadata=True)
        pictures = []
        for warp in (False, True):
            stem = crt.stem + ('-warp' if warp else '-normal')
            screen = out / (stem + '.png')
            args = ['-console', '-directory', a.vice_data, '+sound',
                    '-warp' if warp else '+warp', '-seed', '1', '-jamaction', '5',
                    '-limitcycles', '2000000', '-exitscreenshot', str(screen)]
            result = subprocess.run(command(a.vice, crt, args, clean_settings=True),
                                    cwd=root, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, timeout=60)
            log = result.stdout
            (out / (stem + '.log')).write_text(log)
            assert result.returncode in (0, 1), log[-1500:]
            assert 'cycle limit reached' in log.lower(), log[-1500:]
            assert 'JAM at' not in log and 'CPU JAM' not in log, log[-1500:]
            assert 'EF: EAPI found' in log and 'as ID 32' in log
            assert hashlib.sha256(crt.read_bytes()).hexdigest() == original
            with Image.open(screen) as im:
                pictures.append((im.size, im.convert('RGB').tobytes()))
        assert pictures[0] == pictures[1], row['path']
        print(crt.name, 'Warp off/on PASS', flush=True)
        return dict(path=row['path'], sha256=original, **info,
                    warp_modes=['off', 'on'], no_jam=True,
                    startup_pixels_match=True, crt_unchanged=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, carts))
    report = dict(passed=True, version=index['version'], vice='Linux VICE 3.10',
                  cycles_per_case=2000000, cartridges=len(results),
                  cold_boot_cases=len(results)*2, results=results)
    (out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Cold-boot verification PASS:', len(results)*2, 'cases')


if __name__ == '__main__':
    main()
