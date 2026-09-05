from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .font import FONT as HUD_FONT

EASYFLASH_BANKS = 64
EASYFLASH_CHIP_SIZE = 0x2000
EASYFLASH_BANK_SIZE = EASYFLASH_CHIP_SIZE * 2
EASYFLASH_RAW_SIZE = EASYFLASH_BANKS * EASYFLASH_BANK_SIZE


def easyflash_offset(bank: int, chip: str, offset: int = 0) -> int:
    """Return the raw-image offset for one EasyFlash bank/chip location.

    cartconv's EasyFlash binary input is bank-major/interleaved:
    bank 0 ROML, bank 0 ROMH, bank 1 ROML, bank 1 ROMH, ...
    """
    if not 0 <= bank < EASYFLASH_BANKS:
        raise ValueError(f'EasyFlash bank must be 0..{EASYFLASH_BANKS - 1}')
    if chip not in ('roml', 'romh'):
        raise ValueError("EasyFlash chip must be 'roml' or 'romh'")
    if not 0 <= offset < EASYFLASH_CHIP_SIZE:
        raise ValueError('EasyFlash chip offset must be 0..0x1fff')
    return bank * EASYFLASH_BANK_SIZE + (EASYFLASH_CHIP_SIZE if chip == 'romh' else 0) + offset


def put_easyflash_chip(image: bytearray, bank: int, chip: str, payload: bytes) -> None:
    if len(image) != EASYFLASH_RAW_SIZE:
        raise ValueError(f'EasyFlash raw image must be exactly {EASYFLASH_RAW_SIZE} bytes')
    if len(payload) > EASYFLASH_CHIP_SIZE:
        raise ValueError(f'EasyFlash {chip} payload is {len(payload)} bytes; maximum is {EASYFLASH_CHIP_SIZE}')
    start = easyflash_offset(bank, chip)
    image[start:start + len(payload)] = payload


def new_easyflash_image() -> bytearray:
    return bytearray([0xFF]) * EASYFLASH_RAW_SIZE


def build_smoke_raw(romh0: bytes) -> tuple[bytes, dict]:
    if len(romh0) != EASYFLASH_CHIP_SIZE:
        raise ValueError(f'smoke bootstrap must be exactly 8192 bytes, got {len(romh0)}')
    image = new_easyflash_image()
    put_easyflash_chip(image, 0, 'romh', romh0)
    markers = {
        1: b'C643D EASYFLASH BANK 1 OK\x00',
        2: b'C643D EASYFLASH BANK 2 OK\x00',
        3: b'C643D EASYFLASH BANK 3 OK\x00',
    }
    for bank, marker in markers.items():
        put_easyflash_chip(image, bank, 'roml', marker)
        # One byte outside the visible marker gives the C64 smoke routine a
        # deterministic bank-identity check before it prints the string.
        image[easyflash_offset(bank, 'roml', 0x0100)] = bank
    manifest = {
        'format': 'c64-3d-toolkit-easyflash-smoke-v1',
        'cartridge': 'EasyFlash',
        'raw_size': EASYFLASH_RAW_SIZE,
        'bank_count': EASYFLASH_BANKS,
        'chip_size': EASYFLASH_CHIP_SIZE,
        'raw_layout': 'bank-major: ROML 8KiB then ROMH 8KiB for each bank',
        'entries': [
            {'bank': 0, 'chip': 'romh', 'cpu_window_at_reset': '$e000-$ffff', 'purpose': 'bootstrap/reset vectors'},
            *[
                {'bank': bank, 'chip': 'roml', 'cpu_window': '$8000-$9fff', 'sentinel': f'$8100 = ${bank:02x}', 'purpose': marker[:-1].decode('ascii')}
                for bank, marker in markers.items()
            ],
        ],
    }
    return bytes(image), manifest


