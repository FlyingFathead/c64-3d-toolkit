"""Experimental HORS-V3: shared colour addresses and optional packed indices.

Each frame covers every potentially changed screen cell with absolute values.
Addresses are shared across frames; direct bytes prioritize speed and packed
four-bit dictionary indices prioritize size. Absolute runs provide a fallback.
Any of the three buffers may be reused without resetting old colour spans.
Bitmap drawing remains HORS-V2 literal spans.
"""
from dataclasses import replace
import itertools
import json
from pathlib import Path
from . import hors_v2_stable as v2
from .optimize import picture_bytes

NAME = 'hors-renderer-v3'


def prepare_colors(frames, base_screen=0x10):
    maps = [picture_bytes(f, base_screen)[7680:] for f in frames]
    active = {i for m in maps for i, value in enumerate(m) if value != base_screen}
    prepared = []
    for frame, screen in zip(frames, maps):
        runs, i = [], 0
        while i < 960:
            start, value = i, screen[i]
            i += 1
            while i < 960 and screen[i] == value:
                i += 1
            touched = [j for j in range(start, i) if j in active]
            if not touched:
                continue
            first, end = touched[0], touched[-1] + 1
            while first < end:
                count = min(255, end - first)
                runs.append((first & 255, first >> 8, count, value))
                first += count
        new = replace(frame, color_spans=runs,
                      color_cells=sum(span[2] for span in runs))
        if picture_bytes(new, base_screen) != picture_bytes(frame, base_screen):
            raise AssertionError('V3 colour coverage changes the source picture')
        covered = {lo + hi * 256 + j for lo, hi, n, value in runs for j in range(n)}
        if not active.issubset(covered):
            raise AssertionError('V3 frame leaves stale screen cells')
        prepared.append(new)
    return prepared, dict(dynamic_screen_cells=len(active),
                          old_color_reset_removed=True,
                          previous_picture_dependency=False,
                          color_encoding='absolute runs covering every potentially changed cell',
                          old_spans=sum(len(f.color_spans) for f in frames),
                          new_spans=sum(len(f.color_spans) for f in prepared))


def color_plan(frames, base_screen=0x10):
    maps = [picture_bytes(f, base_screen)[7680:] for f in frames]
    active = sorted({i for m in maps for i, value in enumerate(m) if value != base_screen})
    runs = []
    for _, group in itertools.groupby(enumerate(active), lambda pair: pair[1]-pair[0]):
        cells = [value for index, value in group]
        start, end = cells[0], cells[-1]+1
        while start < end:
            count = min(255, end-start)
            runs.append((start, count)); start += count
    return active, runs


def color_plan_fits(frames, active, runs, palette=None):
    color_bytes = (len(active) + 1) // 2 if palette is not None else len(active)
    return len(runs) * 3 + len(palette or []) <= 256 and all(
        1 + 3 * len(f.clear_spans) + color_bytes <= 1024 for f in frames)


def literal_encoder(active, base_screen=0x10, gap=6, batch_budget=2048, palette=None):
    draw = v2.encoder(gap, batch_budget)
    def encode(frame, colors=True):
        block, meta = draw(frame, False)
        if not colors: return block, meta
        screen = picture_bytes(frame, base_screen)[7680:]
        values = bytes(screen[i] for i in active)
        if palette is not None:
            indices = [palette.index(value) for value in values]
            values = bytes((indices[i] << 4) | (indices[i+1] if i+1 < len(indices) else 0)
                           for i in range(0, len(indices), 2))
        data = block[:meta] + values + block[meta:]
        meta += len(values)
        if meta > 1024: raise ValueError('V3 colour literal metadata exceeds 1 KiB')
        if len(data) > 8192: raise ValueError('V3 literal picture exceeds one 8 KiB bank')
        return data, meta
    return encode


def patch_literal_runtime(text, runs, palette=None):
    text = patch_runtime(text)
    start = text.index('acfc_read_count:')
    end = text.index('screen_base_hi:', start)
    body = f"""; HORS-V3 addresses are shared by the entire animation.
        ldx render_slot
        lda screen_base_hi,x
        sta color_screen_base_hi
        ldx #0
v3_color_run:
        lda v3_color_lo,x
        sta PTR_LO
        lda v3_color_hi,x
        clc
        adc color_screen_base_hi
        sta PTR_HI
        lda v3_color_length,x
        sta color_cells_temp
        ldy #0
v3_color_copy:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        cpy color_cells_temp
        bne v3_color_copy
        tya
        clc
        adc STREAM_LO
        sta STREAM_LO
        bcc v3_color_next
        inc STREAM_HI
v3_color_next:
        inx
        cpx #{len(runs)}
        bne v3_color_run
        rts

""" if runs else '        rts\n\n'
    if palette is not None and runs:
        body = f"""; HORS-V3 packed four-bit colour-pair indices.
        ldx render_slot
        lda screen_base_hi,x
        sta color_screen_base_hi
        lda #0
        sta color_skip_temp
        ldx #0
v3_color_run:
        lda v3_color_lo,x
        sta PTR_LO
        lda v3_color_hi,x
        clc
        adc color_screen_base_hi
        sta PTR_HI
        lda v3_color_length,x
        sta color_cells_temp
v3_color_copy:
        lda color_skip_temp
        bne v3_color_low
        ldy #0
        lda (STREAM_LO),y
        sta color_value_temp
        lsr a
        lsr a
        lsr a
        lsr a
        inc color_skip_temp
        bne v3_color_lookup
v3_color_low:
        lda color_value_temp
        and #15
        dec color_skip_temp
        inc STREAM_LO
        bne v3_color_lookup
        inc STREAM_HI
v3_color_lookup:
        tay
        lda v3_color_palette,y
        ldy #0
        sta (PTR_LO),y
        inc PTR_LO
        bne v3_color_advanced
        inc PTR_HI
v3_color_advanced:
        dec color_cells_temp
        bne v3_color_copy
        inx
        cpx #{len(runs)}
        bne v3_color_run
        rts

"""
    text = text[:start] + body + text[end:]
    # V2 direct-only playback does not use the legacy vector-dispatch page.
    start = text.index('* = $4300\nv3_entry_hi:')
    end = text.index('* =', start+len('* = $4300'))
    table = ['* = $4300', 'v3_entry_hi = $4300 ; legacy vectors disabled', 'v3_entry_lo = $4f00 ; legacy vectors disabled']
    for name, values in [('lo',[o&255 for o,n in runs]),
                         ('hi',[o>>8 for o,n in runs]),
                         ('length',[n for o,n in runs])]:
        table += ['v3_color_'+name+':']
        if values: table += ['    .byte '+','.join(str(v) for v in values)]
    if palette is not None:
        table += ['v3_color_palette:']
        if palette:
            table += ['    .byte '+','.join(map(str,palette))]
    table += ['.if * > $4400', '.error "V3 colour plan overlaps screen RAM"', '.endif']
    return text[:start] + '\n'.join(table)+'\n' + text[end:]


