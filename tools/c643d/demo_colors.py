"""Event-only palette controls for stable-v2 demo carts.

Reuse the existing IRQ matrix scan. The no-key path adds CMP (2 cycles) and
removes AND (2 cycles) from the RUN/STOP test. No renderer-loop hook is used.
The handler replaces the unused high-byte vector-dispatch page; only the
all-direct stable-v2 menu integrations may enable it.
"""


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('demo colour integration site changed: '+old[:70])
    return text.replace(old, new, 1)


def configure_control_source(source):
    source=once(source, '    and #$10\n    beq control_menu_key',
        'control_row0_read:\n    and #$38\n    cmp #$38\n    bne control_row0_key')
    source=once(source, '    txa\n    and #$80\n    beq control_menu_key',
        '    txa\n    bpl control_menu_key')
    source=once(source, '    jsr $c700', 'control_timer:\n    jsr $c700')
    return once(source, 'control_menu_key:\n', '''control_row0_key:
    and #$10
    beq control_menu_key
    jsr $4300                  ; event-only handler; A/X/Y already saved
    jmp control_timer          ; colour keys do not pause PLAY ALL

control_menu_key:
''')


def configure_runtime(source, border=0):
    if 'v3_entry_lo = $4f00' not in source:
        raise ValueError('demo colour controls require an all-direct v2 runtime')
    start=source.index('* = $4300\nv3_entry_hi:')
    end=source.index('v3_entry_lo = $4f00', start)
    handler='''* = $4300
v3_entry_hi = $4300             ; dead vector-only dispatch, reused for controls
demo_color_key:
        lda $02fb
        bne demo_color_done
        inc $02fb
        lda #$fe
        sta $dc00
        lda $dc01
demo_color_row_read:
        and #$20
        beq demo_color_graphics
        jsr demo_color_shift
        bne demo_color_reset
        inc $d020              ; low nibble wraps; independent of bitmap
        jmp demo_color_done
demo_color_reset:
        lda #BORDER_PRESET
        sta $d020
.if COLORS_ENABLED == 0
        lda #SCREEN_COLOR
        jmp demo_color_apply
.else
        jmp demo_color_done
.endif
demo_color_graphics:
.if COLORS_ENABLED == 0
        jsr demo_color_shift
        bne demo_color_background
        lda demo_color_screen
        clc
        adc #$10
        jmp demo_color_apply
demo_color_background:
        lda demo_color_screen
        clc
        adc #1
        and #$0f
        tax
        lda demo_color_screen
        and #$f0
        sta demo_color_screen
        txa
        ora demo_color_screen
demo_color_apply:
        sta demo_color_screen
        and #$0f
        sta $d021
        lda demo_color_screen
        ldx #0
demo_color_fill:
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
        bne demo_color_fill
.endif
demo_color_done:
        lda #$ff
        sta $dc00
        rts
demo_color_shift:
        lda #$fd
        sta $dc00
        lda $dc01
demo_color_left_shift_read:
        and #$80
        beq demo_color_shift_yes
        lda #$bf
        sta $dc00
        lda $dc01
demo_color_right_shift_read:
        and #$10
        beq demo_color_shift_yes
        lda #0
        rts
demo_color_shift_yes:
        lda #1
        rts
demo_color_screen: .byte SCREEN_COLOR
demo_color_end:
.if * > $4400
.error "demo colour controls overlap screen RAM"
.endif
'''.replace('BORDER_PRESET',str(border))
    return source[:start]+handler+source[end:]


def metadata(monochrome):
    return dict(foreground_key='F3' if monochrome else None,
        background_key='F4 / SHIFT+F3' if monochrome else None,
        border_key='F7', reset_key='F8 / SHIFT+F7',
        border_follows_background=False, reset_on_entry=True,
        source_palette_preserved=True, idle_extra_cpu_cycles=0,
        handler_range='$4300-$43ff (unused direct-only vector table)')
