"""Private HORS-V3 controls: remap black only, preserving surface shades."""
from .demo_colors import once
from .font import bitmap_text
from .emit import bytes_lines


def configure(source, palette=None):
    source = once(source, 'frame_begin:\n', 'frame_begin:\n        jsr v3_poll\n        jsr v3_cycle\n        jsr v3_prepare_background\n')
    source = once(source, 'frame_draw_complete:\n',
                  '        jsr v3_draw_label\nframe_draw_complete:\n')
    source = once(source, 'irq_no_flip:\n', 'irq_no_flip:\n        jsr v3_display_colors\n')
    source = once(source, '''        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc frame_index_ok
        lda #0
        sta frame_index
frame_index_ok:
''', '''        jsr v3_advance
frame_index_ok:
''')
    # Preserve the fast direct copy when the original black background is used.
    mapped_copy = ''
    if 'v3_color_copy:\n        lda (STREAM_LO),y' in source:
        source = once(source, '''        ldy #0
v3_color_copy:
''', '''        ldy #0
        lda v3_background
        bne v3_color_mapped
v3_color_copy:
''')
        source = once(source, '        tya\n        clc\n        adc STREAM_LO\n',
                      'v3_color_copied:\n        tya\n        clc\n        adc STREAM_LO\n')
        mapped_copy = '''v3_color_mapped:
        stx v3_run_restore+1
v3_color_mapped_loop:
        lda (STREAM_LO),y
        tax
        lda v3_color_lut,x
        sta (PTR_LO),y
        iny
        cpy color_cells_temp
        bne v3_color_mapped_loop
v3_run_restore:
        ldx #0
        jmp v3_color_copied
'''
        # A distant branch would exceed the 6502 range: trampoline beside loop.
        source = once(source, '        bne v3_color_mapped\n',
                      '        beq v3_color_copy\n        jmp v3_color_mapped\n')
    elif 'acfc_span:' in source:
        source = once(source, '''        lda (STREAM_LO),y
        sta color_value_temp
''', '''        lda (STREAM_LO),y
        tax
        lda v3_color_lut,x
        sta color_value_temp
''')
    # Kernel helper owns $4f00..$4f19; its remaining page is private controls.
    source += '''
.if hors_v2_extension_end > $4f40
.error "HORS-V3 input controls overlap literal helper"
.endif
* = $4f40
v3_poll:
        lda #0
        sta $dc02
        sta $dc03
        lda $dc00
v3_joy2_read:
        and $dc01
v3_joy1_read:
        and #$1f
        cmp #$1f
        beq v3_keyboard
        and #$0c
        cmp #$0c
        beq v3_poll_done
        cmp #0
        beq v3_poll_done
        and #4
        beq v3_left
        bne v3_right
v3_keyboard:
        lda #$ff
        sta $dc02
        lda #$fe
        sta $dc00
        lda $dc01
v3_row0_read:
        sta v3_key_row
        and #$78
        cmp #$78
        beq v3_no_color_key
        lda v3_key_held
        bne v3_poll_done
        inc v3_key_held
        jsr v3_color_key
        jmp v3_poll_done
v3_no_color_key:
        lda #0
        sta v3_key_held
        lda v3_key_row
        and #4
        bne v3_poll_done
        jsr v3_shift
        bne v3_left
v3_right:
        lda #1
        bne v3_set_direction
v3_left:
        lda #$ff
v3_set_direction:
        sta v3_step
v3_poll_done:
        lda #$ff
        sta $dc00
        sta $dc02
v3_poll_return:
        rts
v3_shift:
        lda #$fd
        sta $dc00
        lda $dc01
v3_left_shift_read:
        and #$80
        beq v3_shift_yes
        lda #$bf
        sta $dc00
        lda $dc01
v3_right_shift_read:
        and #$10
        beq v3_shift_yes
        lda #0
        rts
v3_shift_yes:
        lda #1
        rts
v3_advance:
        lda v3_step
        bmi v3_reverse
        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc v3_advance_done
        lda #0
        sta frame_index
        rts
v3_reverse:
        lda frame_index
        bne v3_decrement
        lda #FRAME_COUNT
        sta frame_index
v3_decrement:
        dec frame_index
v3_advance_done:
        rts
v3_input_end:
.if * > $5000
.error "HORS-V3 input controls overlap metadata cache"
.endif

; Private tail of bootstrap image. $0200 lookup replaces black nibbles only;
; no KERNAL keyboard buffer is in use in this standalone runtime.
.if v5_cold_end > $5d20
.error "HORS-V3 controls overlap drawing kernel"
.endif
* = $5d20
v3_color_lut = $0200
v3_step: .byte 1
v3_key_row: .byte $ff
v3_key_held: .byte 0
v3_background: .byte 0
v3_slot_background: .byte 0,0,0
v3_slot_border: .byte 0,0,0
v3_border_mode: .byte 1
v3_custom_border: .byte 0
v3_cycle_enabled: .byte 0
v3_cycle_last: .byte 0
v3_cycle_rate: .byte 2
v3_cycle_interval: .byte 50
v3_flash_ticks: .byte 0
v3_lut_last: .byte $ff
v3_lut_high: .byte 0
v3_cycle_rates: .byte 200,100,50,25,12,6,3,1

v3_color_key:
        jsr v3_shift
        sta v3_shifted+1
        lda v3_key_row
        and #$10
        bne v3_not_f1
v3_shifted:
        lda #0
        beq v3_key_done
        jmp v3_reset
v3_not_f1:
        lda v3_key_row
        and #$20
        bne v3_not_f3
        lda v3_shifted+1
        beq v3_key_done
        jmp v3_next_background
v3_not_f3:
        lda v3_key_row
        and #$40
        bne v3_f7
        lda v3_shifted+1
        bne v3_slower
        lda v3_cycle_enabled
        eor #1
        sta v3_cycle_enabled
        jmp v3_restart_timer
v3_slower:
        ldx v3_cycle_rate
        beq v3_key_done
        dex
        jmp v3_set_rate
v3_f7:
        lda v3_shifted+1
        bne v3_toggle_border
        lda #$7f
        sta $dc00
        lda $dc01
v3_ctrl_read:
        and #4
        beq v3_custom
        ldx v3_cycle_rate
        cpx #7
        beq v3_key_done
        inx
v3_set_rate:
        stx v3_cycle_rate
        lda v3_cycle_rates,x
        sta v3_cycle_interval
v3_restart_timer:
        lda tick_counter
        sta v3_cycle_last
v3_key_done:
        rts
v3_toggle_border:
        lda v3_border_mode
        cmp #1
        beq v3_lock_black
        lda #1
        bne v3_set_border_mode
v3_lock_black:
        lda #0
v3_set_border_mode:
        sta v3_border_mode
        rts
v3_custom:
        lda $d020
        clc
        adc #1
        and #15
        sta v3_custom_border
        lda #2
        bne v3_set_border_mode
v3_reset:
        lda #0
        sta v3_background
        sta v3_cycle_enabled
        lda #1
        sta v3_border_mode
        lda #2
        sta v3_cycle_rate
        lda #50
        sta v3_cycle_interval
        lda #5
        sta v3_flash_ticks
        jmp v3_restart_timer
v3_next_background:
        inc v3_background
        lda v3_background
        and #15
        sta v3_background
        rts
v3_cycle:
        lda v3_cycle_enabled
        beq v3_cycle_done
        lda tick_counter
        sec
        sbc v3_cycle_last
        cmp v3_cycle_interval
        bcc v3_cycle_done
        lda tick_counter
        sta v3_cycle_last
        jmp v3_next_background
v3_cycle_done:
        rts

v3_prepare_background:
        lda v3_background
        cmp v3_lut_last
        beq v3_prepare_slot
        ldx v3_lut_last
        inx
        bne v3_lut_initialized
        pha
        ldx #0
v3_lut_init:
        txa
        sta v3_color_lut,x
        inx
        bne v3_lut_init
        pla
v3_lut_initialized:
        sta v3_lut_last
        asl a
        asl a
        asl a
        asl a
        sta v3_lut_high
        ; Only 31 of 256 colour pairs contain black. Update those entries,
        ; retaining the identity mapping of all other pairs permanently.
        ldx #0
v3_lut_low_black:
        txa
        ora v3_background
        sta v3_color_lut,x
        txa
        clc
        adc #16
        tax
        bne v3_lut_low_black
        ldx #15
v3_lut_high_black:
        txa
        ora v3_lut_high
        sta v3_color_lut,x
        dex
        bpl v3_lut_high_black
        lda v3_lut_high
        ora v3_background
        sta v3_color_lut
'''
    if palette:
        # Remap the small dictionary once per palette event, never per cell.
        for i, value in enumerate(palette):
            if (value & 15) == 0 or (value >> 4) == 0:
                source += f'        lda v3_color_lut+{value}\n        sta v3_color_palette+{i}\n'
    source += '''v3_prepare_slot:
        ldx render_slot
        lda v3_background
        ldy v3_border_mode
        cpy #1
        beq v3_border_chosen
        lda #0
        cpy #0
        beq v3_border_chosen
        lda v3_custom_border
v3_border_chosen:
        sta v3_slot_border,x
        lda v3_background
        cmp v3_slot_background,x
        beq v3_prepare_done
        sta v3_slot_background,x
        ; Only the producer buffer is reset. Absolute frame colours are
        ; restored immediately afterwards, including two-grey interior cells.
        lda v3_screen_hi,x
        sta v3_fill0+2
        clc
        adc #1
        sta v3_fill1+2
        adc #1
        sta v3_fill2+2
        adc #1
        sta v3_fill3+2
        lda v3_color_lut+SCREEN_COLOR
        ldx #0
v3_fill_loop:
v3_fill0:
        sta $0400,x
v3_fill1:
        sta $0500,x
v3_fill2:
        sta $0600,x
v3_fill3:
        sta $0700,x
        inx
        bne v3_fill_loop
v3_prepare_done:
        rts
v3_screen_hi: .byte $04,$44,$c8

; Run at the existing raster IRQ after its possible display flip. Metadata
; belongs to the displayed buffer, so the border never leads queued pictures.
v3_display_colors:
        lda v3_flash_ticks
        beq v3_display_normal
        dec v3_flash_ticks
        lda #1
        sta $d020
        sta $d021
        lda #$2b
        sta $d011
v3_flash_done:
        rts
v3_display_normal:
        lda #$3b
        sta $d011
        ldx display_slot
        lda v3_slot_border,x
        sta $d020
        lda v3_slot_background,x
        sta $d021
v3_display_colors_done:
        rts

v3_draw_label:
        ldx render_slot
        lda bitmap_base_hi,x
        sta v3_label_store+2
        ldx #87
v3_label_loop:
        lda v3_label_bitmap,x
v3_label_store:
        sta $20e8,x
        dex
        bpl v3_label_loop
        rts
'''
    source += mapped_copy
    source += 'v3_label_bitmap:\n' + '\n'.join(bytes_lines(bitmap_text('INTERACTIVE'))) + '\n'
    source += '''v3_controls_end:
.if * > $6000
.error "HORS-V3 controls exceed bootstrap RAM"
.endif
'''
    return source


def describe(manifest):
    manifest['interactive_cart'] = dict(
        rotation='cursor left/right and joystick ports 1/2 left/right',
        direction_persists=True, opposite_directions_ignored=True,
        source_surface_colors_preserved=True, uniform_palette_controls=False,
        background_override='replace original black nibbles only; nonblack surface colours are unchanged',
        keys={'F2':'white flash, reset black background, follow border, auto off, default rate',
              'F4':'next background colour', 'F5':'toggle automatic background cycling',
              'F6':'slower cycling', 'F7':'faster cycling',
              'F8':'toggle black border / follow background',
              'Ctrl+F7':'next independent border colour'},
        cycle_intervals_pal_ticks=[200,100,50,25,12,6,3,1], default_cycle_ticks=50,
        cycle_clock='PAL raster ticks; at most one event per produced sample',
        background_border_synchronized_to_display=True,
        polling='once per produced sample', extra_reserved_RAM_bytes=256,
        black_remap_RAM=[0x0200,0x0300])
    manifest['interactive_overlay'] = dict(
        text='INTERACTIVE', x=232, y=0, width=88, height=8, font='HUD 5x7')
