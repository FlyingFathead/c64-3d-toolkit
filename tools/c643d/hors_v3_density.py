"""Adjust star points per sprite on key events; eight hardware motion paths."""
from .demo_colors import once
from .hors_v3_effects import STAR_PERIODS

LEVELS = (2, 4, 8, 16, 24, 32)
DEFAULT_LEVEL = 3
POINTS = ((0, 0), (13, 3), (5, 15), (21, 19))


def configure(source, *, opaque=False):
    # The existing 4 KiB copy loop has room for four more page-copy pairs.
    copies = ''.join(f'        lda ${0x2400+p*256:04x},x\n        sta ${0x9c00+p*256:04x},x\n' for p in range(4))
    source = once(source, 'sp_boot_copy_loop:\n', 'sp_boot_copy_loop:\n' + copies)
    source = once(source, '        jsr fx_init\n', '        jsr sd_init\n')
    source = once(source, '        ldx #7\nfx_star_loop:', 'sd_sprite_count:\n        ldx #7\nfx_star_loop:')
    source = once(source, '        sta fx_y\n', '        sta fx_y\n        jsr sd_visible\n        bcs fx_hidden\n        lda fx_y\n')
    source = once(source, '''        ldx #7
        lda #$fe
fx_pointer_loop:
fx_pointer_store:
        sta $07f8,x
        dex
        bpl fx_pointer_loop
''', '')
    source = once(source, '''        and #63
        sta fx_phase,x
        tay
''', '''        cmp sd_periods,x
        bcc sd_phase_ready
        lda #0
sd_phase_ready:
        sta fx_phase,x
        cmp sd_near_phase,x
        lda #0
        rol a
        sta sd_wide
        lda #$fe
        sec
        sbc sd_wide
fx_pointer_store:
        sta $07f8,x
        lda fx_phase,x
        tay
''')
    # Run inside the existing speed poll, including its slow-playback waits.
    # Reuse its release latch; plain number keys avoid host Shift translation.
    source = once(source, '        lda #0\n        sta sp_held\n',
                  '        jmp sd_poll\nsp_keys_released:\n        lda #0\n        sta sp_held\n')
    source = once(source, 'v3_reset:\n', 'v3_reset:\n        jsr sd_default\n')
    code = '''
* = $2400
.logical $9c00
sd_poll:
        lda #$7f
        sta $dc00
        lda $dc01
sd_row7_read:
        sta sd_row
        and #$80
        bne sd_stop_released
        jsr hp_open
        jmp sp_keys_released
sd_stop_released:
        lda sd_row
        and #1
        beq sd_reset
        lda sd_row
        and #8
        beq sd_more
        lda #$fd
        sta $dc00
        lda $dc01
sd_row1_read:
        and #1
        beq sd_less
        jmp sp_keys_released
sd_init:
        jsr fx_init
sd_default:
        lda #3
        sta sd_level
        jmp sd_apply
sd_more:
        lda sp_held
        bne sd_key_done
        lda sd_level
        cmp #5
        beq sd_key_done
        inc sd_level
        bne sd_changed
sd_less:
        lda sp_held
        bne sd_key_done
        lda sd_level
        beq sd_key_done
        dec sd_level
        jmp sd_changed
sd_reset:
        lda sp_held
        bne sd_key_done
        lda #3
        sta sd_level
sd_changed:
        php
        sei
        jsr sd_apply
        plp
sd_key_done:
        lda #1
        sta sp_held
        jmp sp_poll_done
sd_apply:
        lda #0
        ldy #62
sd_clear:
        sta $3f80,y
        sta $7f80,y
        sta $ff80,y
        sta $3f40,y
        sta $7f40,y
        sta $ff40,y
        dey
        bpl sd_clear
        ldy sd_level
        lda sd_sprites,y
        sta sd_sprite_count+1
        lda sd_points,y
        sta sd_dot_count
        tay
        dey
sd_point:
        lda sd_offsets,y
        tax
        lda sd_bits,y
        sta $3f80,x
        sta $7f80,x
        sta $ff80,x
        lsr a
        ora sd_bits,y
        sta $3f40,x
        sta $7f40,x
        sta $ff40,x
        dey
        bpl sd_point
        rts
; The original point still uses the established cell and opaque-box tests.
; Extra points suppress the entire group if any could touch opaque paint,
; a non-background low-nibble cell, or the model viewport boundary.
sd_visible:
        lda sd_dot_count
        cmp #2
        bcs sd_extra
        lda sd_wide
        bne sd_extra
        clc
        rts
sd_extra:
        lda fx_x
        sta sd_base_x
        lda fx_y
        sta sd_base_y
        ldy sd_dot_count
        dey
sd_check:
        sty sd_point_index
        lda sd_base_x
        clc
        adc sd_dx,y
        bcs sd_blocked
        sta fx_x
        lda sd_base_y
        clc
        adc sd_dy,y
        cmp #192
        bcs sd_blocked
        sta fx_y
        jsr sd_test_pixel
        bcs sd_blocked
        lda sd_wide
        beq sd_next_point
SD_WIDE_MASK
        ; Inside one colour cell, VIC priority masks both bitmap pixels.
        ; Only a cell boundary (or an opaque box) needs another test.
        lda fx_x
        and #7
        cmp #7
        bne sd_next_point
sd_right_pixel:
        inc fx_x
        beq sd_blocked
        jsr sd_test_pixel
        bcs sd_blocked
sd_next_point:
        ldy sd_point_index
        dey
        bmi sd_visible_done
        bne sd_check
        lda sd_wide
        bne sd_check
        ; The existing main star loop checks the first distant pixel.
sd_visible_done:
        clc
        bcc sd_restore
sd_blocked:
        sec
sd_restore:
        lda sd_base_x
        sta fx_x
        lda sd_base_y
        sta fx_y
        rts
sd_test_pixel:
'''
    if opaque:
        code += '''        lda fx_box_enabled+1
        beq sd_no_box
        jsr fx_box_test
        bcs sd_test_blocked
sd_no_box:
'''
    code += '''        lda fx_y
        lsr a
        lsr a
        lsr a
        tay
        lda fx_row_lo,y
        sta $f8
        lda fx_row_hi,y
        clc
        adc fx_screen_base
        sta $f9
        lda fx_x
        lsr a
        lsr a
        lsr a
        tay
        lda ($f8),y
        and #15
        cmp fx_background
        bne sd_test_blocked
        clc
        rts
sd_test_blocked:
        sec
        rts
sd_level: .byte 3
sd_row: .byte 0
sd_wide: .byte 0
sd_dot_count: .byte 2
sd_base_x: .byte 0
sd_base_y: .byte 0
sd_point_index: .byte 0
sd_sprites: .byte 1,3,7,7,7,7
sd_points: .byte 1,1,1,2,3,4
sd_dx: .byte 0,13,5,21
sd_dy: .byte 0,3,15,19
sd_offsets: .byte 0,10,45,59
sd_bits: .byte $80,$04,$04,$04
sd_periods: .byte PERIODS
sd_near_phase: .byte NEAR_PHASE
sd_end:
.if * > $a000
.error "Star density controls overlap frame staging RAM"
.endif
.here
'''
    code = code.replace('SD_WIDE_MASK', '        lda fx_box_enabled+1\n        bne sd_right_pixel' if opaque else '')
    code = code.replace('PERIODS', ','.join(map(str, STAR_PERIODS))).replace('NEAR_PHASE', ','.join(str(p*3//4) for p in STAR_PERIODS))
    return source + code


def describe(manifest):
    manifest['background_effect']['density'] = dict(default=16, levels=list(LEVELS),
        hardware_sprites=8, point_offsets=list(POINTS),
        trajectory_periods=list(STAR_PERIODS), near_star_width=2,
        near_sprite_ram=[0x3f40,0x7f40,0xff40], additional_sprite_RAM_bytes=192,
        motion='Points share up to eight sprite trajectories; denser settings form small groups.',
        masking='The whole sprite group is suppressed if an extra point crosses opaque paint, a filled colour cell or the viewport edge.',
        code_ram=[0x9c00, 0xa000], boot_staging=[0x2400, 0x2800])
    manifest['interactive_cart']['keys'].update({'1': 'reset starfield density to 16',
        '2': 'increase starfield density', '3': 'decrease starfield density'})
