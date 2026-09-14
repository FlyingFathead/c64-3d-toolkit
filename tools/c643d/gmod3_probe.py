"""Build and measure independent GMod3/EasyFlash read-only diagnostic carts."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from . import gmod3_image as cart
from .gmod3_stream import install_runtime
from .monitor_logs import vice_monitor_args

BENCHES = ('empty', 'fixed', 'indexed', 'read', 'ram_read', 'copy', 'ram_copy', 'mapping')


def build(root, out, *, tass, cartconv, size_mib=16, cart_type='gmod3'):
    root, out = Path(root).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stem = f'gmod3-probe-{size_mib}m' if cart_type == 'gmod3' else 'easyflash-probe'
    work = root/'build'/stem
    work.mkdir(parents=True, exist_ok=True)
    runtime, labels = work/'runtime.prg', out/f'{stem}.lbl'
    is_gmod = cart_type == 'gmod3'
    if cart_type not in ('gmod3', 'easyflash'):
        raise ValueError('Unknown diagnostic cartridge type')
    groups = cart.bank_count(size_mib)//256 if is_gmod else 1
    subprocess.run([str(tass), '--cbm-prg', '-D', f'GMOD3={int(is_gmod)}', '-D', f'BANK_GROUPS={groups}',
        '--vice-labels', '-l', str(labels), '-o', str(runtime), str(root/'c64/gmod3/diagnostic.asm')], check=True)
    if is_gmod:
        image = cart.new_image(size_mib)
        install_runtime(root, image, runtime, work, tass)
        count = cart.bank_count(size_mib)
    else:
        from .cartridge import new_easyflash_image, put_easyflash_chip
        image = new_easyflash_image()
        blob = runtime.read_bytes()
        ram = bytearray(0x5800)
        ram[1:len(blob)-1] = blob[2:]
        for bank in range(3):
            put_easyflash_chip(image, bank, 'roml', ram[bank*8192:(bank+1)*8192])
        boot = work/'boot.bin'
        subprocess.run([str(tass), '--nostart', '-o', str(boot), str(root/'c64/cart/easyflash-object-boot.asm')], check=True)
        put_easyflash_chip(image, 0, 'romh', boot.read_bytes())
        count = 64
    for bank in range(count):
        base = bank*(8192 if is_gmod else 16384)
        sig = bytes([bank & 255, bank >> 8, (bank & 255)^255, (bank >> 8)^255])
        image[base+0x1fe0:base+0x1fe4] = sig
        image[base+0x1ffc:base+0x2000] = sig
        image[base+0x1e00:base+0x1f00] = bytes(range(256))
    crt, raw = out/f'{stem}.crt', work/f'{stem}.bin'
    if is_gmod:
        info = cart.convert(image=image, raw=raw, crt=crt, cartconv=cartconv, name='C643D GMOD3 BANK PROBE')
    else:
        from .cartridge import convert_easyflash, inspect_easyflash_crt
        raw.write_bytes(image)
        convert_easyflash(cartconv=str(cartconv), raw=raw, crt=crt, name='C643D EF BANK PROBE', cwd=root)
        info = inspect_easyflash_crt(crt)
    manifest = dict(format='c643d-cartridge-bank-probe-v1', cart_type=cart_type, banks=count,
        capacity_bytes=len(image), crt_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256((root/'c64/gmod3/diagnostic.asm').read_bytes()).hexdigest(),
        container=info, tests=['bank signatures', 'bank boundaries', 'mapping', 'IRQ/NMI vector override', 'read/copy cycles'])
    (out/f'{stem}-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return crt


def labels(path):
    return {p[2].lstrip('.'): int(p[1], 16) for line in Path(path).read_text().splitlines()
            if len(p := line.split()) == 3 and p[0] == 'al'}


def vice_command(vice, crt, vice_data=None):
    command = [str(vice), '-console', '-default', '-pal', '+sound', '-warp', '-seed', '1',
        '+saveres', '+easyflashcrtwrite', '+gmod3flashwrite', '-jamaction', '5',
        '-cartcrt', str(Path(crt).resolve()), *vice_monitor_args()]
    if vice_data:
        command += ['-directory', str(vice_data)]
    return command


def measure(crt, *, vice, vice_data=None):
    crt = Path(crt).resolve()
    sym = labels(crt.with_suffix('.lbl'))
    manifest = json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    work = crt.parent/(crt.stem+'-measurement')
    work.mkdir(parents=True, exist_ok=True)
    for filename in ('results.bin', 'copy.bin'):
        (work/filename).unlink(missing_ok=True)
    mon = ['delete']
    for display in ('off', 'on', 'eight_sprites'):
        for name in BENCHES:
            mon += [f'break ${sym[f"bench_{name}_start"]:04x}', 'g', 'delete', 'stopwatch reset',
                    f'break ${sym[f"bench_{name}_end"]:04x}', 'g', 'stopwatch', 'delete']
    mon += [f'break ${sym["diagnostic_done"]:04x}', 'g', 'delete', 'bank ram',
        f'bsave "{work / "results.bin"}" 0 $3000 $30ff',
        f'bsave "{work / "copy.bin"}" 0 $6000 $60ff', 'quit']
    script, log = work/'run.mon', work/'monitor.log'
    script.write_text('\n'.join(mon)+'\n')
    # A unique log per run prevents the stale-monitor-log failure seen earlier.
    log.unlink(missing_ok=True)
    command = vice_command(vice, crt, vice_data) + ['-initbreak', 'reset', '-moncommands', str(script),
        '-monlogname', str(log), '-monlog', '-limitcycles', '10000000']
    with (work/'vice.log').open('w') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=60)
    trace = log.read_text() if log.exists() else ''
    values = [int(n) for n in re.findall(r'Stopwatch:\s*(\d+)', trace)]
    if result.returncode or len(values) != len(BENCHES)*3 or not (work/'results.bin').exists():
        raise RuntimeError('Diagnostic did not finish: '+(work/'vice.log').read_text()[-1500:]+'\n'+trace[-1800:])
    ram = (work/'results.bin').read_bytes()
    if ram[0] != 1 or ram[1] != 1 or int.from_bytes(ram[2:4], 'little') != manifest['banks']:
        raise AssertionError(f'Bank probe failed: {ram[:8].hex()}')
    if (work/'copy.bin').read_bytes() != bytes(range(256)):
        raise AssertionError('ROM/RAM copy payload differs')
    mapping = None
    if manifest['cart_type'] == 'gmod3':
        # $35 exposes RAM; $36 hides ROML as LORAM=0; $37 exposes cartridge.
        if ram[0x10] != 0xa5 or ram[0x13] != 0xa5 or ram[0x14] != 0x5a:
            raise AssertionError('GMod3 RAM visibility probe failed')
        if list(ram[0x18:0x1c]) != [8, 12, 8, 12] or not ram[0x20] or ram[0x22] < 32 or ram[0x24]:
            raise AssertionError('GMod3 vector/interrupt bank-integrity probe failed: '+ram[0x18:0x25].hex())
        mapping = dict(ports=['$35', '$36', '$37'], at_8000=list(ram[0x10:0x13]),
            at_e000=list(ram[0x14:0x17]), disabled_rom_at_8000=ram[0x13],
            irq_events=ram[0x20], nmi_events=ram[0x22], interrupt_bank_mismatches=ram[0x24],
            override_vectors=list(ram[0x18:0x1c]))
    timing = {display: dict(zip(BENCHES, values[i*len(BENCHES):(i+1)*len(BENCHES)]))
              for i, display in enumerate(('off', 'on', 'eight_sprites'))}
    off = timing['off']
    if off['fixed']-off['empty'] != 1024 or off['indexed']-off['empty'] != 1280:
        raise AssertionError('Bank-store base cycle count differs from 6502 timing')
    if off['read'] != off['ram_read'] or off['copy'] != off['ram_copy'] or off['copy'] != 2623:
        raise AssertionError('Unexpected display-off ROM/RAM transfer timings')
    if (off['mapping']-off['empty'])/256 != (40 if manifest['cart_type']=='gmod3' else 60):
        raise AssertionError('Production mapper pair cycle count differs from expected')
    report = dict(passed=True, cartridge=crt.name, cart_type=manifest['cart_type'],
        banks_verified=manifest['banks'], mapping=mapping, cycles=timing,
        fixed_store_cycles=(off['fixed']-off['empty'])/256,
        indexed_store_cycles=(off['indexed']-off['empty'])/256,
        mapping_pair_cycles=(off['mapping']-off['empty'])/256,
        copy_bytes=256, copy_verified=True, cpu='PAL MOS6510', emulator='VICE x64sc',
        scope='Emulated C64 clocks, including VIC stalls with display on. No physical hardware measurement.',
        crt_sha256=manifest['crt_sha256'], source_sha256=manifest['source_sha256'])
    (crt.parent/f'{crt.stem}-results.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def verify_reset(crt, *, vice, vice_data=None):
    """Dirty bank/control state, then exercise both VICE monitor reset modes."""
    crt = Path(crt).resolve()
    cart.inspect_crt(crt)
    sym = labels(crt.with_suffix('.lbl'))
    work = crt.parent/(crt.stem+'-reset')
    work.mkdir(parents=True, exist_ok=True)
    commands = ['delete', f'break ${sym["diagnostic_done"]:04x}', 'g', 'delete']
    for mode in (0, 1):
        commands += ['bank cpu', '> $de07 $ff', '> $de08 $60',
            f'break $800c', f'reset {mode}', 'delete',
            f'bsave "{work/f"bank-{mode}.bin"}" 0 $de00 $de08',
            f'bsave "{work/f"boot-{mode}.bin"}" 0 $8000 $8008',
            f'break ${sym["diagnostic_done"]:04x}', 'g', 'delete']
    commands += ['quit']
    script = work/'run.mon'
    script.write_text('\n'.join(commands)+'\n')
    with (work/'vice.log').open('w') as output:
        proc = subprocess.run(vice_command(vice, crt, vice_data)+[
            '-initbreak', 'reset', '-moncommands', str(script), '-limitcycles', '15000000'],
            stdout=output, stderr=subprocess.STDOUT, timeout=60)
    if proc.returncode:
        raise RuntimeError('Reset probe failed: '+(work/'vice.log').read_text()[-2000:])
    for mode in (0, 1):
        bank = (work/f'bank-{mode}.bin').read_bytes()
        boot = (work/f'boot-{mode}.bin').read_bytes()
        if bank[0] != 0 or bank[8] != 0 or boot[4:9] != bytes.fromhex('c3 c2 cd 38 30'):
            raise AssertionError(f'GMod3 reset mode {mode} did not restore bank 0 normal ROM')
    return dict(passed=True, monitor_reset_modes=[0,1], dirty_bank=2047,
                dirty_control=0x60, rebooted_probe=True, reset_bank=0, cbm80_visible=True)
