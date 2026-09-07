"""Join compatible visible runs without changing their pixel union or colours.

The existing format carries explicit minor-axis step bits. Connected runs can
share one header when their combined path keeps the same major axis and minor
direction, has no gap, and fits the 127-pixel limit. No straight-line fitting or
approximation is involved; every encoded result is decoded and compared.
"""
from collections import defaultdict
from dataclasses import replace
from .pipeline import decode_record_points, encode_run
from .optimize import picture_bytes


def join_frame_runs(frame, *, order='input'):
    records = [tuple(r) for r in frame.records]
    points = [decode_record_points(r) for r in records]
    starts = defaultdict(list)
    for i, (rec, path) in enumerate(zip(records, points)):
        starts[((rec[3] >> 6) & 1, path[0])].append(i)
    active = set(range(len(records)))
    output = []
    indices = list(range(len(records)))
    if order == 'position':
        indices.sort(key=lambda i: ((records[i][3] >> 6) & 1,
                                   points[i][0][(records[i][3] >> 6) & 1],
                                   points[i][0][1 - ((records[i][3] >> 6) & 1)], i))
    elif order != 'input':
        raise ValueError('unknown join ordering')
    for i in indices:
        if i not in active:
            continue
        active.remove(i)
        axis = (records[i][3] >> 6) & 1
        minor = 1 - axis
        path = points[i]
        direction = 0
        if path[-1][minor] != path[0][minor]:
            direction = 1 if path[-1][minor] > path[0][minor] else -1
        while True:
            end = path[-1]
            neighbors = [end]
            for delta in (-1, 0, 1):
                neighbor = list(end)
                neighbor[axis] += 1
                neighbor[minor] += delta
                neighbors.append(tuple(neighbor))
            candidates = []
            for neighbor in neighbors:
                for j in starts.get((axis, neighbor), ()):
                    if j not in active:
                        continue
                    other = points[j]
                    shared = other[0] == end
                    length = len(path) + len(other) - int(shared)
                    if length > 127:
                        continue
                    deltas = [other[-1][minor] - other[0][minor], other[0][minor] - end[minor]]
                    signs = {1 if d > 0 else -1 for d in deltas if d}
                    if direction:
                        signs.add(direction)
                    if len(signs) > 1:
                        continue
                    candidates.append((int(shared), len(other), -j, j, shared, next(iter(signs), 0)))
            if not candidates:
                break
            _, _, _, j, shared, direction = max(candidates)
            active.remove(j)
            path = path + points[j][int(shared):]
        if len(path) == len(points[i]):
            output.append(records[i])
            continue
        encoded = encode_run(dict(axis=axis, negative=direction < 0, points=path), 0, len(path) - 1)
        if decode_record_points(encoded) != path:
            raise AssertionError('joined record changed its pixel path')
        output.append(encoded)
    result = replace(frame, records=output, raw_pixels=sum(r[2] for r in output))
    if picture_bytes(result) != picture_bytes(frame):
        raise AssertionError('joining changed bitmap or resolved colours')
    return result, dict(original_runs=len(records), retained_runs=len(output),
                        merged_runs=len(records) - len(output),
                        saved_record_bytes=sum(map(len, records)) - sum(map(len, output)))


def join_frames(frames):
    result = []
    totals = dict(original_runs=0, retained_runs=0, merged_runs=0, saved_record_bytes=0)
    for frame in frames:
        candidates = [join_frame_runs(frame, order=order) for order in ('input', 'position')]
        joined, stats = min(candidates, key=lambda item: (len(item[0].records),
                            sum(map(len, item[0].records)), item[0].raw_pixels))
        result.append(joined)
        for key, value in stats.items():
            totals[key] += value
    return result, dict(bitmap_and_colors_preserved=True, **totals)
