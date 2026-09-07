"""Lossless post-colour vector optimization for the opt-in V5 cartridge path."""
from collections import Counter
from dataclasses import replace
import hashlib
from .pipeline import decode_record_points


def picture_bytes(frame, screen=0x10):
    bitmap = bytearray(7680)
    colors = bytearray([screen])*960
    for rec in frame.records:
        for x, y in decode_record_points(rec):
            bitmap[(y//8)*320+(x//8)*8+(y&7)] |= 128 >> (x&7)
    for lo, hi, n, color in frame.color_spans:
        off = lo+(hi<<8)
        colors[off:off+n] = bytes([color])*n
    return bytes(bitmap+colors)


def remove_redundant_runs(frame):
    """Remove whole records only; original colour votes/spans are already final.

    First keep one copy of each exact record. Then remove short covered records
    one at a time, decrementing coverage after each removal. The changing counts
    are the coverage witness: mutually covering records cannot all disappear.
    Retained records stay in original order, with no new fragments or formats.
    """
    unique = list(dict.fromkeys(tuple(r) for r in frame.records))
    points = [set(decode_record_points(r)) for r in unique]
    coverage = Counter(p for pts in points for p in pts)
    keep = [True]*len(unique)
    for i in sorted(range(len(unique)), key=lambda i: (len(points[i]), -i)):
        if all(coverage[p] > 1 for p in points[i]):
            keep[i] = False
            for p in points[i]:
                coverage[p] -= 1
    records = [r for i, r in enumerate(unique) if keep[i]]
    return replace(frame, records=records, raw_pixels=sum(r[2] for r in records))


def optimize_frames(frames, screen=0x10):
    result = []
    # Use complete bytes as dictionary keys, so equality is exact, not hash-only.
    pictures = {}
    aliases = []
    before_runs = before_bytes = after_runs = after_bytes = 0
    holds = 0
    previous = None
    for i, frame in enumerate(frames):
        original = picture_bytes(frame, screen)
        optimized = remove_redundant_runs(frame)
        if picture_bytes(optimized, screen) != original:
            raise AssertionError(f'optimization changed frame {i}')
        if optimized.color_spans != frame.color_spans or optimized.clear_spans != frame.clear_spans:
            raise AssertionError('optimization changed resolved metadata')
        before_runs += len(frame.records)
        after_runs += len(optimized.records)
        before_bytes += sum(map(len, frame.records))
        after_bytes += sum(map(len, optimized.records))
        alias = pictures.setdefault(original, i)
        aliases.append(alias)
        holds += original == previous
        previous = original
        result.append(optimized)
    return result, dict(original_runs=before_runs, retained_runs=after_runs,
                        removed_runs=before_runs-after_runs, original_record_bytes=before_bytes,
                        retained_record_bytes=after_bytes, saved_record_bytes=before_bytes-after_bytes,
                        unique_pictures=len(pictures), duplicate_pictures=len(frames)-len(pictures),
                        consecutive_holds=holds, picture_references=aliases,
                        bitmap_and_colors_preserved=True)