def write_smoke_map(path: Path, manifest: dict) -> None:
    lines = [
        'c64-3d-toolkit EasyFlash smoke-test map',
        '=======================================',
        '',
        'Raw layout: 64 banks x (8 KiB ROML + 8 KiB ROMH) = 1 MiB',
        'Unused flash bytes are $FF; cartconv may omit empty CHIP packets in the CRT.',
        '',
        'bank 00 ROMH  reset/boot code; native EasyFlash starts in Ultimax ($E000-$FFFF)',
        'bank 01 ROML  "C643D EASYFLASH BANK 1 OK" at $8000; sentinel $01 at $8100',
        'bank 02 ROML  "C643D EASYFLASH BANK 2 OK" at $8000; sentinel $02 at $8100',
        'bank 03 ROML  "C643D EASYFLASH BANK 3 OK" at $8000; sentinel $03 at $8100',
        '',
        'Expected visible result:',
        '  C643D EASYFLASH BANK 1 OK',
        '  C643D EASYFLASH BANK 2 OK',
        '  C643D EASYFLASH BANK 3 OK',
        '',
    ]
    path.write_text('\n'.join(lines), encoding='utf-8')


def assemble_smoke_bootstrap(*, tass: str, tass_args: Sequence[str], source: Path,
                             output: Path, labels: Path, listing: Path, cwd: Path,
                             vice_debugcart: bool = False) -> None:
    command = [
        tass, *list(tass_args), '-D', f'VICE_DEBUGCART={1 if vice_debugcart else 0}',
        '-b', '--vice-labels', '-l', str(labels), '-L', str(listing),
        '-o', str(output), str(source),
    ]
    print('+', ' '.join(command))
    subprocess.run(command, cwd=cwd, check=True)
    size = output.stat().st_size
    if size != EASYFLASH_CHIP_SIZE:
        raise RuntimeError(f'EasyFlash bootstrap assembled to {size} bytes; expected exactly 8192')


def convert_easyflash(*, cartconv: str, raw: Path, crt: Path, name: str, cwd: Path) -> None:
    command = [cartconv, '-t', 'easy', '-i', str(raw), '-o', str(crt), '-n', name]
    print('+', ' '.join(command))
    subprocess.run(command, cwd=cwd, check=True)


def validate_easyflash_info(info: str) -> None:
    """Reject a structurally valid CRT if it is not the EasyFlash image we asked for."""
    required = (
        'Hardware ID: 32 (EasyFlash)',
        'Mode: exrom: 1 game: 0 (ultimax)',
    )
    missing = [item for item in required if item not in info]
    if missing:
        raise RuntimeError('cartconv info did not describe a native EasyFlash CRT: ' + ', '.join(missing))


def check_easyflash_crt(*, cartconv: str, crt: Path, cwd: Path) -> str:
    completed = subprocess.run(
        [cartconv, '-c', str(crt)], cwd=cwd, capture_output=True, text=True, check=False,
    )
    check_output = (completed.stdout + completed.stderr).strip()
    if completed.returncode != 0:
        raise RuntimeError(f'cartconv rejected generated CRT: {check_output or "unknown error"}')

    info_run = subprocess.run(
        [cartconv, '-f', str(crt)], cwd=cwd, capture_output=True, text=True, check=False,
    )
    info = (info_run.stdout + info_run.stderr).strip()
    if info_run.returncode != 0:
        raise RuntimeError(f'cartconv could not inspect generated CRT: {info or "unknown error"}')
    validate_easyflash_info(info)
    return info


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')


DEMO_RUNTIME_LOAD = 0xC800
DEMO_RUNTIME_SIZE = 0x0800
DEMO_CONTROL_LOAD = 0x0200
DEMO_CONTROL_SIZE = 0x0100
DEMO_CONTROL_ROM_OFFSET = DEMO_RUNTIME_SIZE
DEMO_MENU_FONT_ROM_OFFSET = 0x1000
DEMO_MENU_FONT_SIZE = 0x0800
MENU_STYLES = {'default': 0, 'decorative': 1, 'demoscene': 2}
DEMO_MENU_STYLE_ORDER = tuple(MENU_STYLES)
DEMO_MENU_STYLE_BANK = 1
DEMO_MENU_STYLE_BUNDLE_SIZE = DEMO_RUNTIME_SIZE * len(DEMO_MENU_STYLE_ORDER)
DEMO_FIRST_DATA_BANK = 1
DEMO_ENTRY_POINT = 0x080D


