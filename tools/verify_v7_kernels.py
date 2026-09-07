#!/usr/bin/env python3
"""Check V7 X/Y kernels, byte clearing, and holds against independent pixels."""
import argparse
import json
from pathlib import Path

from c643d.cartscene import assemble_scene
from c643d.pipeline import oriented_dda, encode_run
from verify_cart_stream import verify
from verify_v5_kernels import frame, scene
from profile_cart_stream import profile


def check(tass, cartconv, vice, vice_data, prefer="fps"):
    root = Path(__file__).resolve().parents[1]
    out = root / f'build/v7-kernel-checks-{prefer}'
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
    # Y loops/full blocks: all phases, signs, boundary counts and step masks.
    for phase in range(8):
        for neg in (False, True):
            for count in (2,7,8,9,15,16,17,126,127):
                for mask in (0,255,85,170):
                    x = 192 if neg else 64
                    y = 16 + phase
                    off = (y//8)*320 + (x//8)*8
                    ctl = (x&7) | ((y&7)<<3) | 64 | (128 if neg else 0)
                    rec = (off&255,off>>8,count,ctl,*([mask]*((phase+count+7)//8)))
                    frames.append(frame(rec))
    # Tagged byte spans cross cells and pages, including the 0=256 loop count.
    from c643d.pipeline import FrameBuild
    for start in (250, 7097):
        for count in (1, 7, 8, 31, 127, 128, 255, 256):
            records = []
            cells = set()
            for off in range(start, start+count):
                row, cellbyte = divmod(off,320)
                col, phase = divmod(cellbyte,8)
                x, y = col*8, row*8+phase
                dda = oriented_dda(x,y,x+1,y)
                records.append(encode_run(dda,0,1))
                cells.add(off//8)
            colors = [(c&255,c>>8,1,112) for c in sorted(cells)]
            frames.append(FrameBuild(records,[(start&255,(start>>8)|128,count&255)],
                                     count*2,count*2,[],colors))
    crt, _ = assemble_scene(
        root, frames, scene(frames, 'V7 KERNEL CHECK'),
        tass=tass, cartconv=cartconv, outdir=out, stem='v7-kernels',
        hud_text='V7 KERNEL CHECK', frame_ticks=1, intro=False,
        ending=False, text_overlay=False, renderer='yunroll-cart-v7-scene',
        optimize=False, prefer=prefer,
    )
    result = dict(preference=prefer, kernel_cases=len(frames), validation=verify(crt, vice, vice_data))
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
        root, holds, scene(holds, 'V7 REUSE CHECK'), tass=tass, cartconv=cartconv,
        outdir=out, stem='v7-reuse', hud_text='V7 REUSE CHECK', frame_ticks=3,
        intro=True, ending=True, text_overlay=False, renderer='yunroll-cart-v7-scene', prefer=prefer,
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
    parser.add_argument('--prefer', choices=('fps','ram'), default='fps')
    args = parser.parse_args()
    print(json.dumps(check(args.tass, args.cartconv, args.vice, args.vice_data, args.prefer), indent=2))
