"""V10 byte-first pictures: prefer direct spans, with a bank-size vector fallback.

The metadata is unchanged. Bit 15 of the record count selects byte spans:
(offset low, offset high, length 1..255, literal bitmap bytes). Otherwise the
payload is the unchanged V7 vector stream. No previous-picture dependency.
"""
from .optimize import picture_bytes


def spans_for_bitmap(bitmap):
    if len(bitmap) != 7680:
        raise ValueError('V8 requires the 192-line bitmap')
    spans = []
    first = last = None
    for offset, value in enumerate(bitmap):
        if not value:
            continue
        if first is not None and (offset-last > 3 or offset-first >= 255):
            spans.append((first, bytes(bitmap[first:last+1])))
            first = None
        if first is None:
            first = offset
        last = offset
    if first is not None:
        spans.append((first, bytes(bitmap[first:last+1])))
    return spans


def frame_block(frame, colors=True):
    from .cartstream import frame_block as vector_block
    original, meta = vector_block(frame, colors)
    bitmap = picture_bytes(frame)[:7680]
    spans = spans_for_bitmap(bitmap)
    data = bytearray(original[:meta])
    data.extend((0x8000 | len(spans)).to_bytes(2, 'little'))
    for offset, values in spans:
        data.extend((offset & 255, offset >> 8, len(values)))
        data.extend(values)
    # A strict win avoids dispatching byte mode for empty or tied pictures.
    if len(data) <= 8192:
        return bytes(data), meta
    if len(original) <= 8192:
        return original, meta
    raise ValueError("V10 picture exceeds one 8 KiB frame arena")


def configure_source(source, directory):
    marker = 'V8_BYTE_SPANS = 0'
    if marker not in source:
        raise ValueError('V8 source lacks byte-span configuration')
    enabled = any(d.get('encoding') == 'byte-spans' for d in directory)
    return source.replace(marker, f'V8_BYTE_SPANS = {int(enabled)}', 1)
