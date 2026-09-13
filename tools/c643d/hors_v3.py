"""HORS-V3: shared colour addresses and optional packed indices.

Each frame covers every potentially changed screen cell with absolute values.
Addresses are shared across frames; direct bytes prioritize speed and packed
four-bit dictionary indices prioritize size. Absolute runs provide a fallback.
Any of the three buffers may be reused without resetting old colour spans.
Bitmap drawing remains HORS-V2 literal spans.
"""
from dataclasses import replace
from contextlib import contextmanager
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


def compact_color_addresses(active):
    """Cover gaps within screen rows when sparse shared addresses exceed a page."""
    rows = {}
    for cell in active:
        row, col = divmod(cell, 40)
        low, high = rows.get(row, (col, col))
        rows[row] = min(low, col), max(high, col)
    runs = [(row * 40 + low, high - low + 1) for row, (low, high) in sorted(rows.items())]
    return [cell for start, count in runs for cell in range(start, start + count)], runs


def color_plan_fits(frames, active, runs, palette=None):
    color_bytes = (len(active) + 1) // 2 if palette is not None else len(active)
    return len(runs) * 3 + len(palette or []) <= 256 and all(
        len(f.clear_spans) <= 255 and 1 + 3 * len(f.clear_spans) + color_bytes <= 1024 for f in frames)


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


def compact_clear_spans(frame):
    """Bound fragmented clears to <=32-cell spans within each bitmap row.

    Clears may cover additional zero bytes. Pixels and colour cells are unchanged.
    Spans end at the last used cell; the bottom HUD row is excluded.
    """
    rows = {}
    for lo, hi, count in frame.clear_spans:
        start = lo | ((hi & 0x7f) << 8)
        end = start + count * (1 if hi & 0x80 else 8)
        if not 0 <= start < end <= 7680:
            raise ValueError('Invalid bitmap clear span')
        for offset in range(start, end):
            row, col = divmod(offset, 320)
            cell = col // 8
            low, high = rows.get(row, (cell, cell))
            rows[row] = min(low, cell), max(high, cell)
    spans = []
    for row, (low, high) in sorted(rows.items()):
        start = row * 320 + low * 8
        count=high-low+1
        while count:
            part=min(count,32)
            spans.append((start & 255,start >> 8,part))
            start+=part*8;count-=part
    return replace(frame, clear_spans=spans) if len(spans) < len(frame.clear_spans) else frame


def encoding_plan(frames, colors=True, base=0x10, draw_gap=6, batch_budget=2048, color_encoding='literal'):
    """Shared preflight/assembly choice; never discard pixels or source samples."""
    palette = None
    if color_encoding not in ('literal', 'indexed4'):
        raise ValueError('V3 color encoding must be literal or indexed4')
    plan_encoder = v2.encoder(draw_gap, batch_budget)
    literal = False
    runs = []
    clear_compaction = 0
    if colors:
        active, runs = color_plan(frames, base)
        if len(runs) * 3 + (16 if color_encoding == 'indexed4' else 0) > 256:
            active, runs = compact_color_addresses(active)
        if color_encoding == 'indexed4':
            screen_maps = [picture_bytes(f, base)[7680:] for f in frames]
            palette = sorted({screen[i] for screen in screen_maps for i in active})
            if len(palette) > 16:
                raise ValueError('indexed4 requires at most 16 colour pairs; use literal')
        if not color_plan_fits(frames, active, runs, palette):
            compacted = [compact_clear_spans(f) for f in frames]
            if color_plan_fits(compacted, active, runs, palette):
                clear_compaction = sum(a.clear_spans != b.clear_spans for a, b in zip(frames, compacted))
                frames = compacted
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
        compacted = [compact_clear_spans(f) if len(f.clear_spans) > 255 else f for f in frames]
        clear_compaction = sum(a.clear_spans != b.clear_spans for a, b in zip(frames, compacted))
        frames = compacted
        policy = dict(dynamic_screen_cells=0, color_updates=False,
                      old_color_reset_removed=False, previous_picture_dependency=False)
    policy['clear_metadata_compacted_frames'] = clear_compaction
    return frames, plan_encoder, policy, literal, runs, palette