def patch_runtime(text):
    old = '        ldx color_old_frame_temp\n        jsr reset_old_frame_colors'
    if text.count(old) != 1:
        raise ValueError('V3 expected exactly one old-colour reset call')
    return text.replace(old, '        ; HORS-V3: every changed cell is covered by the new frame.')


def assemble_cartridge(root, frames, mesh, *, draw_gap=6, batch_budget=2048, color_encoding='literal', interactive=False, **kwargs):
    """Build in V2's isolated staging tree; no old renderer source is modified."""
    from . import cartstream
    root = Path(root)
    base = (kwargs.get('color_index', 1) << 4) | kwargs.get('background_color', 0)
    colors = kwargs.get('colors', True)
    original = frames
    palette = None
    if color_encoding not in ('literal', 'indexed4'):
        raise ValueError('V3 color encoding must be literal or indexed4')
    plan_encoder = v2.encoder(draw_gap, batch_budget)
    literal = False
    runs = []
    if colors:
        active, runs = color_plan(frames, base)
        if color_encoding == 'indexed4':
            screen_maps = [picture_bytes(f, base)[7680:] for f in frames]
            palette = sorted({screen[i] for screen in screen_maps for i in active})
            if len(palette) > 16:
                raise ValueError('indexed4 requires at most 16 colour pairs; use literal')
        literal = color_plan_fits(frames, active, runs, palette)
        if literal:
            plan_encoder = literal_encoder(active, base, draw_gap, batch_budget, palette)
            policy = dict(dynamic_screen_cells=len(active), old_color_reset_removed=True,
                previous_picture_dependency=False, color_encoding='shared addresses plus packed 4-bit pair indices' if palette is not None else 'shared addresses plus absolute colour bytes',
                color_pair_dictionary=palette,
                shared_address_bytes=len(runs)*3, color_bytes_per_frame=(len(active)+1)//2 if palette is not None else len(active),
                extra_reserved_RAM_bytes=0, reused_vector_dispatch_page=[0x4300,0x4400])
        else:
            if color_encoding == 'indexed4':
                raise ValueError('indexed4 colour address plan exceeds reserved space; use literal')
            frames, policy = prepare_colors(frames, base)
    else:
        policy = dict(dynamic_screen_cells=0, color_updates=False,
                      old_color_reset_removed=False, previous_picture_dependency=False)
    # Selective clears are already prepared by the surface builder.
    kwargs['optimize'] = False
    with v2.staged(root) as stage:
        runtime = stage / 'c64/renderer-yunroll-cart-v10.asm'
        if colors:
            runtime.write_text(patch_literal_runtime(runtime.read_text(), runs, palette) if literal else patch_runtime(runtime.read_text()))
        if interactive:
            from .hors_v3_controls import configure
            runtime.write_text(configure(runtime.read_text(), palette=palette))
        old_pack = cartstream.pack_frames
        def pack(items, colors=True, **options):
            options['encoder'] = plan_encoder
            return old_pack(items, colors, **options)
        cartstream.pack_frames = pack
        try:
            kwargs['renderer'] = 'yunroll-cart-v10'
            crt, manifest = v2._object_assembler(stage, frames, mesh, **kwargs)
        finally:
            cartstream.pack_frames = old_pack
        v2.save_builds(stage, root)
    v2.describe(manifest, draw_gap, batch_budget)
    manifest.update(renderer=NAME, experimental=False,
        implementation='HORS-V2 literal drawing with HORS-V3 shared colour plan',
        color_policy=policy, wire_format='hors-v3-color-indexed4-v1' if palette is not None else 'hors-v3-color-literals-v1' if literal else 'hors-v3-complete-color-runs-v1',
        runtime_work=f"build/{kwargs['stem']}-stream-v10")
    if 'build_screen' in manifest:
        manifest['build_screen']['renderer'] = NAME
    if interactive:
        from .hors_v3_controls import describe
        describe(manifest)
    # The independent oracle stays the pre-optimisation picture set.
    from dataclasses import asdict
    (root / manifest['runtime_work'] / 'oracle.json').write_text(json.dumps([asdict(f) for f in original]))
    (Path(kwargs['outdir']) / (kwargs['stem'] + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    return crt, manifest
