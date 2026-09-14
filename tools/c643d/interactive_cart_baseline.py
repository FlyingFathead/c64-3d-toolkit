"""Reusable interactive-cart baseline derived from the released SAKU 2026 cart.

Compose the preserved SAKU controls, effects, HUD, help and exhibition modules
in one place. GMod3 builders opt in here; the existing EasyFlash path is intact.
Stars are included but OFF unless a caller explicitly requests them.
"""
from . import hors_v3_controls as ctrl, hors_v3_speed as sp, hors_v3_help as hp
from . import hors_v3_hud as ui, hors_v3_exhibition as ex, hors_v3_intro as intro
from . import hors_v3_effects as fx, hors_v3_density as sd, hors_v3_star_modes as sl
from .hors_v3_occlusion import configure as opaque
from .demo_colors import once
from .emit import bytes_lines


def configure_runtime(source, *, version, interactive=True, palette=None, base=0, samples=48,
        effects=True, include_starfield=True, background_effect='none',
        mode_frames=0, presentation_variants=(), occlusion_bounds=None,
        starfield_profile='light', hud_visible=True, toggle=True,
        exhibition_default='disabled', exhibition_order='sequential', exhibition_interval=5):
    if interactive:
        source = ctrl.configure(source, palette=palette)
        source = source.replace("v3_background: .byte 0", f"v3_background: .byte {base&15}", 1)
    if effects:
        source = fx.configure(source, starfield=background_effect!='none', interactive=interactive,
            mode_frames=mode_frames, include_starfield=include_starfield, variants=presentation_variants)
    if interactive:
        source = sp.configure(source, samples=samples)
        source = hp.configure(source, version=version, effects=effects, modes=bool(mode_frames),
            stars=include_starfield, variants=presentation_variants, hud=toggle, interval=exhibition_interval)
        if include_starfield:
            if occlusion_bounds is not None:
                source = opaque(source, occlusion_bounds)
            source = sd.configure(source, opaque=occlusion_bounds is not None)
            source = sl.configure(source, default_profile=starfield_profile or 'light')
    source = ui.configure(source, effects=effects, visible=hud_visible, toggle=toggle, internal=interactive)
    if interactive:
        source = ex.configure(source, mode_frames=mode_frames, variants=presentation_variants,
            stars=include_starfield, enabled=exhibition_default=='enabled', order=exhibition_order, interval=exhibition_interval)
    return source


def describe_runtime(manifest, *, version, interactive=True, palette=None, base=0, samples=48,
        effects=True, include_starfield=True, background_effect='none',
        mode_frames=0, presentation_variants=(), occlusion_bounds=None,
        starfield_profile='light', hud_visible=True, toggle=True,
        exhibition_default='disabled', exhibition_order='sequential', exhibition_interval=5):
    if interactive:
        ctrl.describe(manifest)
        sp.describe(manifest, samples)
        hp.describe(manifest, version, effects=effects, modes=bool(mode_frames),
            variants=presentation_variants, hud=toggle, interval=exhibition_interval)
        ex.describe(manifest, mode_frames=mode_frames, variants=presentation_variants,
            enabled=exhibition_default=='enabled', order=exhibition_order, interval=exhibition_interval)
    ui.describe(manifest, visible=hud_visible, toggle=toggle)
    if effects:
        fx.describe(manifest, starfield=background_effect!='none', mode_frames=mode_frames,
            include_starfield=include_starfield, variants=presentation_variants)
        if occlusion_bounds is not None:
            manifest['background_effect']['opaque_bounds'] = occlusion_bounds
        if interactive and include_starfield:
            sd.describe(manifest)
            sl.describe(manifest, default_profile=starfield_profile or 'light')
    else:
        manifest['background_effect'] = dict(name='none', included=False, extra_reserved_RAM_bytes=0)