def assemble_cartridge(root, frames, mesh, *, draw_gap=6, batch_budget=2048, color_encoding='literal', interactive=False, background_effect='none', include_starfield=True, starfield_profile=None, mode_frames=0, presentation_variants=(), occlusion_bounds=None, hud_visible=True, allow_hud_toggle=None, exhibition_default="disabled", exhibition_order="sequential", exhibition_interval=5, **kwargs):
    """Build in V2's isolated staging tree; no old renderer source is modified."""
    from . import cartstream
    root = Path(root)
    base = (kwargs.get('color_index', 1) << 4) | kwargs.get('background_color', 0)
    colors = kwargs.get('colors', True)
    original = frames
    allow_hud_toggle=interactive if allow_hud_toggle is None else allow_hud_toggle
    if allow_hud_toggle and not interactive:
        raise ValueError('HUD toggles require an interactive cart')
    stars_included = include_starfield and (background_effect != 'none' or interactive)
    effects = stars_included or bool(mode_frames)
    if starfield_profile is not None and (not interactive or not stars_included or starfield_profile not in ('full','light')):
        raise ValueError('Starfield profile requires an interactive cart with included stars')
    if not include_starfield and background_effect != 'none':
        raise ValueError('Cannot enable an excluded starfield')
    if background_effect not in ('none', 'starfield-forward'):
        raise ValueError('Unknown V3 background effect')
    if mode_frames and len(frames) != mode_frames * (4+2*len(presentation_variants)):
        raise ValueError('Presentation frame count does not match the selected variants')
    if mode_frames and color_encoding != 'literal':
        raise ValueError('Presentation modes currently require literal colour encoding')
    frames, plan_encoder, policy, literal, runs, palette = encoding_plan(
        frames, colors, base, draw_gap, batch_budget, color_encoding)
    # Selective clears are already prepared by the surface builder.
    kwargs['optimize'] = False
    with v2.staged(root) as stage:
        runtime = stage / 'c64/renderer-yunroll-cart-v10.asm'
        if colors:
            runtime.write_text(patch_literal_runtime(runtime.read_text(), runs, palette) if literal else patch_runtime(runtime.read_text()))
        if interactive:
            from .hors_v3_controls import configure
            runtime.write_text(configure(runtime.read_text(), palette=palette))
        if effects:
            from .hors_v3_effects import configure as configure_effects, reclaim_tables
            runtime.write_text(configure_effects(runtime.read_text(), starfield=background_effect!='none',
                interactive=interactive, mode_frames=mode_frames, include_starfield=stars_included, variants=presentation_variants))
        if interactive:
            from .hors_v3_speed import configure as configure_speed
            runtime.write_text(configure_speed(runtime.read_text(), samples=mode_frames or len(frames)))
            from .hors_v3_help import configure as configure_help
            from . import __version__
            runtime.write_text(configure_help(runtime.read_text(), version=__version__, effects=effects, modes=bool(mode_frames), stars=stars_included, variants=presentation_variants,hud=allow_hud_toggle,interval=exhibition_interval))
            if stars_included and occlusion_bounds is not None:
                from .hors_v3_occlusion import configure as configure_occlusion
                runtime.write_text(configure_occlusion(runtime.read_text(),occlusion_bounds))
            if stars_included:
                from .hors_v3_density import configure as configure_density
                runtime.write_text(configure_density(runtime.read_text(), opaque=occlusion_bounds is not None))
                from .hors_v3_star_modes import configure as configure_star_modes
                runtime.write_text(configure_star_modes(runtime.read_text(), default_profile=starfield_profile or 'full'))
        from .hors_v3_hud import configure as configure_hud
        runtime.write_text(configure_hud(runtime.read_text(),effects=effects,visible=hud_visible,toggle=allow_hud_toggle,internal=interactive))
        if interactive:
            from .hors_v3_exhibition import configure as configure_exhibition
            runtime.write_text(configure_exhibition(runtime.read_text(), mode_frames=mode_frames,
                variants=presentation_variants, stars=stars_included,enabled=exhibition_default=="enabled",order=exhibition_order,interval=exhibition_interval))
        from .hors_v3_intro import configure as configure_intro
        from . import __version__
        boot = stage / 'c64/cart' / ('easyflash-stream-v10-boot.asm' if kwargs.get('legacy_cart') else 'easyflash-object-boot.asm')
        intro_runtime, intro_boot = configure_intro(runtime.read_text(), boot.read_text(),
                                                    version=__version__, interactive=interactive)
        runtime.write_text(intro_runtime)
        boot.write_text(intro_boot)
        old_pack = cartstream.pack_frames
        old_directory = cartstream.emit_directory
        def pack(items, colors=True, **options):
            options['encoder'] = plan_encoder
            return old_pack(items, colors, **options)
        cartstream.pack_frames = pack
        if effects:
            cartstream.emit_directory = lambda path, directory, **options: reclaim_tables(path, directory, old_directory, **options)
        try:
            kwargs['renderer'] = 'yunroll-cart-v10'
            crt, manifest = v2._object_assembler(stage, frames, mesh, **kwargs)
        finally:
            cartstream.pack_frames = old_pack
            cartstream.emit_directory = old_directory
        v2.save_builds(stage, root)
    v2.describe(manifest, draw_gap, batch_budget)
    manifest.update(renderer=NAME, experimental=False,
        implementation='HORS-V2 literal drawing with HORS-V3 shared colour plan',
        color_policy=policy, wire_format='hors-v3-color-indexed4-v1' if palette is not None else 'hors-v3-color-literals-v1' if literal else 'hors-v3-complete-color-runs-v1',
        runtime_work=f"build/{kwargs['stem']}-stream-v10")
    if 'build_screen' in manifest:
        manifest['build_screen']['renderer'] = NAME
    from .hors_v3_intro import describe as describe_intro
    describe_intro(manifest, __version__, interactive=interactive)
    if interactive:
        from .hors_v3_controls import describe
        describe(manifest)
        from .hors_v3_speed import describe as describe_speed
        describe_speed(manifest, mode_frames or len(frames))
        from .hors_v3_help import describe as describe_help
        describe_help(manifest, __version__, effects=stars_included, modes=bool(mode_frames),variants=presentation_variants,hud=allow_hud_toggle,interval=exhibition_interval)
    from .hors_v3_hud import describe as describe_hud
    describe_hud(manifest,visible=hud_visible,toggle=allow_hud_toggle)
    if effects:
        from .hors_v3_effects import describe as describe_effects
        describe_effects(manifest, starfield=background_effect!='none', mode_frames=mode_frames, include_starfield=stars_included,variants=presentation_variants)
        if stars_included and occlusion_bounds is not None:
            manifest['background_effect']['opaque_bounds']=occlusion_bounds
            manifest['background_effect']['opaque_bounds_ram']=[0x8800,0x8c00]
            manifest['background_effect']['relocated_paths_ram']=[0x8c00,0x9000]
            manifest['background_effect']['opaque_occlusion']='conservative per-picture painted bounds; hides stars behind black paint and card interiors'
    else:
        manifest['background_effect'] = dict(name='none',included=False,extra_reserved_RAM_bytes=0)
    if interactive and stars_included:
        from .hors_v3_density import describe as describe_density
        describe_density(manifest)
        from .hors_v3_star_modes import describe as describe_star_modes
        describe_star_modes(manifest, default_profile=starfield_profile or 'full')
    if interactive:
        from .hors_v3_exhibition import describe as describe_exhibition
        describe_exhibition(manifest,mode_frames=mode_frames,variants=presentation_variants,enabled=exhibition_default=="enabled",order=exhibition_order,interval=exhibition_interval)
    # The independent oracle stays the pre-optimisation picture set.
    from dataclasses import asdict
    (root / manifest['runtime_work'] / 'oracle.json').write_text(json.dumps([asdict(f) for f in original]))
    (Path(kwargs['outdir']) / (kwargs['stem'] + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    return crt, manifest


def _optimize_wire_frames(frames, base):
    from .optimize import optimize_frames
    from .runjoin import join_frames
    from .clearplan import selective_clear_frames
    frames, _ = optimize_frames(frames, base)
    frames, _ = join_frames(frames)
    return selective_clear_frames(frames)[0]


@contextmanager
def scene_identity():
    """Label the existing scene intro with the selected public renderer."""
    from . import cartintro
    old = cartintro.emit_intro
    def emit(*args, **kwargs):
        identity = kwargs.get('build_identity')
        if identity:
            kwargs['build_identity'] = (identity[0], NAME + (' (ram)' if '(ram)' in identity[1] else ''))
        return old(*args, **kwargs)
    cartintro.emit_intro = emit
    try:
        yield
    finally:
        cartintro.emit_intro = old


def assemble_scene(root, frames, scene, *, draw_gap=6, batch_budget=2048,
                   color_encoding='literal', **kwargs):
    """V3 colour plans with the existing paced, paged authored-scene player."""
    from . import cartscene
    from dataclasses import asdict
    original = frames
    base = (kwargs.get('color_index', 1) << 4) | kwargs.get('background_color', 0)
    frames = _optimize_wire_frames(frames, base)
    frames, encode, policy, literal, runs, palette = encoding_plan(
        frames, kwargs.get('colors', True), base, draw_gap, batch_budget, color_encoding)
    with v2.staged(root, scene=True) as stage, scene_identity():
        runtime = stage / 'c64/renderer-yunroll-cart-v10-scene.asm'
        if kwargs.get('colors', True):
            runtime.write_text(patch_literal_runtime(runtime.read_text(), runs, palette)
                               if literal else patch_runtime(runtime.read_text()))
        old_pack = cartscene.pack_scene_frames
        def pack(items, colors=True, **options):
            options.update(encoder=encode, direct_bytes=True)
            return old_pack(items, colors, **options)
        cartscene.pack_scene_frames = pack
        try:
            kwargs.update(renderer='yunroll-cart-v10-scene', optimize=False)
            crt, manifest = cartscene.assemble_scene(stage, frames, scene, **kwargs)
        finally:
            cartscene.pack_scene_frames = old_pack
        v2.save_builds(stage, root)
    v2.describe(manifest, draw_gap, batch_budget)
    manifest.update(renderer=NAME, color_policy=policy,
        implementation='HORS-V3 colour plan with paced authored-scene playback',
        wire_format='hors-v3-color-indexed4-v1' if palette is not None else 'hors-v3-color-literals-v1' if literal else 'hors-v3-complete-color-runs-v1',
        runtime_work=f"build/{kwargs['stem']}-stream-scene")
    if kwargs.get('intro'):
        from . import __version__
        manifest['build_screen'] = dict(version=__version__, renderer=NAME,
            ticks=None, skip_key='SPACE', wait_for_space=True)
    (Path(root) / manifest['runtime_work'] / 'oracle.json').write_text(json.dumps([asdict(f) for f in original]))
    (Path(kwargs['outdir']) / (kwargs['stem'] + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    return crt, manifest


def cmd_build(a):
    from . import cli, cartstream
    if a.interactive_cart:
        if a.blend or a.scene or a.animation not in (None, 'spin'):
            raise ValueError('--interactive-cart requires a standalone spin; authored scenes are unsupported')
        if a.output and Path(a.output).suffix:
            if Path(a.output).suffix.lower() != '.crt':
                raise ValueError('--interactive-cart output must be a .crt file or an extensionless basename')
            a.output = a.output[:-4]
    if a.surface_fill != 'none' or a.interactive_cart or getattr(a, 'background_effect', 'none') != 'none' or (not getattr(a,'hud_visible',True) and not (a.blend or a.scene)):
        from .surface_fill import cmd_build as build_surface
        return build_surface(a)
    if a.surface_palette != 'grey' or a.surface_ramp is not None:
        raise ValueError('--surface-palette/--surface-ramp require --surface-fill metallic')
    a.public_renderer = NAME
    if a.output and a.output.endswith('.crt'):
        a.output = a.output[:-4]
    if a.blend or a.scene:
        from .cartscene import cmd_build_cart_scene
        a.renderer = 'yunroll-cart-v10-scene'
        return cmd_build_cart_scene(a)
    if a.blender_output_fps is not None:
        raise ValueError('--blender-output-fps requires --blend')
    if a.no_assemble:
        from .surface_fill import cmd_build as build_surface
        return build_surface(a)
    a.renderer = 'yunroll-cart-v10'
    with v2._lock:
        old = cartstream.assemble_cartridge
        def build(root, frames, mesh, **kwargs):
            base = (kwargs.get('color_index', 1) << 4) | kwargs.get('background_color', 0)
            frames = _optimize_wire_frames(frames, base)
            return assemble_cartridge(root, frames, mesh, draw_gap=a.v2_draw_gap,
                batch_budget=a.v2_batch_budget, color_encoding=a.v3_color_encoding, **kwargs)
        cartstream.assemble_cartridge = build
        try:
            return cartstream.cmd_build_cart_v2(a)
        finally:
            cartstream.assemble_cartridge = old
