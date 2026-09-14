"""GMod3 read-only image format and allocator; no EasyFlash state or mutations."""
from __future__ import annotations

import hashlib
import struct
import subprocess
from pathlib import Path

BANK_SIZE = 8192
CAPACITIES_MIB = (2, 4, 8, 16)
CRT_TYPE = 62


def bank_count(size_mib):
    if type(size_mib) is not int or size_mib not in CAPACITIES_MIB:
        raise ValueError('GMod3 capacity must be 2, 4, 8 or 16 MiB')
    return size_mib * 128


def bank_select(bank, size_mib=16):
    """Return (write address, value), including the upper three bank bits."""
    if type(bank) is not int or not 0 <= bank < bank_count(size_mib):
        raise ValueError('GMod3 bank is outside the selected capacity')
    return 0xde00 + (bank >> 8), bank & 255


def new_image(size_mib):
    return bytearray(b'\xff') * (bank_count(size_mib) * BANK_SIZE)


def put_bank(image, bank, payload, offset=0):
    size_mib, remainder = divmod(len(image), 1024 * 1024)
    if remainder:
        raise ValueError('GMod3 image must have a supported exact capacity')
    bank_select(bank, size_mib)
    if not 0 <= offset < BANK_SIZE or len(payload) > BANK_SIZE - offset:
        raise ValueError('GMod3 payload crosses its 8 KiB bank')
    start = bank * BANK_SIZE + offset
    image[start:start + len(payload)] = payload


def inspect_crt(path):
    data = Path(path).read_bytes()
    if len(data) < 64 or data[:16] != b'C64 CARTRIDGE   ':
        raise ValueError('Invalid CRT header')
    length, version, hardware = struct.unpack_from('>IHH', data, 16)
    if (length, version, hardware) != (64, 0x100, CRT_TYPE) or data[24:26] != b'\x00\x01':
        raise ValueError('Expected GMod3 type 62, version 1.0, 8K game mapping')
    if any(data[26:32]):
        raise ValueError('GMod3 CRT reserved header bytes must be zero')
    banks = {}
    offset = length
    while offset < len(data):
        if len(data) - offset < 16:
            raise ValueError('Truncated CRT CHIP header')
        magic, packet, chip, bank, address, size = struct.unpack_from('>4sIHHHH', data, offset)
        if magic != b'CHIP' or packet != 16 + BANK_SIZE or size != BANK_SIZE or address != 0x8000 or chip not in (0, 2):
            raise ValueError('Invalid GMod3 CHIP packet')
        if bank in banks or bank >= 2048 or offset + packet > len(data):
            raise ValueError('Duplicate, invalid or truncated GMod3 bank')
        banks[bank] = data[offset + 16:offset + packet]
        offset += packet
    if len(banks) not in [bank_count(n) for n in CAPACITIES_MIB] or set(banks) != set(range(len(banks))):
        raise ValueError('GMod3 CRT must contain a complete contiguous supported capacity')
    boot = banks[0]
    if boot[4:9] != bytes.fromhex('c3 c2 cd 38 30'):
        raise ValueError('GMod3 boot bank lacks CBM80 signature')
    if not all(0x8009 <= int.from_bytes(boot[i:i+2], 'little') < 0xa000 for i in (0, 2)):
        raise ValueError('GMod3 autostart vectors are outside boot ROM')
    return dict(cartridge='GMod3', hardware_type=CRT_TYPE, bank_count=len(banks),
                header_bytes=length, version='1.0', exrom=0, game=1, reserved_bytes_zero=True,
                chip_packet_bytes=16+BANK_SIZE, chip_payload_bytes=BANK_SIZE, load_address='0x8000',
                cold_start=f'0x{int.from_bytes(boot[:2],"little"):04x}',
                warm_start=f'0x{int.from_bytes(boot[2:4],"little"):04x}', cbm80=True,
                capacity_bytes=len(banks)*BANK_SIZE, crt_sha256=hashlib.sha256(data).hexdigest(),
                raw_sha256=hashlib.sha256(b''.join(banks[n] for n in range(len(banks)))).hexdigest())


def convert(*, image, raw, crt, cartconv, name='C643D GMOD3', cwd=None):
    size, remainder = divmod(len(image), 1024*1024)
    if remainder or size not in CAPACITIES_MIB:
        raise ValueError('Invalid GMod3 raw size')
    raw, crt = Path(raw).resolve(), Path(crt).resolve()
    raw.write_bytes(image)
    title = ''.join(c if 32 <= ord(c) <= 126 else '?' for c in name).strip()[:32] or 'C643D GMOD3'
    subprocess.run([str(cartconv), '-t', 'gmod3', '-i', str(raw), '-o', str(crt), '-n', title], cwd=cwd, check=True)
    info = inspect_crt(crt)
    if info['raw_sha256'] != hashlib.sha256(image).hexdigest():
        raise ValueError('GMod3 CRT differs from the complete raw image')
    return info