def collection_help_pages(*, modes=False):
    """Complete baseline controls; HUD and effects are visible on the first page."""
    pages = [[
        'Demo Cart v3.1             1/2 >',
        'HUD, stars and playback',
        'SHIFT+I  name and V/E on/off',
        'SHIFT+F  FPS/speed text on/off',
        'SHIFT+U  ALL HUD text on/off',
        'SHIFT+S  stars on/off (start OFF)',
        '1/2/3    stars reset/more/less',
        '4        light/full stars',
        '+ / - / 0  faster/slower/reset speed',
        'CURSOR / JOY1/2 L/R  direction',
        'F2       reset; stars OFF',
        'STOP/F1  collection menu',
        'N / P    next/previous demo',
        'C        next Dragon shade/wire',
        'SHIFT+H  open/close help',
        'SPACE    close help',
        'RIGHT: more controls',
    ], [
        'Demo Cart v3.1             2/2 <',
        'Colours and presentations',
        'F3       foreground/source palette',
        'F4       next background colour',
        'F5       background cycle on/off',
        'F6/F7    slower/faster cycle',
        'F8       border black/follow',
        'CTRL+F7  next border colour',
        '5        exhibition on/off',
        '6        ordered/random styles',
        '7/8      interval -/+5s (5..60s)',
        'Exhibition enters with HUD/stars OFF.',
    ]]
    if modes:
        pages[1] += ['SAKU ONLY:',
            'SHIFT+T/W solid white, stars OFF',
            'SHIFT+G  gradient black, stars ON',
            'SHIFT+R  spin/crawl',
            'SHIFT+B  white card/gradient',
            'SHIFT+O  outline/gradient']
    pages[1] += ['F2/4/6/8 = SHIFT + F1/3/5/7',
                 'LEFT: HUD/effects. STOP/F1: menu']
    if any(len(page)>25 or any(len(line)>40 for line in page) for page in pages):
        raise ValueError('Collection help exceeds 40x25')
    hp.packed_help(pages)  # Enforce the shared 1 KiB help store.
    return pages


def configure_collection_help(source, *, modes=False):
    packed, offsets = hp.packed_help(collection_help_pages(modes=modes))
    first=source.index('hp_packed:\n')+len('hp_packed:\n')
    last=source.index('.if * > $c400',first)
    return source[:first]+'\n'.join(bytes_lines(packed))+f'\nhp_page_lo: .byte <hp_packed,<({offsets[1]}+hp_packed)\nhp_page_hi: .byte >hp_packed,>({offsets[1]}+hp_packed)\n'+source[last:]


def configure_collection_exit(source):
    """Resident collection services give STOP priority, including held speed keys.

    The IRQ latches short STOP presses. Foreground dispatch performs the actual
    menu reload. Equal-size JSR substitutions leave all renderer addresses intact.
    """
    source=source.replace('        jsr sp_poll\n','        jsr $a640\n')
    source=once(source,'        jsr sp_tick\n','        jsr $a680\n')
    source=once(source,'hp_exit_key:\n','''hp_exit_key:
        lda #$fe
        sta $dc00
        lda $dc01
        and #$10
        bne collection_help_not_f1
        jsr v3_shift
        bne collection_help_not_f1
        jmp $a600
collection_help_not_f1:
''')
    # Fixed resident service calls are verified against every assembled entry.
    return source+'\n.if sp_poll != $9000 || sp_tick != $9094\n.error "Collection input service ABI changed"\n.endif\n'


def describe_collection(manifest, *, modes=False):
    keys=manifest['interactive_cart']['keys']
    keys.update({'RUN/STOP (Esc in VICE)':'return to collection menu, including help and slow playback',
        'F1':'return to collection menu', 'N':'next demo', 'P':'previous demo',
        'C':'next Dragon shade or wireframe',
        'Shift+H':'open/close help; closing startup help returns to the menu',
        'SPACE':'close help; start the selected demo from the menu',
        'RETURN (Enter)':'start the selected demo from the main menu',
        'Cursor left/right':'help page selection; playback direction',
        'Joystick 1/2 left/right':'playback direction',
        'F2':'reset presentation; stars OFF'})
    pages=collection_help_pages(modes=modes)
    help_info=manifest['interactive_cart']['help']
    help_info.update(lines=pages[0],pages=pages,startup='Shift+H on the collection menu; close returns to the same menu selection',
        navigation='left/right pages; STOP/F1 always returns to collection menu')
    manifest['interactive_baseline']=dict(name='saku-2026',version=1,
        module='tools/c643d/interactive_cart_baseline.py',starfield_default='disabled',
        exit='IRQ-latched RUN/STOP, serviced in foreground; help scans it directly')
    return keys
