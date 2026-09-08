"""Experimental whole-frame packing for hors-render-v1 recovery builds only."""
import hashlib
from c643d.cartscene import MAX_SCENE_FRAMES
from c643d.cartstream import frame_block
from c643d.cartridge import new_easyflash_image, easyflash_offset


class CapacityError(ValueError):
    pass

def pack_scene_frames(frames, colors=True, *, aliases=None, encoder=frame_block, direct_bytes=False):
    if not 1 <= len(frames) <= MAX_SCENE_FRAMES:
        raise ValueError('invalid scene frame count')
    if aliases is None:
        aliases = list(range(len(frames)))
    if len(aliases) != len(frames) or any(not isinstance(a, int) or not 0 <= a <= i for i, a in enumerate(aliases)):
        raise ValueError('aliases must reference current or preceding frames')
    blocks = {}
    for i, frame in enumerate(frames):
        if aliases[i] == i:
            block, meta = encoder(frame, colors)
            if not 2 <= len(block) <= 8192 or not 0 <= meta < len(block)-1:
                raise ValueError(f'frame {i}: invalid block size/metadata ({len(block)} bytes)')
            blocks[i] = (block, meta)
    # Compare original sequential placement with best-fit decreasing; never use
    # more banks than the original placement. Whole blocks never cross banks.
    def layout(order, compact):
        used = []; locations = {}
        for i in order:
            size = len(blocks[i][0])
            choices = [b for b, n in enumerate(used) if n + size <= 8192] if compact else ([len(used)-1] if used and used[-1]+size <= 8192 else [])
            bank = min(choices, key=lambda b: (8192-used[b]-size, b)) if choices else len(used)
            if bank == len(used): used.append(0)
            locations[i] = (bank, used[bank]); used[bank] += size
        return used, locations
    original = layout(blocks, False)
    packed = layout(sorted(blocks, key=lambda i: (-len(blocks[i][0]), i)), True)
    used, locations = min((packed, original), key=lambda x: len(x[0]))
    payload = sum(len(b) for b, m in blocks.values())
    print(f'Packing: payload={payload} bytes; sequential={len(original[0])} banks; packed={len(used)} banks; available=122; unused in allocated banks={len(used)*8192-payload} bytes', flush=True)
    if len(used) > 122:
        raise CapacityError(f'EasyFlash capacity: packing requires {len(used)} x 8192-byte banks; 122 available; payload={payload} bytes; payload lower bound={(payload+8191)//8192} banks')
    image = new_easyflash_image(); directory = []
    for i, frame in enumerate(frames):
        if aliases[i] != i:
            directory.append(dict(directory[aliases[i]], frame=i, reference_frame=aliases[i])); continue
        block, meta = blocks[i]; place, offset = locations[i]
        chip = 'roml' if place < 61 else 'romh'; bank = 3 + place % 61
        address = (0x8000 if chip == 'roml' else 0xa000) + offset
        start = easyflash_offset(bank, chip, offset); image[start:start+len(block)] = block
        entry = dict(frame=i, chip=chip, bank=bank, address=address, bytes=len(block), metadata_bytes=meta, runs=len(frame.records), sha256=hashlib.sha256(block).hexdigest())
        if encoder is not frame_block: entry['encoding'] = 'byte-spans' if block[meta+1] & 128 else 'vectors'
        directory.append(entry)
    for page in range((len(frames)+255)//256):
        records = directory[page*256:(page+1)*256]
        values = [[d['bank'] for d in records], [d['address']&255 for d in records], [d['address']>>8 for d in records], [d['bytes']&255 for d in records], [(d['bytes']>>8) | (0x80 if direct_bytes and d.get('encoding')=='byte-spans' else 0) for d in records], [d['metadata_bytes']&255 for d in records], [d['metadata_bytes']>>8 for d in records]]
        blob = b''.join(bytes(a).ljust(256,b'\0') for a in values)
        start = easyflash_offset(1+page//4,'romh',(page%4)*1792)
        image[start:start+len(blob)] = blob
    return image, directory
