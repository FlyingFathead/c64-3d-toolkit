"""Reproducible monochrome palette showcase using classic geometry samples."""
from dataclasses import replace
from pathlib import Path
from .colors import c64_color_index, hires_screen_byte
from .cartframes import load_menu_reference
from .font import bitmap_text

# Foreground and background names use the same parser as user-facing controls.
COMBOS = (
    ('TORUS', 'TORUS BLACK ON WHITE', 'black', 'white'),
    ('TORUS DENSE', 'DENSE TORUS CYAN ON BLUE', 'cyan', 'blue'),
    ('SPHERE', 'SPHERE LIGHT GREEN ON BLACK', 'light_green', 'black'),
    ('CUBE', 'CUBE WHITE ON PURPLE', 'white', 'purple'),
)


def combo_sources(root):
    reference={demo.name:demo for demo in load_menu_reference(root)}
    result=[]
    for source,title,foreground,background in COMBOS:
        original=reference[source]
        fg,bg=c64_color_index(foreground),c64_color_index(background)
        # Keep every visible vector and authored orientation. Replace only the
        # source colour metadata; a monochrome frame needs no per-cell spans.
        frames=[replace(frame,color_spans=[],color_palette=(),color_cells=0,color_conflicts=0) for frame in original.frames]
        result.append(replace(original,name=title,frames=frames,colors=False,
            screen=hires_screen_byte(fg,bg),border=bg,interactive_colors=True,
            hud=bytes(bitmap_text(source+' F3:FG F4:BG',31))))
    return result


def configure_combo_menu(source):
    """Opt-in menu behavior; preserve all manual menu/skip/exit controls."""
    cold='    jmp menu_full_redraw\n\nruntime_return_menu:'
    wrap='    jsr play_all_thanks_start\n    bcc runtime_next_wrap'
    if source.count(cold)!=1 or source.count(wrap)!=1:
        raise ValueError('color-combo menu startup/wrap configuration sites changed')
    # selected_entry=$ff selects normal PLAY ALL and installs its normal timer.
    source=source.replace(cold,'    jmp menu_launch_nowait\n\nruntime_return_menu:',1)
    # After the final entry, restart without a ten-second thank-you intermission.
    return source.replace(wrap,'    clc\n    nop\n    nop\n    bcc runtime_next_wrap',1)


def configure_combo_runtime(source):
    """Add the tester-only keyboard hook in v2's unused tail of the v2 extension page."""
    marker='v3_entry_lo = $4f00 ; v2 direct-only'
    if marker not in source or source.count('frame_begin:\n')!=1:
        raise ValueError('interactive colours require the stable v2 direct-only runtime')
    source=source.replace('frame_begin:\n','frame_begin:\n        jsr combo_poll_keys\n',1)
    return source.replace(marker,marker+'''
* = $4f40
; Keep $4f00-$4f3f for the v2 span extension; use the remaining page tail.
.if hors_v2_extension_end > $4f40
.error "v2 span extension overlaps colour tester controls"
.endif
combo_screen_color: .byte SCREEN_COLOR
combo_key_latch: .byte 0
combo_poll_keys:
        php
        sei                         ; keep IRQ keyboard scans out of our row reads
        pha
        txa
        pha
        tya
        pha
        lda #$fe                    ; keyboard row 0, F3 = bit 5
        sta $dc00
        lda $dc01
combo_f3_read:
        and #$20
        beq combo_key_down
        lda #0
        sta combo_key_latch
        jmp combo_keys_done
combo_key_down:
        lda combo_key_latch
        bne combo_keys_done
        inc combo_key_latch
        lda #$fd                    ; left SHIFT, row 1 bit 7
        sta $dc00
        lda $dc01
combo_left_shift_read:
        and #$80
        beq combo_background
        lda #$bf                    ; right SHIFT, row 6 bit 4
        sta $dc00
        lda $dc01
combo_right_shift_read:
        and #$10
        beq combo_background
        lda combo_screen_color
        clc
        adc #$10                    ; wrap high nibble, preserve background
        jmp combo_apply_color
combo_background:
        lda combo_screen_color
        clc
        adc #1
        and #$0f
        tax
        lda combo_screen_color
        and #$f0
        sta combo_screen_color
        txa
        ora combo_screen_color
combo_apply_color:
        sta combo_screen_color
        lda #$ff
        sta $dc00
        cli                         ; main-loop hook; let raster IRQ run during fills
        lda combo_screen_color
        and #$0f
        sta $d020
        sta $d021
        lda combo_screen_color
        ldx #0
combo_fill_screens:
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        sta $4400,x
        sta $4500,x
        sta $4600,x
        sta $4700,x
        sta $c800,x
        sta $c900,x
        sta $ca00,x
        sta $cb00,x
        inx
        bne combo_fill_screens
combo_keys_done:
        lda #$ff
        sta $dc00
        pla
        tay
        pla
        tax
        pla
        plp
        rts
combo_controls_end:
.if * > $5000
.error "colour tester controls exceed the reclaimed v2 page"
.endif
''',1)


def cmd_color_combo_test(a):
    from . import cli,cartuniform
    a.color_combo_test=True
    a.stream_renderer='hors-render-v2'
    a.menu_style='default'
    a.output=a.output or 'color-combo-test'+('-legacy' if getattr(a,'legacy_cart',False) else '')
    a.output_dir=a.output_dir or str(cli.ROOT/'examples/color_combo_test')
    return cartuniform.build(a,sources=combo_sources(cli.ROOT))