# Menu-only 5x7 lowercase extension.  Uppercase/digits reuse the compact HUD
# font from tools/c643d/font.py; this keeps the decorative cartridge menu
# visually related to the in-animation overlay without changing that overlay's
# historical uppercase-only behaviour.
_MENU_LOWER = {
    'a':["00000","01110","00001","01111","10001","10011","01101"],
    'b':["10000","10000","10110","11001","10001","10001","11110"],
    'c':["00000","01110","10001","10000","10000","10001","01110"],
    'd':["00001","00001","01101","10011","10001","10001","01111"],
    'e':["00000","01110","10001","11111","10000","10001","01110"],
    'f':["00110","01001","01000","11100","01000","01000","01000"],
    'g':["00000","01111","10001","10001","01111","00001","01110"],
    'h':["10000","10000","10110","11001","10001","10001","10001"],
    'i':["00100","00000","01100","00100","00100","00100","01110"],
    'j':["00010","00000","00110","00010","00010","10010","01100"],
    'k':["10000","10000","10010","10100","11000","10100","10010"],
    'l':["01100","00100","00100","00100","00100","00100","01110"],
    'm':["00000","11010","10101","10101","10101","10101","10101"],
    'n':["00000","10110","11001","10001","10001","10001","10001"],
    'o':["00000","01110","10001","10001","10001","10001","01110"],
    'p':["00000","11110","10001","10001","11110","10000","10000"],
    'q':["00000","01111","10001","10001","01111","00001","00001"],
    'r':["00000","10110","11001","10000","10000","10000","10000"],
    's':["00000","01111","10000","01110","00001","00001","11110"],
    't':["01000","01000","11100","01000","01000","01001","00110"],
    'u':["00000","10001","10001","10001","10001","10011","01101"],
    'v':["00000","10001","10001","10001","10001","01010","00100"],
    'w':["00000","10001","10001","10101","10101","10101","01010"],
    'x':["00000","10001","01010","00100","01010","10001","10001"],
    'y':["00000","10001","10001","10001","01111","00001","01110"],
    'z':["00000","11111","00010","00100","01000","10000","11111"],
}

_MENU_PUNCT = {
    ',':["00000","00000","00000","00000","00100","00100","01000"],
    '.':["00000","00000","00000","00000","00000","00100","00100"],
    '+':["00000","00100","00100","11111","00100","00100","00000"],
    '=':["00000","00000","11111","00000","11111","00000","00000"],
    '|':["00100","00100","00100","00100","00100","00100","00100"],
    '>':["10000","01000","00100","00010","00100","01000","10000"],
}

def _menu_glyph(rows: Sequence[str]) -> bytes:
    return bytes([int(row, 2) << 2 for row in rows] + [0])

def build_menu_charset() -> bytes:
    """Build the cartridge-menu-only 2 KiB 5x7 character set.

    Screen-code layout is intentionally simple for the menu runtime:
    codes 1..26 are uppercase A..Z and $41..$5a are lowercase a..z.
    Digits/punctuation keep their normal screen-code values.
    """
    charset=bytearray(DEMO_MENU_FONT_SIZE)
    for i,ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ',1):
        charset[i*8:(i+1)*8]=_menu_glyph(HUD_FONT[ch])
    for i,ch in enumerate('abcdefghijklmnopqrstuvwxyz',0x41):
        charset[i*8:(i+1)*8]=_menu_glyph(_MENU_LOWER[ch])
    for ch in '0123456789':
        code=ord(ch)
        charset[code*8:(code+1)*8]=_menu_glyph(HUD_FONT[ch])
    punct={k:v for k,v in HUD_FONT.items() if k in ' :-_/'}
    punct.update(_MENU_PUNCT)
    for ch,rows in punct.items():
        code=ord(ch)
        if code < 256:
            charset[code*8:(code+1)*8]=_menu_glyph(rows)
    return bytes(charset)

def menu_style_id(name: str) -> int:
    try:
        return MENU_STYLES[name]
    except KeyError as exc:
        raise ValueError(f'unknown cartridge menu style: {name!r}') from exc


@dataclass(frozen=True)
class DemoEntryPlan:
    name: str
    path: Path
    bank: int
    banks: int
    load_address: int
    entry_address: int
    length: int
    checksum16: int
    irq_address: int


def _petscii_safe_name(name: str) -> str:
    clean=''.join(ch if 32 <= ord(ch) < 127 else '?' for ch in name.upper())
    return clean[:30]



