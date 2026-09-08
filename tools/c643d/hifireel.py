"""Finite authored-scene presentation inside the independent HiFi reel."""

def configure_scene_runtime(src, demo):
    if not 1 <= demo.frame_ticks <= 255:
        raise ValueError('frame ticks must fit one byte')
    if not demo.show_hud:
        for call in ('init_static_hud','init_fps_label','maybe_update_fps'):
            src=src.replace('        jsr '+call, '        nop\n        nop\n        nop')
    if demo.frame_ticks != 1 or demo.finite:
        src=src.replace('        sta tick_counter', '        sta tick_counter\n        sta reel_hold',1)
        src=src.replace('        inc tick_counter', '        inc tick_counter\n        lda reel_hold\n        beq reel_check_ready\n        dec reel_hold\n        bne irq_no_flip\nreel_check_ready:',1)
        src=src.replace('        stx display_slot',f'        stx display_slot\n        lda #{demo.frame_ticks}\n        sta reel_hold',1)
        src=src.replace('display_slot:           .byte 0','display_slot:           .byte 0\nreel_hold: .byte 0')
        start=src.index('v5_hold_wait:');end=src.index('v5_reused: .byte',start)
        src=src[:start]+f'v5_hold_wait:\n        lda reel_hold\n        bne v5_hold_wait\n        jmp profile_publish_ready\nv5_hold_commit:\n        sei\n        lda #{demo.frame_ticks}\n        sta reel_hold\n        lda v5_saved_render\n        sta render_slot\n        cli\n        rts\n'+src[end:]
    if demo.finite:
        old='        bcc frame_index_ok\n        lda #0\n        sta frame_index'
        new='        bcc frame_index_ok\nreel_wait_last_visible:\n        ldx display_slot\n        lda slot_frame,x\n        cmp #FRAME_COUNT-1\n        bne reel_wait_last_visible\nreel_wait_final_hold:\n        lda reel_hold\n        bne reel_wait_final_hold\nreel_scene_complete:\n        jmp $0206\n'
        if old not in src:raise ValueError('scene completion integration point missing')
        src=src.replace(old,new,1)
    return src
