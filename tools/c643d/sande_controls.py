"""Opt-in standalone controls in private all-direct v2 assembly copies."""
from contextlib import contextmanager
from .demo_colors import configure_runtime, once


def configure(source, border=0, text_overlay=True):
    source = configure_runtime(source, border=border)
    # Only this private runtime links F4's background to the border.
    source = once(source, '        and #$0f\n        tax\n',
                  '        and #$0f\n        jsr sande_apply_border\n        tax\n')
    source = once(source, '        bne demo_color_done\n',
                  '        beq sande_manual_new_key\n        jmp demo_color_done\nsande_manual_new_key:\n')
    source = once(source, 'demo_color_reset:\n',
                  'demo_color_reset:\n        jsr sande_flash\n        jsr sande_cycle_reset\n')
    source = once(source, '        inc $d020              ; low nibble wraps; independent of bitmap\n        jmp demo_color_done',
                  '        jmp sande_faster')
    source = once(source, '        bne demo_color_reset\n',
                  '        beq sande_faster_key\n        jmp sande_toggle_border\nsande_faster_key:\n')
    if text_overlay:
        source = once(source, 'frame_draw_complete:\n',
                      '        jsr sande_draw_label\nframe_draw_complete:\n')
    source = once(source, 'frame_begin:\n', 'frame_begin:\n        jsr sande_cycle\n        jsr sande_poll\n')
    source = once(source, '        sta last_tick\n        sta display_slot',
                  '        sta last_tick\n        sta $02fb\n        sta display_slot')
    source = once(source, '''        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc frame_index_ok
        lda #0
        sta frame_index
frame_index_ok:
''', '''        jsr sande_advance
frame_index_ok:
''')
    marker = 'v3_entry_lo = $4f00 ; v2 direct-only'
    source = once(source, marker, marker + '''
* = $4f40
.if hors_v2_extension_end > $4f40
.error "v2 extension overlaps Sande controls"
.endif
sande_step: .byte 1
sande_poll:
        ; Both joystick ports are inputs while sampled. Ignore simultaneous
        ; opposite directions. Skip keyboard decoding while a joystick is
        ; active, avoiding the C64's shared CIA matrix ghost keys.
        lda #0
        sta $dc02
        sta $dc03
        lda $dc00
sande_joy2_read:
        and $dc01
sande_joy1_read:
        and #$1f
        cmp #$1f
        beq sande_keyboard
        and #$0c
        cmp #$0c
        beq sande_done
        cmp #0
        beq sande_done
        and #4
        beq sande_left
        bne sande_right
sande_keyboard:
        lda #$ff
        sta $dc02
        lda #$fe
        sta $dc00
        lda $dc01
sande_row0_read:
        tax
        and #$78
        cmp #$78
        beq sande_no_color
        jsr sande_color_dispatch
        jmp sande_done
sande_no_color:
        lda #0
        sta $02fb
        txa
        and #4                 ; C64 CRSR right; SHIFT+CRSR is left
        bne sande_done
        jsr demo_color_shift
        bne sande_left
sande_right:
        lda #1
        bne sande_set_direction
sande_left:
        lda #$ff
sande_set_direction:
        sta sande_step
sande_done:
        lda #$ff
        sta $dc00
        sta $dc02
        rts
sande_advance:
        lda sande_step
        bmi sande_reverse
        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc sande_advance_done
        lda #0
        sta frame_index
        rts
sande_reverse:
        lda frame_index
        bne sande_decrement
        lda #FRAME_COUNT
        sta frame_index
sande_decrement:
        dec frame_index
sande_advance_done:
        rts
sande_controls_end:
.if * > $5000
.error "Sande controls overlap metadata cache"
.endif
''')
    if text_overlay:
        source = once(source, 'sande_controls_end:\n', '''; Draw only into the producer's buffer, before publication. Repaint the
; same top-right 11 cells after geometry so overlapping spans cannot erase it.
sande_draw_label:
        ldx render_slot
        lda bitmap_base_hi,x
        sta sande_label_store+2
        ldx #87
sande_label_loop:
        lda sande_label_bitmap,x
sande_label_store:
        sta $20e8,x
        dex
        bpl sande_label_loop
        rts
sande_controls_end:
''')
    source += '''
; Private controls fit inside the existing bootstrap allocation. Check the
; real end of the Y/reuse kernel before using the otherwise unused tail.
.if v5_cold_end > $5e00
.error "Interactive controls overlap Y/reuse kernel"
.endif
* = $5e00
sande_cycle_enabled: .byte 0
sande_cycle_last: .byte 0
sande_cycle_phase: .byte 0
sande_cycle_other: .byte 0
sande_cycle_rate: .byte 2
sande_cycle_interval: .byte 50
sande_border_follow: .byte 1
sande_cycle:
        lda sande_cycle_enabled
        beq sande_cycle_done
        lda tick_counter
        sec
        sbc sande_cycle_last
        cmp sande_cycle_interval
        bcc sande_cycle_done
        lda tick_counter
        sta sande_cycle_last
        lda sande_cycle_phase
        eor #1
        sta sande_cycle_phase
        bne sande_cycle_foreground
        lda demo_color_screen
        and #$f0
        sta sande_cycle_other
        lda demo_color_screen
        tax
sande_cycle_bg_next:
        txa
        clc
        adc #1
        and #$0f
        tax
        asl a
        asl a
        asl a
        asl a
        cmp sande_cycle_other
        beq sande_cycle_bg_next
        sei
        txa
        jsr sande_apply_border
        ora sande_cycle_other
        jmp sande_cycle_commit
sande_cycle_foreground:
        lda demo_color_screen
        and #$0f
        sta sande_cycle_other
        lda demo_color_screen
        tax
sande_cycle_fg_next:
        txa
        clc
        adc #$10
        tax
        lsr a
        lsr a
        lsr a
        lsr a
        cmp sande_cycle_other
        beq sande_cycle_fg_next
        txa
sande_cycle_commit:
        ; Complete one palette event before the next display IRQ observes it.
        sei
        jsr demo_color_apply
        cli
sande_cycle_done:
        rts
sande_cycle_rates: .byte 200,100,50,25,12,6,3,1
sande_slower:
        ldx sande_cycle_rate
        beq sande_speed_done
        dex
        jmp sande_speed_set
sande_faster:
        lda #$7f
        sta $dc00
        lda $dc01
sande_ctrl_read:
        and #4
        beq sande_custom_border
        ldx sande_cycle_rate
        cpx #7
        beq sande_speed_done
        inx
sande_speed_set:
        stx sande_cycle_rate
        lda sande_cycle_rates,x
        sta sande_cycle_interval
        lda tick_counter
        sta sande_cycle_last
sande_speed_done:
        jmp demo_color_done
sande_cycle_reset:
        lda #0
        sta sande_cycle_enabled
        sta sande_cycle_phase
        lda #2
        sta sande_cycle_rate
        lda #50
        sta sande_cycle_interval
        lda #1
        sta sande_border_follow
        rts
sande_toggle_border:
        lda sande_border_follow
        cmp #1
        beq sande_lock_black
        lda #1
        bne sande_border_mode
sande_lock_black:
        lda #0
sande_border_mode:
        sta sande_border_follow
        lda demo_color_screen
        jsr sande_apply_border
        jmp demo_color_done
sande_custom_border:
        lda #2
        sta sande_border_follow
        inc $d020
        jmp demo_color_done
sande_apply_border:
        pha
        lda sande_border_follow
        cmp #1
        beq sande_border_background
        cmp #2
        beq sande_border_keep
        lda #0
        sta $d020
sande_border_keep:
        pla
        rts
sande_border_background:
        pla
        pha
        and #$0f
        sta $d020
        pla
        rts
sande_color_dispatch:
        txa
        and #$10
        beq sande_reset_key
        txa
        and #$40
        beq sande_cycle_key
        jmp demo_color_key
sande_reset_key:
        lda $02fb
        bne sande_dispatch_done
        inc $02fb
        jsr demo_color_shift
        beq sande_dispatch_done     ; F1 has no action; SHIFT+F1 is F2
        jmp demo_color_reset
sande_cycle_key:
        lda $02fb
        bne sande_dispatch_done
        inc $02fb
        jsr demo_color_shift
        beq sande_toggle
        jmp sande_slower            ; SHIFT+F5 is F6
sande_toggle:
        lda sande_cycle_enabled
        eor #1
        sta sande_cycle_enabled
        lda tick_counter
        sta sande_cycle_last
        lda #0
        sta sande_cycle_phase
sande_dispatch_done:
        rts
sande_flash:
        lda #1
        sta $d020
        lda #$11
        jsr demo_color_apply
        lda tick_counter
        sta sande_flash_tick
sande_flash_visible:
        lda tick_counter
        sec
        sbc sande_flash_tick
        cmp #5
        bcc sande_flash_visible
        rts
sande_flash_tick: .byte 0
'''
    if text_overlay:
        from .font import bitmap_text
        from .emit import bytes_lines
        source += 'sande_label_bitmap:\n' + '\n'.join(bytes_lines(bitmap_text('INTERACTIVE'))) + '\n'
    source += '''sande_extension_end:
.if * > $6000
.error "Interactive controls exceed bootstrap RAM"
.endif
'''
    return source


@contextmanager
def enabled(border=0, text_overlay=True):
    """Apply only to the separately named interactive build; no repo ASM edits."""
    from . import hors_v2_stable
    original = hors_v2_stable.staged

    @contextmanager
    def staged(root, *, scene=False):
        if scene:
            raise ValueError('Sande controls require standalone object frames')
        with original(root, scene=False) as stage:
            runtime = stage / 'c64/renderer-yunroll-cart-v10.asm'
            runtime.write_text(configure(runtime.read_text(), border, text_overlay))
            yield stage

    with hors_v2_stable._lock:
        hors_v2_stable.staged = staged
        try:
            yield
        finally:
            hors_v2_stable.staged = original