def _patch_demo_irq(payload: bytes, *, target: int = DEMO_CONTROL_LOAD) -> tuple[bytes, int]:
    """Redirect a generated yunroll PRG's raster IRQ to the cart control shim.

    The shipped demo PRGs all install their hardware IRQ vector with the same
    short instruction sequence.  We patch only the cartridge copy, retaining
    the original handler address so the shim can tail-jump to it on every frame.
    """
    data=bytearray(payload)
    matches=[]
    for i in range(max(0,len(data)-9)):
        if (data[i]==0xA9 and data[i+2:i+5]==bytes((0x8D,0xFE,0xFF))
                and data[i+5]==0xA9 and data[i+7:i+10]==bytes((0x8D,0xFF,0xFF))):
            matches.append(i)
    if len(matches)!=1:
        raise ValueError(
            f'demo PRG needs exactly one generated raster-IRQ install sequence; found {len(matches)}'
        )
    i=matches[0]
    original=data[i+1] | (data[i+6]<<8)
    data[i+1]=target & 0xff
    data[i+6]=(target>>8) & 0xff
    return bytes(data),original

def pack_demo_prgs(entries: Sequence[tuple[str, Path]], *, source_root: Path | None = None) -> tuple[bytearray, list[DemoEntryPlan], dict]:
    """Pack existing toolkit PRGs into bank-aligned EasyFlash ROML banks.

    This is an intentionally simple bridge for the 0.6.3 cartridge demo.  Each
    PRG starts on a fresh ROML bank so the C64-side loader only needs a bank
    number and byte length.  The real yunroll-cart streamer will use a denser
    logical stream format later.
    """
    image=new_easyflash_image()
    current_bank=DEMO_FIRST_DATA_BANK
    plans=[]
    manifest_entries=[]
    for name,path in entries:
        path=Path(path)
        data=path.read_bytes()
        if len(data)<3:
            raise ValueError(f'demo PRG is too short: {path}')
        load=data[0] | (data[1]<<8)
        payload,irq_address=_patch_demo_irq(data[2:])
        end=load+len(payload)
        if load < 0x0800:
            raise ValueError(f'demo PRG {path} loads at ${load:04x}; loader runtime occupies low RAM')
        if end > DEMO_RUNTIME_LOAD:
            raise ValueError(f'demo PRG {path} ends at ${end:04x}; stage-2 demo loader runtime starts at ${DEMO_RUNTIME_LOAD:04x}')
        banks=max(1,math.ceil(len(payload)/EASYFLASH_CHIP_SIZE))
        if current_bank+banks > EASYFLASH_BANKS:
            raise ValueError(
                f'demo set needs {current_bank+banks} EasyFlash banks including bootstrap; maximum is {EASYFLASH_BANKS}'
            )
        for i in range(banks):
            chunk=payload[i*EASYFLASH_CHIP_SIZE:(i+1)*EASYFLASH_CHIP_SIZE]
            put_easyflash_chip(image,current_bank+i,'roml',chunk)
        checksum=sum(payload)&0xffff
        plan=DemoEntryPlan(
            name=_petscii_safe_name(name),path=path,bank=current_bank,banks=banks,
            load_address=load,entry_address=DEMO_ENTRY_POINT,length=len(payload),checksum16=checksum,
            irq_address=irq_address,
        )
        plans.append(plan)
        try:
            source_display=path.relative_to(source_root).as_posix() if source_root is not None else str(path)
        except ValueError:
            source_display=str(path)
        manifest_entries.append({
            'name':plan.name,
            'source':source_display,
            'bank':plan.bank,
            'banks':plan.banks,
            'chip':'roml',
            'cpu_window':'$8000-$9fff',
            'load_address':f'${plan.load_address:04x}',
            'entry_address':f'${plan.entry_address:04x}',
            'payload_bytes':plan.length,
            'checksum16':f'${plan.checksum16:04x}',
            'original_irq':f'${plan.irq_address:04x}',
            'cart_irq':f'${DEMO_CONTROL_LOAD:04x}',
        })
        current_bank+=banks
    manifest={
        'format':'c64-3d-toolkit-easyflash-demo-v1',
        'cartridge':'EasyFlash',
        'raw_size':EASYFLASH_RAW_SIZE,
        'bank_count':EASYFLASH_BANKS,
        'chip_size':EASYFLASH_CHIP_SIZE,
        'runtime_load':f'${DEMO_RUNTIME_LOAD:04x}',
        'runtime_size':DEMO_RUNTIME_SIZE,
        'data_banks_used':current_bank-DEMO_FIRST_DATA_BANK,
        'highest_bank_used':current_bank-1,
        'entries':manifest_entries,
        'note':'Demo launcher packs existing PRGs and patches only the cartridge copies through a low-RAM control IRQ shim; it is not yet the yunroll-cart frame/table streamer.',
    }
    return image,plans,manifest


