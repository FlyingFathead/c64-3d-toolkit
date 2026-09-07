"""V7 clearing plans: select byte ranges without adding metadata records.

The high bit of a clear span's offset high byte selects a byte count instead
of a cell count. Geometry offsets use only bits 0..4. Colour spans are unchanged.
The three-byte record and one-byte span count stay the same size as V6.
"""
from dataclasses import replace
from .pipeline import decode_record_points


BYTE_RANGE = 0x80


def selective_clear(frame):
    """Trim each existing span when a bounded byte loop is estimated cheaper.

    Compare 69 cycles per unrolled cell with 11 per byte, retaining an eight
    cycle margin for the differing setup/dispatch costs. This is a selection
    estimate, not an emulator timing claim. Each replacement has the same
    three-byte representation, so cache and ROM capacities cannot grow.
    """
    dirty = set()
    for record in frame.records:
        for x, y in decode_record_points(record):
            dirty.add((y // 8) * 320 + (x // 8) * 8 + (y & 7))
    spans = []
    cell_bytes = selected_bytes = byte_spans = 0
    for lo, hi, count in frame.clear_spans:
        start = lo | (hi << 8)
        if not (0 <= start < 7680 and 1 <= count <= 32 and start + count * 8 <= 7680):
            raise ValueError('V7 requires valid geometry cell spans')
        touched = [offset for offset in range(start, start + count * 8) if offset in dirty]
        cell_bytes += count * 8
        if touched:
            first, last = touched[0], touched[-1]
            length = last - first + 1
            if length <= 255 and 11 * length + 8 < 69 * count:
                spans.append((first & 255, (first >> 8) | BYTE_RANGE, length))
                selected_bytes += length
                byte_spans += 1
                continue
        spans.append((lo, hi, count))
        selected_bytes += count * 8
    return replace(frame, clear_spans=spans), dict(
        cell_spans=len(spans) - byte_spans, byte_spans=byte_spans,
        original_clear_bytes=cell_bytes, selected_clear_bytes=selected_bytes,
        metadata_bytes_added=0,
    )


def selective_clear_frames(frames):
    result = []
    totals = dict(cell_spans=0, byte_spans=0, original_clear_bytes=0,
                  selected_clear_bytes=0, metadata_bytes_added=0)
    for frame in frames:
        selected, stats = selective_clear(frame)
        result.append(selected)
        for key, value in stats.items():
            totals[key] += value
    return result, dict(format='v7-mixed-cell-byte-spans', **totals)
