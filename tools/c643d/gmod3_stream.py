"""Independent experimental GMod3 HORS-V2 object-stream build path.

Shares pure geometry/picture encoders; never patches EasyFlash modules or files.
Each picture fits one bank. Bank high bytes stage at $2300 and live in
RAM $a000; seven low directory arrays leave $4f00 for literal spans.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from . import gmod3_image as cart
from .emit import bytes_lines, emit_hud
from .colors import configure_asm_colors, hires_screen_byte
from .hors_v2_stable import encoder
from .pipeline import build_xchunk_tables

MAX_FRAMES = 255


def pack_frames(frames, *, size_mib=2, first_bank=4, colors=True, gap=6, batch_budget=2048, encode=None, page_frames=0):
    if not 1 <= len(frames) <= (1024 if page_frames else MAX_FRAMES):
        raise ValueError('GMod3 spinner requires 1..255 pictures (wide RAM directory)')
    if first_bank < 4:
        raise ValueError('GMod3 banks 0..3 are reserved for boot/runtime')
    cart.bank_select(first_bank, size_mib)
    image = cart.new_image(size_mib)
    encode = encode or encoder(gap, batch_budget)
    bank, offset, directory = first_bank, 0, []
    for i, frame in enumerate(frames):
        try:
            block, meta = encode(frame, colors)
        except ValueError as exc:
            raise ValueError(f'GMod3 picture {i}: {exc}') from exc
        if offset + len(block) > cart.BANK_SIZE:
            bank, offset = bank + 1, 0
        cart.put_bank(image, bank, block, offset)
        directory.append(dict(frame=i, bank=bank, address=0x8000+offset, bytes=len(block),
            metadata_bytes=meta, runs=len(frame.records), encoding='byte-spans',
            sha256=hashlib.sha256(block).hexdigest()))
        offset += len(block)
    return image, directory


def emit_directory(path, directory):
    levels, masks = build_xchunk_tables()
    lines = ['; GMod3 directory: full 11-bit bank identities.', '* = $1700', 'xchunk_levels:'] + bytes_lines(levels)
    for i, table in enumerate(masks):
        lines += [f'* = ${0x1800+i*256:04x}', f'xchunk_mask{i}:'] + bytes_lines(table)
    lines += ['* = $4800']
    arrays = {
        'cart_bank': [d['bank'] & 255 for d in directory],
        'cart_source_lo': [d['address'] & 255 for d in directory],
        'cart_source_hi': [d['address'] >> 8 for d in directory],
        'cart_length_lo': [d['bytes'] & 255 for d in directory],
        'cart_length_hi': [(d['bytes'] >> 8) | 128 for d in directory],
        'cart_meta_lo': [d['metadata_bytes'] & 255 for d in directory],
        'cart_meta_hi': [d['metadata_bytes'] >> 8 for d in directory],
    }
    for name, values in arrays.items():
        lines += [name+':'] + bytes_lines(values)
    lines += ['.if * > $4f00', '.error "GMod3 directory overlaps span extension"', '.endif']
    lines += ['* = $2300', 'gmod3_bank_hi_staging:'] + bytes_lines([d['bank'] >> 8 for d in directory])
    lines += ['cart_bank_hi = $a000']
    Path(path).write_text('\n'.join(lines)+'\n')


def install_runtime(root, image, runtime, work, tass, tass_args=()):
    blob = Path(runtime).read_bytes()
    load = int.from_bytes(blob[:2], 'little')
    end = load + len(blob) - 2
    if load != 0x0801 or end > 0x6000:
        raise ValueError('GMod3 runtime exceeds $0801..$5fff')
    padded = bytearray(0x5800)
    padded[load-0x0800:end-0x0800] = blob[2:]
    for n in range(3):
        cart.put_bank(image, n+1, padded[n*8192:(n+1)*8192])
    boot = Path(work)/'boot.bin'
    subprocess.run([str(tass), *tass_args, '--nostart', '-o', str(boot), str(Path(root)/'c64/gmod3/boot.asm')], check=True)
    if boot.stat().st_size != 8192:
        raise ValueError('GMod3 boot ROM must be exactly 8 KiB')
    cart.put_bank(image, 0, boot.read_bytes())


def assemble_cartridge(root, frames, mesh, *, tass, cartconv, outdir, stem,
                       size_mib=2, first_bank=4, colors=True, color_index=1,
                       background_color=0, border_color=0, gap=6, batch_budget=2048,
                       prefer='fps', tass_args=(), encode=None, source=None, reclaim_luts=False, page_frames=0, directory_bank=None):
    root, outdir = Path(root).resolve(), Path(outdir).resolve()
    if prefer not in ('fps', 'ram'):
        raise ValueError('GMod3 preference must be fps or ram')
    outdir.mkdir(parents=True, exist_ok=True)
    work = root/'build'/f'{stem}-gmod3'
    gen = work/'generated'
    gen.mkdir(parents=True, exist_ok=True)
    image, directory = pack_frames(frames, size_mib=size_mib, first_bank=first_bank,
        colors=colors, gap=gap, batch_budget=batch_budget, encode=encode, page_frames=page_frames)
    active_directory = directory[:page_frames] if page_frames else directory
    if page_frames:
        if page_frames != 128 or len(directory)%128 or directory_bank is None:
            raise ValueError('GMod3 paged collection requires complete 128-picture pages')
        if directory_bank in set(range(4)) | {d['bank'] for d in directory}:
            raise ValueError('GMod3 page directory overlaps reserved runtime or picture data')
        block=bytearray()
        for start in range(0,len(directory),128):
            ds=directory[start:start+128]
            for key,shift,mask in [('bank',0,255),('address',0,255),('address',8,255),('bytes',0,255),('bytes',8,255),('metadata_bytes',0,255),('metadata_bytes',8,255),('bank',8,255)]:
                block.extend(((d[key]>>shift)&mask) | (128 if key=='bytes' and shift==8 else 0) for d in ds)
        cart.put_bank(image,directory_bank,block)
    if reclaim_luts:
        from .hors_v3_effects import reclaim_tables
        reclaim_tables(gen/'tables.inc', active_directory, emit_directory)
    else:
        emit_directory(gen/'tables.inc', active_directory)
    emit_hud(gen/'hud.inc', mesh.name[:10], len(mesh.vertices), len(mesh.edges))
    shutil.copyfile(root/'c64/gmod3/stream-helper.asm', gen/'gmod3-helper.inc')
    src = source if source is not None else (root/'c64/gmod3/renderer.asm').read_text()
    src = src.replace('FRAME_COUNT = 48', f'FRAME_COUNT = {page_frames or len(frames)}', 1)
    src = src.replace('COLORS_ENABLED = 0', f'COLORS_ENABLED = {int(colors)}', 1)
    src = src.replace('V9_BYTE_SPANS = 0', 'V9_BYTE_SPANS = 1', 1)
    src = src.replace('PREFER_RAM = 0', f'PREFER_RAM = {int(prefer == "ram")}', 1)
    src = configure_asm_colors(src, color_index, background_color, border_color)
    src = src.replace('        .include "generated/hud.inc"', '        .include "generated/hud.inc"\n.if * > $1700\n.error "GMod3 HUD overlaps LUT"\n.endif')
    asm, runtime = work/'main.asm', work/'runtime.prg'
    asm.write_text(src)
    subprocess.run([str(tass), *tass_args, '--cbm-prg', '--vice-labels', '-l', str(outdir/f'{stem}.lbl'),
                    '-o', str(runtime), str(asm)], check=True, cwd=root)
    install_runtime(root, image, runtime, work, tass, tass_args)
    crt = outdir/f'{stem}.crt'
    info = cart.convert(image=image, raw=work/f'{stem}.bin', crt=crt, cartconv=cartconv,
                        name=f'GMOD3 {mesh.name}', cwd=root)
    manifest = dict(format='c643d-gmod3-stream-v1', version=1, experimental=True,
        renderer='gmod3-hors-v2', cartridge='GMod3', name=mesh.name, hud_name=mesh.name[:10], frames=len(frames),
        vertices=len(mesh.vertices), edges=len(mesh.edges), colors=colors,
        screen_color=hires_screen_byte(color_index, background_color), border_color=border_color,
        wire_format='hors-v2-batched-literal-spans-1', frame_data=directory,
        directory_ram_bytes=len(active_directory)*8,
        paged_directory_rom_bytes=len(directory)*8 if page_frames else 0,
        metadata_cache_bytes=3072,
        rom_frame_bytes=sum(d['bytes'] for d in directory), highest_bank=directory[-1]['bank'],
        runtime_work=f'build/{stem}-gmod3', capacity_mib=size_mib, preference=prefer,
        mapping='one bank select per fetch; $37 ROM reads / $35 RAM reads; bounded SEI sections',
        vector_override=False, audio=False, picture_reuse=False,
        encoding_choice=dict(gap=gap, batch_budget=batch_budget), container=info)
    manifest['build_evidence'] = dict(
        generated_asm_sha256=hashlib.sha256(asm.read_bytes()).hexdigest(),
        runtime_prg_sha256=hashlib.sha256(runtime.read_bytes()).hexdigest(),
        symbols_sha256=hashlib.sha256((outdir/f'{stem}.lbl').read_bytes()).hexdigest(),
        boot_sha256=hashlib.sha256((work/'boot.bin').read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256((gen/'gmod3-helper.inc').read_bytes()).hexdigest())
    (outdir/f'{stem}-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (work/'oracle.json').write_text(json.dumps([asdict(f) for f in frames])+'\n')
    occupied = len(set(range(4)) | {d['bank'] for d in directory} |
                   ({directory_bank} if directory_bank is not None else set()))
    print(f'Cart type: GMod3 | used: {occupied*8} KiB | free: {size_mib*1024-occupied*8} KiB | capacity: {size_mib*1024} KiB', flush=True)
    print(f'GMod3: {crt.name}; {size_mib} MiB; {len(frames)} pictures; banks {first_bank}..{directory[-1]["bank"]}', flush=True)
    return crt, manifest