def write_demo_include(path: Path, plans: Sequence[DemoEntryPlan]) -> None:
    if not plans:
        raise ValueError('EasyFlash demo needs at least one entry')
    def bytes_line(label,values):
        return f'{label}:\n    .byte ' + ', '.join(f'${v & 0xff:02x}' for v in values) + '\n'
    lines=[
        '; generated by c64-3d-toolkit; do not edit',
        f'DEMO_ENTRY_COUNT = {len(plans)}',
        '',
    ]
    lines.append(bytes_line('demo_bank',[p.bank for p in plans]))
    lines.append(bytes_line('demo_len_lo',[p.length for p in plans]))
    lines.append(bytes_line('demo_len_hi',[p.length>>8 for p in plans]))
    lines.append(bytes_line('demo_load_lo',[p.load_address for p in plans]))
    lines.append(bytes_line('demo_load_hi',[p.load_address>>8 for p in plans]))
    lines.append(bytes_line('demo_entry_lo',[p.entry_address for p in plans]))
    lines.append(bytes_line('demo_entry_hi',[p.entry_address>>8 for p in plans]))
    lines.append(bytes_line('demo_sum_lo',[p.checksum16 for p in plans]))
    lines.append(bytes_line('demo_sum_hi',[p.checksum16>>8 for p in plans]))
    lines.append(bytes_line('demo_irq_lo',[p.irq_address for p in plans]))
    lines.append(bytes_line('demo_irq_hi',[p.irq_address>>8 for p in plans]))
    lines.append('demo_name_lo:\n    .byte ' + ', '.join(f'<demo_name_{i}' for i in range(len(plans))) + '\n')
    lines.append('demo_name_hi:\n    .byte ' + ', '.join(f'>demo_name_{i}' for i in range(len(plans))) + '\n\n')
    for i,p in enumerate(plans):
        escaped=p.name.replace('"','\'')
        lines.append(f'demo_name_{i}:\n    .text "{escaped}"\n    .byte 0\n')
    path.write_text('\n'.join(lines),encoding='utf-8')


def assemble_demo_runtime(*, tass: str, tass_args: Sequence[str], source: Path,
                          include_dir: Path, output: Path, labels: Path, listing: Path,
                          cwd: Path, vice_debugcart: bool=False, auto_launch: int=255, menu_style: str='default') -> None:
    command=[
        tass,*list(tass_args),'-I',str(include_dir),
        '-D',f'VICE_DEBUGCART={1 if vice_debugcart else 0}',
        '-D',f'AUTO_LAUNCH={int(auto_launch)}',
        '-D',f'MENU_STYLE={menu_style_id(menu_style)}',
        '-b','--vice-labels','-l',str(labels),'-L',str(listing),'-o',str(output),str(source),
    ]
    print('+',' '.join(command))
    subprocess.run(command,cwd=cwd,check=True)
    size=output.stat().st_size
    if size!=DEMO_RUNTIME_SIZE:
        raise RuntimeError(f'EasyFlash demo runtime assembled to {size} bytes; expected {DEMO_RUNTIME_SIZE}')



def assemble_demo_control(*, tass: str, tass_args: Sequence[str], source: Path,
                          output: Path, labels: Path, listing: Path, cwd: Path) -> None:
    command=[
        tass,*list(tass_args),'-b','--vice-labels','-l',str(labels),'-L',str(listing),
        '-o',str(output),str(source),
    ]
    print('+',' '.join(command))
    subprocess.run(command,cwd=cwd,check=True)
    size=output.stat().st_size
    if size!=DEMO_CONTROL_SIZE:
        raise RuntimeError(f'EasyFlash demo control shim assembled to {size} bytes; expected {DEMO_CONTROL_SIZE}')

