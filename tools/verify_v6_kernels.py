#!/usr/bin/env python3
"""Check V6 X-major partial/full transitions against the independent pixel oracle."""
import argparse
import json
from pathlib import Path

from c643d.cartscene import assemble_scene
from c643d.pipeline import oriented_dda, encode_run
from verify_cart_stream import verify
from verify_v5_kernels import frame, scene
from profile_cart_stream import profile


def check(tass, cartconv, vice, vice_data):
    root = Path(__file__).resolve().parents[1]
    out = root / 'build/v6-kernel-checks'
    frames = []
    cases = set()
    # Counts straddle both the partial head and subsequent full/tail boundaries.
    for phase in range(8):
        for negative in (False, True):
            for count in (2, 3, 7, 8, 9, 15, 16, 17, 31, 126, 127):
                for mask in (0, 255, 85, 170):
                    cases.add((phase, (phase + count + mask) & 7, negative, count, mask))
    # Exercise every X/Y entry-phase pair around the bitmap row boundary.
    for phase in range(8):
        for yphase in range(8):
            for negative in (False, True):
                for mask in (0, 255, 85, 170):
                    cases.add((phase, yphase, negative, 8, mask))
    for phase, yphase, negative, count, mask in sorted(cases):
        x = 120 + phase
        y = (152 if negative else 24) + yphase
        offset = (y // 8) * 320 + (x // 8) * 8
        control = phase | (yphase << 3) | (128 if negative else 0)
        chunks = (phase + count + 7) // 8
        record = (offset & 255, offset >> 8, count, control, *([mask] * chunks))
        frames.append(frame(record))
    crt, _ = assemble_scene(
        root, frames, scene(frames, 'V6 X KERNEL CHECK'),
        tass=tass, cartconv=cartconv, outdir=out, stem='v6-x-kernels',
        hud_text='V6 X KERNEL CHECK', frame_ticks=1, intro=False,
        ending=False, text_overlay=False, renderer='yunroll-cart-v6-scene',
        optimize=False,
    )
    result = dict(kernel_cases=len(frames), validation=verify(crt, vice, vice_data))
    # Mixed resident hits/misses, consecutive holds, colour-only changes and
    # the scene directory page transition must survive direct metadata loading.
    def line(coords, color):
        dda = oriented_dda(*coords)
        return frame(encode_run(dda, 0, len(dda['points']) - 1), color)
    a = line((25, 50, 72, 50), 16)
    b = line((50, 20, 50, 70), 32)
    c = line((20, 20, 62, 62), 112)
    d = line((25, 50, 72, 50), 32)
    pattern = [a, b, c, a, b, a, a, a, d, d, a, b, a, c, a]
    holds = [pattern[i % len(pattern)] for i in range(270)]
    crt, _ = assemble_scene(
        root, holds, scene(holds, 'V6 REUSE CHECK'), tass=tass, cartconv=cartconv,
        outdir=out, stem='v6-reuse', hud_text='V6 REUSE CHECK', frame_ticks=3,
        intro=True, ending=True, text_overlay=False, renderer='yunroll-cart-v6-scene',
    )
    result['reuse'] = verify(crt, vice, vice_data)
    assert result['reuse']['reused_samples'] > 150
    timing = profile(crt, vice, vice_data)
    ideal = len(holds) * 3 * 19656 / 985248
    assert abs(timing['measured_seconds'] - ideal) < 0.10
    result.update(hold_seconds=timing['measured_seconds'], ideal_hold_seconds=ideal)
    (out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tass', default='64tass')
    parser.add_argument('--cartconv', default='cartconv')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data', required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.tass, args.cartconv, args.vice, args.vice_data), indent=2))
