"""Event-only HUD switches, sharing the speed module's reserved RAM."""
from .demo_colors import once


def configure(source, *, effects=False, visible=True, toggle=True, internal=False):
    if not toggle and not internal:
        if visible: return source
        source=once(source,'        jsr init_static_hud\n','')
        source=once(source,'        jsr init_fps_label\n','')
        source=once(source,'render_fps_digits:\n','render_fps_digits:\n        rts\n')
        if 'v3_draw_label:\n' in source:
            source=once(source,'v3_draw_label:\n','v3_draw_label:\n        rts\n')
        if 'sp_draw:\n' in source: source=once(source,'sp_draw:\n','sp_draw:\n        rts\n')
        return source
    # Rendering has no new per-frame visibility branch. A key event patches
    # the two drawing entry points to RTS and clears/restores all three slots.
    for marker in ('render_fps_digits:\n        lda fps_hundreds',
                   'sp_draw:\n        ldx render_slot',
                   'v3_draw_label:\n        ldx render_slot'):
        if source.count(marker)!=1:
            raise ValueError('HUD drawing entry changed: '+marker)
    source=once(source,'hp_shifted:\n','hp_shifted:\n        jsr ui_poll\n')
    if effects:
        source=once(source,'        beq fx_keys_released\n        jsr hp_shifted\n', '''        bne ui_shift_scan
        sta ui_held
        jmp fx_keys_released
ui_shift_scan:
        jsr hp_shifted
''')
    else:
        source=once(source,'hp_poll:\n        jsr v3_shift\n        beq hp_return\n', '''hp_poll:
        jsr v3_shift
        bne hp_shifted
        sta ui_held
        rts
''')
    if not visible:
        source=once(source,'        cli\n\nmain_loop:', '        jsr ui_boot\n        cli\n\nmain_loop:')
    code='''
.if sp_end > $9400
.error "Speed feedback overlaps HUD switch module"
.endif
* = $3400
.logical $9400
ui_boot:
        jsr ui_apply_info
        jsr ui_apply_perf
        jmp ui_apply_label
ui_poll:
        lda #$ef
        sta $dc00
        lda $dc01
ui_row4_read:
        and #2
        beq ui_key_info
        lda #$fb
        sta $dc00
        lda $dc01
ui_row2_read:
        and #$20
        beq ui_key_perf
        lda #$f7
        sta $dc00
        lda $dc01
ui_row3_read:
        and #$40
        beq ui_key_both
        lda #0
        sta ui_held
ui_return:
        rts
ui_key_info:
        lda ui_held
        bne ui_return
        inc ui_held
        php
        sei
        lda ui_info_visible
        eor #1
        sta ui_info_visible
        jsr ui_apply_info
        plp
        rts
ui_key_perf:
        lda ui_held
        bne ui_return
        inc ui_held
        php
        sei
        lda ui_perf_visible
        eor #1
        sta ui_perf_visible
        jsr ui_apply_perf
        plp
        rts
ui_key_both:
        lda ui_held
        bne ui_return
        inc ui_held
        php
        sei
        ; Hide all HUD text if any group is visible, otherwise restore all.
        lda ui_info_visible
        ora ui_perf_visible
        ora ui_label_visible
        eor #1
        sta ui_info_visible
        sta ui_perf_visible
        sta ui_label_visible
        jsr ui_apply_info
        jsr ui_apply_perf
        jsr ui_apply_label
        plp
ui_applied:
        rts
ui_apply_info:
        lda ui_info_visible
        beq ui_clear_info
        jmp init_static_hud
ui_clear_info:
        lda #0
        ldx #0
ui_info_loop:
        sta $3e00,x
        sta $7e00,x
        sta $fe00,x
        inx
        cpx #HUD_STATIC_LEN
        bne ui_info_loop
        rts
ui_apply_perf:
        lda ui_perf_visible
        beq ui_hide_perf
        lda #$ad
        sta render_fps_digits
        lda #$ae
        sta sp_draw
        jsr init_fps_label
        jsr render_fps_digits
        inc sp_revision
        rts
ui_hide_perf:
        lda #$60
        sta render_fps_digits
        sta sp_draw
        lda #0
        ldx #63
ui_fps_clear:
        sta $3f00,x
        sta $7f00,x
        sta $ff00,x
        dex
        bpl ui_fps_clear
        ldx #55
ui_message_clear:
        sta $3dc0,x
        sta $7dc0,x
        sta $fdc0,x
        dex
        bpl ui_message_clear
        rts
ui_apply_label:
        lda ui_label_visible
        beq ui_hide_label
        lda #$ae
        sta v3_draw_label
        ldx #87
ui_label_restore:
        lda v3_label_bitmap,x
        sta $20e8,x
        sta $60e8,x
        sta $e0e8,x
        dex
        bpl ui_label_restore
        rts
ui_hide_label:
        lda #$60
        sta v3_draw_label
        lda #0
        ldx #87
ui_label_clear:
        sta $20e8,x
        sta $60e8,x
        sta $e0e8,x
        dex
        bpl ui_label_clear
        rts
ui_info_visible: .byte 1
ui_perf_visible: .byte 1
ui_label_visible: .byte 1
ui_held: .byte 0
ui_end:
.if * > $9800
.error "HUD switches exceed shared speed RAM"
.endif
.here
'''
    if not toggle:
        a=code.index('ui_poll:');b=code.index('ui_apply_info:',a)
        code=code[:a]+code[b:]
        source=source.replace('        jsr ui_poll\n','').replace('        sta ui_held\n','')
    for group in ('info','perf','label'):
        code=code.replace(f'ui_{group}_visible: .byte 1',f'ui_{group}_visible: .byte {int(visible)}')
    return source+code


def describe(manifest, *, visible=True, toggle=True):
    if toggle: manifest['interactive_cart']['keys'].update({
        'Shift+I':'toggle bottom-left name and vertex/edge counts',
        'Shift+F':'toggle FPS and speed feedback; speed controls remain active',
        'Shift+U':'hide all HUD text, or show all when hidden (including INTERACTIVE)'})
    info=dict(initial_info=visible,initial_performance=visible,initial_label=visible,toggle_allowed=toggle,
        code_ram=[0x9400,0x9800],additional_reserved_RAM_bytes=0,
        implementation='key-event bitmap clear/restore across three slots; patch drawing entry points to RTS',
        idle='no added rendering branch; small release-latch update in existing unshifted input scan',
        model_viewport_unchanged=True,measurements_continue_while_hidden=True)
    if not toggle:
        info.update(code_ram=None,implementation='fixed initial HUD state; no switching code',idle='no toggle scanner')
    manifest['hud_visibility']=info
    if manifest.get('interactive_cart'):manifest['interactive_cart']['hud_visibility']=info