def assemble_demo_boot(*, tass: str, tass_args: Sequence[str], source: Path,
                       output: Path, labels: Path, listing: Path, cwd: Path) -> None:
    command=[
        tass,*list(tass_args),'-b','--vice-labels','-l',str(labels),'-L',str(listing),
        '-o',str(output),str(source),
    ]
    print('+',' '.join(command))
    subprocess.run(command,cwd=cwd,check=True)
    size=output.stat().st_size
    if size!=EASYFLASH_CHIP_SIZE:
        raise RuntimeError(f'EasyFlash demo bootstrap assembled to {size} bytes; expected 8192')


def install_demo_boot(image: bytearray, boot_romh0: bytes, runtime: bytes, control: bytes,
                      menu_font: bytes | None=None, style_runtimes: Sequence[bytes] | None=None) -> None:
    if len(boot_romh0)!=EASYFLASH_CHIP_SIZE:
        raise ValueError('demo boot ROMH must be exactly 8192 bytes')
    if len(runtime)!=DEMO_RUNTIME_SIZE:
        raise ValueError(f'demo runtime must be exactly {DEMO_RUNTIME_SIZE} bytes')
    if len(control)!=DEMO_CONTROL_SIZE:
        raise ValueError(f'demo control shim must be exactly {DEMO_CONTROL_SIZE} bytes')
    if menu_font is not None and len(menu_font)!=DEMO_MENU_FONT_SIZE:
        raise ValueError(f'demo menu font must be exactly {DEMO_MENU_FONT_SIZE} bytes')
    put_easyflash_chip(image,0,'romh',boot_romh0)
    put_easyflash_chip(image,0,'roml',runtime)
    start=easyflash_offset(0,'roml',DEMO_CONTROL_ROM_OFFSET)
    image[start:start+len(control)]=control
    if menu_font is not None:
        start=easyflash_offset(0,'roml',DEMO_MENU_FONT_ROM_OFFSET)
        image[start:start+len(menu_font)]=menu_font
    if style_runtimes is not None:
        if len(style_runtimes)!=len(DEMO_MENU_STYLE_ORDER):
            raise ValueError(f'demo menu style bundle needs {len(DEMO_MENU_STYLE_ORDER)} runtimes')
        for style,payload in zip(DEMO_MENU_STYLE_ORDER,style_runtimes):
            if len(payload)!=DEMO_RUNTIME_SIZE:
                raise ValueError(f'demo {style} runtime must be exactly {DEMO_RUNTIME_SIZE} bytes')
        bundle=b''.join(style_runtimes)
        if len(bundle)!=DEMO_MENU_STYLE_BUNDLE_SIZE:
            raise ValueError('demo menu style bundle has unexpected size')
        put_easyflash_chip(image,DEMO_MENU_STYLE_BANK,'romh',bundle)


def write_demo_map(path: Path, manifest: dict) -> None:
    lines=[
        'c64-3d-toolkit EasyFlash demo cartridge map',
        '============================================',
        '',
        'bank 00 ROMH  native EasyFlash Ultimax bootstrap + reset vectors',
        'bank 00 ROML  startup $C800-$CFFF menu/loader + $0200 cart-control IRQ shim',
        '                + menu-only compact 5x7 charset at ROML $9000-$97FF',
        'bank 01 ROMH  switchable default/decorative/demoscene menu runtimes (3 x 2 KiB)',
        '',
    ]
    for entry in manifest['entries']:
        start=entry['bank']; end=start+entry['banks']-1
        banks=f'{start:02d}' if start==end else f'{start:02d}-{end:02d}'
        lines.append(
            f"banks {banks:>5} ROML  {entry['name']:<24} {entry['payload_bytes']:>6} bytes "
            f"load {entry['load_address']} entry {entry['entry_address']}"
        )
    lines.extend([
        '',
        f"data banks used: {manifest['data_banks_used']} / 63",
        f"startup style:   {manifest.get('menu_style','default')}",
        'live menu styles: default -> decorative -> demoscene -> default (F1)',
        f"highest bank:    {manifest['highest_bank_used']} / 63",
        '',
        'Bridge note: these are existing PRG payloads launched from cartridge.',
        'Menu F1 cycles styles; cartridge copies use F1/RUN-STOP menu + SPACE next-demo controls.',
        'True yunroll-cart frame/table streaming is the next backend milestone.',
        '',
    ])
    path.write_text('\n'.join(lines),encoding='utf-8')
