"""Small, shared exhibition scheduler; all animation data remains in cartridge ROM."""
from .demo_colors import once
from .font import bitmap_text
from .emit import bytes_lines


def loops(mode_frames, variants):
    if not mode_frames: return [('current loop', 0, 0)]
    result=[('solid',0,2),('gradient',1,3)]
    if 'outline' in variants:
        start=4+2*variants.index('outline');result[0]=('solid outline',start,start+1)
    for i,kind in enumerate(variants):
        if kind=='card': result.append(('white card',4+2*i,5+2*i))
    return result


def configure(source, *, mode_frames=0, variants=(), stars=False, enabled=False, order="sequential", interval=5):
    if order not in ('sequential','random') or interval not in range(5,61,5):
        raise ValueError('Exhibition needs sequential/random and an interval of 5..60 seconds in steps of 5')
    scenes=loops(mode_frames,variants);count=len(scenes)
    source=once(source,'sp_poll_return:\n        rts\n','sp_poll_return:\n        jmp ex_poll\n')
    source=once(source,'sp_tick_done:\n        rts\n','sp_tick_done:\nex_tick_gate:\n        rts\n        .word ex_tick\n')
    source=once(source,'v3_reset:\n','v3_reset:\n        jsr ex_reset\n')
    # Polling reuses the speed poll frequency, including slow-motion waits.
    # Inactive timer/service gates are the original RTS, patched only on events.
    code='''
.if ui_end > $9540
.error "HUD overlaps exhibition controls"
.endif
* = $3540
.logical $9540
ex_poll:
        lda #$fb
        sta $dc00
        lda $dc01
ex_row2_read:
        sta ex_row
        and #1
        beq ex_key_toggle
        lda ex_row
        and #8
        beq ex_key_order
        lda #$f7
        sta $dc00
        lda $dc01
ex_row3_read:
        sta ex_row
        and #1
        beq ex_key_less
        lda ex_row
        and #8
        beq ex_key_more
        lda #0
        sta ex_held
ex_poll_done:
        lda #$ff
        sta $dc00
ex_service_gate:
        rts
        .word ex_service
ex_key_toggle:
        lda ex_held
        bne ex_poll_done
        inc ex_held
        lda ex_enabled
        beq ex_start
        jsr ex_stop
        jmp ex_poll_done
ex_key_order:
        lda ex_held
        bne ex_poll_done
        inc ex_held
        lda ex_random
        eor #1
        sta ex_random
        jsr ex_restart
        jmp ex_poll_done
ex_key_less:
        lda ex_held
        bne ex_poll_done
        lda ex_interval
        cmp #5
        beq ex_poll_done
        sec
        sbc #5
        ldx #1
        bne ex_set_interval
ex_key_more:
        lda ex_held
        bne ex_poll_done
        lda ex_interval
        cmp #60
        beq ex_poll_done
        clc
        adc #5
        ldx #0
ex_set_interval:
        sta ex_interval
        stx ex_notice_kind
        inc ex_held
        jsr ex_restart
        jsr ex_notice
        jmp ex_poll_done
ex_start:
        php
        sei
        lda #1
        sta ex_enabled
'''
    for group in ('info','perf','label'):
        code+=f'        lda ui_{group}_visible\n        sta ex_saved_{group}\n        lda #0\n        sta ui_{group}_visible\n'
    code+='        jsr ui_boot\n'
    if stars:
        code+='''        lda fx_enabled
        sta ex_saved_stars
        lda #0
        sta fx_enabled
        sta fx_visible
        sta $d015
'''
    code+='''        lda tick_counter
        ora #1
        sta ex_rng
        jsr ex_restart
        jsr ex_gates
        plp
        jmp ex_poll_done
ex_stop:
        lda ex_enabled
        beq ex_stop_done
        php
        sei
        lda #0
        sta ex_enabled
        sta ex_pending
'''
    for group in ('info','perf','label'):
        code+=f'        lda ex_saved_{group}\n        sta ui_{group}_visible\n'
    code+='        jsr ui_boot\n'
    if stars: code+='        lda ex_saved_stars\n        sta fx_enabled\n        bne ex_restored_stars\n        sta $d015\n        sta fx_visible\nex_restored_stars:\n'
    code+='''        jsr ex_gates
        plp
ex_stop_done:
        rts
ex_restart:
        php
        sei
        lda #50
        sta ex_subsecond
        lda ex_interval
        sta ex_seconds
        lda #0
        sta ex_pending
        plp
        rts
ex_gates:
        lda ex_enabled
        ora ex_notice_ticks
        ora ex_notice_dirty
        beq ex_gates_off
        lda #$4c
        bne ex_gates_store
ex_gates_off:
        lda #$60
ex_gates_store:
        sta ex_tick_gate
        sta ex_service_gate
        rts
ex_tick:
        lda ex_notice_ticks
        beq ex_clock
        dec ex_notice_ticks
        bne ex_clock
        inc ex_notice_dirty
ex_clock:
        lda ex_enabled
        beq ex_tick_done
        dec ex_subsecond
        bne ex_tick_done
        lda #50
        sta ex_subsecond
        dec ex_seconds
        bne ex_tick_done
        lda ex_interval
        sta ex_seconds
        lda #1
        sta ex_pending
ex_tick_done:
        rts
ex_service:
        lda ex_notice_dirty
        beq ex_scene_check
        jsr ex_notice_clear
ex_scene_check:
        lda ex_pending
        beq ex_service_done
        lda #0
        sta ex_pending
        jsr ex_choose
ex_service_done:
        jmp ex_gates
ex_choose:
'''
    if mode_frames:
        # Identify the currently displayed style; preserve axis spin/crawl.
        code+='''        lda fx_mode
'''
        if variants: code+='        jsr fx_standard_motion\n'
        code+='''        and #2
        lsr a
        sta ex_motion
        lda fx_mode
        ldx #0
ex_identify:
        cmp ex_spin,x
        beq ex_identified
        cmp ex_crawl,x
        beq ex_identified
        inx
'''+f'        cpx #{count}\n'+'''        bcc ex_identify
        ldx #0
ex_identified:
        stx ex_current
        lda #1
        ldx ex_random
        beq ex_offset
        lda ex_rng
        lsr a
        bcc ex_rng_ready
        eor #$b8
ex_rng_ready:
        sta ex_rng
'''+f'''ex_modulo:
        cmp #{count-1}
        bcc ex_random_ready
        sbc #{count-1}
        bcs ex_modulo
ex_random_ready:
        clc
        adc #1
ex_offset:
        clc
        adc ex_current
        cmp #{count}
        bcc ex_index_ready
        sbc #{count}
ex_index_ready:
        tax
        lda ex_motion
        beq ex_spin_selected
        lda ex_crawl,x
        jmp ex_scene_selected
ex_spin_selected:
        lda ex_spin,x
ex_scene_selected:
        sta fx_mode
        lda #0
        sta fx_position
        sta fx_foreground
        sta v3_cycle_enabled
        sta v3_background
        jsr fx_set_frame
'''
        # Original solid source is white-backed, not a transparent black logo.
        if 'outline' not in variants:
            code+='''        lda fx_mode
        and #1
        bne ex_choose_done
        lda #1
        sta v3_background
ex_choose_done:
'''
    code+='''        rts
ex_reset:
        jsr ex_stop
        lda #0
        sta ex_notice_ticks
        jsr ex_notice_clear
        lda #EX_ORDER_DEFAULT
        sta ex_random
        lda #EX_INTERVAL_DEFAULT
        sta ex_interval
        jsr ex_restart
        jmp ex_gates
ex_enabled: .byte 0
ex_random: .byte 0
ex_interval: .byte 5
ex_seconds: .byte 5
ex_subsecond: .byte 50
ex_pending: .byte 0
ex_rng: .byte 1
ex_current: .byte 0
ex_motion: .byte 0
ex_held: .byte 0
ex_row: .byte 0
ex_saved_info: .byte 0
ex_saved_perf: .byte 0
ex_saved_label: .byte 0
ex_saved_stars: .byte 0
ex_notice_ticks: .byte 0
ex_notice_dirty: .byte 0
ex_notice_kind: .byte 0
'''
    code+='ex_spin: .byte '+','.join(str(s[1]) for s in scenes)+'\nex_crawl: .byte '+','.join(str(s[2]) for s in scenes)+'\n'
    code+='''ex_end:
.if * > $9800
.error "Exhibition controls overlap help code"
.endif
.here
* = hp_end-$6000
.logical hp_end
ex_notice:
        php
        sei
        lda #100
        sta ex_notice_ticks
        lda #1
        sta ex_notice_dirty
        ldx #239
ex_notice_copy:
        lda ex_notice_template,x
        sta $3cc0,x
        sta $7cc0,x
        sta $fcc0,x
        dex
        cpx #$ff
        bne ex_notice_copy
        lda ex_notice_kind
        beq ex_notice_digits
        ldx #15
ex_notice_de:
        lda ex_de,x
        sta $3d10,x
        sta $7d10,x
        sta $fd10,x
        dex
        bpl ex_notice_de
ex_notice_digits:
        lda ex_interval
        ldx #0
ex_tens:
        cmp #10
        bcc ex_decimal
        sbc #10
        inx
        bne ex_tens
ex_decimal:
        asl a
        asl a
        asl a
        tay
        txa
        asl a
        asl a
        asl a
        tax
        lda #8
        sta ex_digit_count
ex_digits:
        lda ex_digits_font,x
        sta $3d78
        sta $7d78
        sta $fd78
        lda ex_digits_font,y
        sta $3d80
        sta $7d80
        sta $fd80
        inx
        iny
'''
    # Advance all six digit store operands; reset them after each notification.
    # Self modifying stores avoid a spare zero-page pointer reservation.
    for name in ('t0','t1','t2','u0','u1','u2'):
        code+=f'        inc ex_{name}+1\n'
    code+='''        dec ex_digit_count
        bne ex_digits
        lda #$78
'''
    for name in ('t0','t1','t2'):code+=f'        sta ex_{name}+1\n'
    code+='        lda #$80\n'
    for name in ('u0','u1','u2'):code+=f'        sta ex_{name}+1\n'
    code+='''        lda #$10
        ldx #29
ex_notice_colors:
        sta $0798,x
        sta $4798,x
        sta $cb98,x
        dex
        bpl ex_notice_colors
        jsr ex_gates
        plp
        rts
ex_notice_clear:
        lda ex_notice_ticks
        bne ex_clear_done
        lda #0
        ldx #239
ex_clear_loop:
        sta $3cc0,x
        sta $7cc0,x
        sta $fcc0,x
        dex
        cpx #$ff
        bne ex_clear_loop
        sta ex_notice_dirty
        ldx #29
ex_clear_colors:
        lda v3_slot_background
        sta $0798,x
        lda v3_slot_background+1
        sta $4798,x
        lda v3_slot_background+2
        sta $cb98,x
        dex
        bpl ex_clear_colors
ex_clear_done:
        rts
ex_digit_count: .byte 0
ex_notice_template:
'''
    code+='\n'.join(bytes_lines(bitmap_text('AUTO TIME INCREASED TO 05 SECS')))+'\n'
    code+='''ex_notice_end:
.if * > $9c00
.error "Exhibition notification overlaps star density RAM"
.endif
.here
* = $3360
.logical $9360
.if sp_end > $9360
.error "Speed data overlaps notification digits"
.endif
ex_digits_font:
'''
    code+='\n'.join(bytes_lines(bitmap_text('0123456789')))+'\nex_de:\n'+'\n'.join(bytes_lines(bitmap_text('DE')))+'\n.here\n'
    for i,(addr,name) in enumerate(zip((0x3d78,0x7d78,0xfd78,0x3d80,0x7d80,0xfd80),('t0','t1','t2','u0','u1','u2'))):
        code=code.replace(f'        sta ${addr:04x}\n',f'ex_{name}:\n        sta ${addr:04x}\n',1)
    code=code.replace('ex_random: .byte 0',f'ex_random: .byte {int(order=="random")}').replace('ex_interval: .byte 5',f'ex_interval: .byte {interval}')
    if enabled:
        source=once(source,'        cli\n\nmain_loop:', '        jsr ex_start\n        cli\n\nmain_loop:')
    code=code.replace('EX_ORDER_DEFAULT',str(int(order=='random'))).replace('EX_INTERVAL_DEFAULT',str(interval))
    return source+code


def describe(manifest, *, mode_frames=0, variants=(), enabled=False, order="sequential", interval=5):
    manifest['interactive_cart']['keys'].update({'5':'exhibition on/off; hide HUD/stars on entry, restore previous on/off states on exit',
        '6':'exhibition order: sequential/random (no immediate repeats)', '7':'auto-change interval -5 seconds (minimum 5)',
        '8':'auto-change interval +5 seconds (maximum 60)'})
    manifest['interactive_cart']['exhibition']=dict(default_enabled=enabled,default_interval_seconds=interval,
        interval_seconds=[5,60],interval_step_seconds=5,default_order=order,
        loops=[dict(name=n,spin=s,crawl=c) for n,s,c in loops(mode_frames,variants)],
        clock='PAL raster clock; scene selection deferred to safe producer/input boundary; help pauses clock',
        stars='on/off defaults to off on entry; manual choices persist across scene switches; profile and density retained',
        hud='off on entry; previous visibility restored on exit',
        single_loop='continues the existing animation if only one loop was compiled',
        ram='reuses spare HUD/help RAM; 1 KiB additional packed help storage at $c000',
        new_animation_frames=0,random='8-bit LFSR, modulo selection excludes current style; not uniform cryptographic randomness')
