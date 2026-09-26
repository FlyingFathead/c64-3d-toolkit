"""Opt-in EasyFlash clear planner; preserved renderers are never edited.

Pictures remain independent. Each slot retains the clear list for the picture
actually written there, so repeated, reverse and skipped traversal stay valid.
The cost model ranks candidates; only VICE measurements establish performance.
"""
from contextlib import contextmanager
from copy import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from . import hors_v3 as v3, hors_v2_stable as v2
from .optimize import picture_bytes

NAME = 'hors-renderer-v5'
GAPS = (1, 2, 3, 4, 6, 8, 10, 12, 16, 24, 32, 48, 64, 96, 128, 255)


def clear_cost(spans):
    """Heuristic CPU work, excluding IRQs, VIC stalls and metadata transfer."""
    return sum(100 + 67*(n//8) + 13*(n%8) if hi & 128 else 90 + 69*n
               for lo, hi, n in spans)


def plan_clear(frame, limit):
    bitmap = picture_bytes(frame)[:7680]
    dirty = [i for i, value in enumerate(bitmap) if value]
    if not dirty:
        return replace(frame, clear_spans=[])
    candidates = [frame.clear_spans]
    for gap in GAPS:
        runs = []
        for offset in dirty:
            if runs and offset-runs[-1][1] <= gap and offset-runs[-1][0] < 255:
                runs[-1][1] = offset
            else:
                runs.append([offset, offset])
        candidates.append([(a & 255, (a >> 8) | 128, b-a+1) for a, b in runs])
    fitting = [spans for spans in candidates if len(spans) <= limit]
    if not fitting:
        raise ValueError('HORS-V5 clear plan does not fit the metadata slot')
    selected = min(fitting, key=lambda spans: (clear_cost(spans), len(spans)))
    covered = set()
    for lo, hi, count in selected:
        start = lo | ((hi & 127) << 8)
        end = start + count*(1 if hi & 128 else 8)
        if not 0 <= start < end <= 7680 or not 1 <= count <= 255:
            raise ValueError('HORS-V5 clear span crosses bitmap/HUD bounds')
        covered.update(range(start, end))
    if not set(dirty) <= covered:
        raise ValueError('HORS-V5 clear plan misses nonzero bitmap bytes')
    return replace(frame, clear_spans=selected)


def patch_clear(source):
    if source.count('cofs_byte_loop:') != 1:
        raise ValueError('Expected one preserved byte-clear kernel')
    start = source.index('cofs_byte_loop:')
    end = source.index('\n.if COLORS_ENABLED', start)
    kernel = '''cofs_byte_loop:
        ; Y is a byte count, 1..255. Clear the remainder, then groups of eight.
        tya
        and #7
        tax
        lda #0
        cpx #0
        beq hors_v5_clear_group
hors_v5_clear_tail:
        dey
        sta (PTR_LO),y
        dex
        bne hors_v5_clear_tail
        cpy #0
        beq hors_v5_clear_done
hors_v5_clear_group:
''' + ''.join('        dey\n        sta (PTR_LO),y\n' for _ in range(8)) + '''        bne hors_v5_clear_group
hors_v5_clear_done:
        dec clear_spans_remaining
        beq cofs_done
        jmp cofs_span
'''
    return source[:start] + kernel + source[end:]


@contextmanager
def installed():
    """Scope the existing staging hooks to one build, including error paths."""
    with v2._lock:
        old_plan, old_stage = v3.encoding_plan, v2.staged

        def plan(frames, colors=True, *args, **kwargs):
            fs, encode, policy, literal, runs, palette = old_plan(frames, colors, *args, **kwargs)
            planned = []
            for frame in fs:
                _, metadata = encode(frame, colors)
                other = metadata - 3*len(frame.clear_spans)
                selected = plan_clear(frame, min(255, (1024-other)//3))
                _, size = encode(selected, colors)
                if size > 1024:
                    raise ValueError('HORS-V5 metadata exceeds its reserved 1 KiB slot')
                planned.append(selected)
            policy = dict(policy, clear_plan='hors-v5-bounded-cost-search',
                clear_cost_model='heuristic CPU cycles; excludes stalls, IRQs and fetch',
                estimated_clear_cycles_before=sum(clear_cost(f.clear_spans) for f in fs),
                estimated_clear_cycles_after=sum(clear_cost(f.clear_spans) for f in planned))
            return planned, encode, policy, literal, runs, palette

        @contextmanager
        def staged(*args, **kwargs):
            with old_stage(*args, **kwargs) as stage:
                suffix = '-scene' if kwargs.get('scene') else ''
                runtime = stage / f'c64/renderer-yunroll-cart-v10{suffix}.asm'
                runtime.write_text(patch_clear(runtime.read_text()))
                yield stage

        v3.encoding_plan, v2.staged = plan, staged
        try:
            yield
        finally:
            v3.encoding_plan, v2.staged = old_plan, old_stage


def describe_output(crt):
    """Label a newly assembled V5 output after the scoped build has finished."""
    from .renderer_labels import label_new_easyflash
    crt = Path(crt)
    path = crt.with_name(crt.stem + '-manifest.json')
    meta = json.loads(path.read_text())
    if meta.get('build_screen'):
        evidence = label_new_easyflash(crt, 'hors-v5-c1')
        meta['build_screen']['renderer'] = 'hors-v5-c1'
    else:
        digest = hashlib.sha256(crt.read_bytes()).hexdigest()
        evidence = dict(original_crt_sha256=digest, crt_sha256=digest, bytes=0,
            change='authored scene without a standard startup renderer field')
    meta.update(renderer=NAME, renderer_label='hors-v5-c1', experimental=True, candidate="c1",
        implementation='HORS-V3 pictures/colour plan with HORS-V5 bounded clear search and unrolled byte clear',
        cartridge='EasyFlash', renderer_label_update=evidence)
    path.write_text(json.dumps(meta, indent=2)+'\n')
    return meta


def build(args):
    from . import cli
    if getattr(args, 'cart_type', None) not in (None, 'easyflash'):
        raise ValueError('HORS-V5 currently requires EasyFlash; HORS-V4 retains GMod3')
    core = copy(args)
    core.renderer = core.requested_renderer = 'hors-renderer-v3'
    core.run = False
    if not core.output:
        source = core.blend or core.scene or core.obj or core.svg or core.object or core.shape
        core.output = Path(source or 'object').stem + '-hors-v5-c1'
    core.output = core.output.removesuffix('.crt')
    with installed():
        result = cli.cmd_build(core)
    if result or core.no_assemble:
        return result
    out = Path(core.output_dir).resolve() if core.output_dir else cli.BUILD
    crt = out / (core.output + '.crt')
    describe_output(crt)
    print('Renderer: hors-v5-c1 | cartridge: EasyFlash | experimental clear optimizer', flush=True)
    if args.run:
        vice = cli.resolve_executable(args.vice, 'vice')
        if not vice:
            raise ValueError('VICE not found')
        return cli.run_cartridge(vice, crt, args.vice_args,
            clean_settings=args.vice_clean_settings, cwd=cli.ROOT)
    return 0
