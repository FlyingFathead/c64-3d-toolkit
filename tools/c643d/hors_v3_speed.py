"""Shared V3 interactive tempo controls, copied into unused RAM before video init."""
from .demo_colors import once
from .emit import bytes_lines
from .font import bitmap_text


def levels(samples):
    cap=max(1,(samples-1)//2)
    skips=sorted(set(min(cap,n) for n in (1,2,3,4,6,8,12,16,24,32,48,64,96,127)))
    return [(1,8),(1,4),(1,2)]+[(n,1) for n in skips]


def configure(source,*,samples):
    rates=levels(samples);advance='fx_advance' if 'fx_advance:' in source else 'v3_advance'
    # $9000..$97ff is unused between ROML transfers. Transfer code disables IRQs
    # while ROM is mapped and never calls this module until RAM is visible.
    # Stage the module in bitmap RAM, copy it before clearing the bitmaps.
    copy=''
    for page in range(16):
        dest=0x9000+page*256 if page<12 else 0x8400+(page-12)*256
        copy+=f'        lda ${0x3000+page*256:04x},x\n        sta ${dest:04x},x\n'
    source=once(source,'        sei\n        cld\n','        sei\n        cld\n        jsr sp_boot_copy\n')
    source=once(source,'frame_begin:\n','frame_begin:\n        lda tick_counter\n        sta sp_started\n        jsr sp_poll\n')
    source=once(source,'profile_published:\n','profile_published:\n        jsr sp_wait\n')
    source=once(source,f'        jsr {advance}\n','        jsr sp_advance\n')
    source=once(source,'        jsr v3_draw_label\n','        jsr v3_draw_label\n        jsr sp_draw\n')
    source=once(source,'irq_no_flip:\n','irq_no_flip:\n        jsr sp_tick\n')
    source=once(source,'v3_reset:\n','v3_reset:\n        lda #3\n        sta sp_level\n')
    code=f'''
* = $3000
.logical $9000
sp_poll:
        lda #$ff
        sta $dc02
        lda #0
        sta $dc03
        lda #$df
        sta $dc00
        lda $dc01
sp_row5_read:
        sta sp_row
        and #1
        beq sp_plus
        lda sp_row
        and #8
        beq sp_minus
        lda #$ef
        sta $dc00
        lda $dc01
sp_row4_read:
        and #8
        beq sp_zero
        lda #0
        sta sp_held
        beq sp_poll_done
sp_plus:
        lda sp_held
        bne sp_poll_done
        lda sp_level
        cmp #{len(rates)-1}
        bcs sp_max
        inc sp_level
        lda sp_level
        cmp #{len(rates)-1}
        bne sp_increased
        lda #5
        bne sp_message
sp_increased:
        lda #0
        beq sp_message
sp_minus:
        lda sp_held
        bne sp_poll_done
        lda sp_level
        beq sp_min
        dec sp_level
        lda #1
        bne sp_message
sp_zero:
        lda sp_held
        bne sp_poll_done
        lda #3
        sta sp_level
        lda #2
        bne sp_message
sp_max:
        lda #3
        bne sp_message
sp_min:
        lda #4
sp_message:
        sta sp_message_id
        lda #1
        sta sp_held
        lda #50
        sta sp_ttl
        inc sp_revision
sp_poll_done:
        lda #$ff
        sta $dc00
        sta $dc02
sp_poll_return:
        rts
sp_tick:
        lda sp_ttl
        beq sp_tick_done
        dec sp_ttl
        beq sp_expired
        lda sp_message_id
        cmp #5
        bne sp_tick_done
        lda sp_ttl
        cmp #40
        bne sp_tick_done
        lda #3
        sta sp_message_id
sp_expired:
        inc sp_revision
sp_tick_done:
        rts
sp_advance:
        ldx sp_level
        lda sp_skips,x
        sta sp_remaining
sp_advance_loop:
        jsr {advance}
        dec sp_remaining
        bne sp_advance_loop
        rts
sp_wait:
        ldx sp_level
        cpx #3
        bcs sp_wait_done
        lda tick_counter
        sec
        sbc sp_started
        bne sp_nonzero_cost
        lda #1
sp_nonzero_cost:
        sta sp_cost
        lda sp_dividers,x
        sec
        sbc #1
        sta sp_waits
sp_wait_period:
        lda tick_counter
        sta sp_wait_start
sp_wait_loop:
        lda tick_counter
        cmp sp_last_poll
        beq sp_wait_check
        sta sp_last_poll
        jsr sp_poll
        lda sp_level
        cmp #3
        bcs sp_wait_done
sp_wait_check:
        lda tick_counter
        sec
        sbc sp_wait_start
        cmp sp_cost
        bcc sp_wait_loop
        dec sp_waits
        bne sp_wait_period
sp_wait_done:
        rts
sp_draw:
        ldx render_slot
        lda sp_revision
        cmp sp_slot_revision,x
        bne sp_draw_bitmap
        lda sp_ttl
        bne sp_draw_colors
        rts
sp_draw_bitmap:
        sta sp_slot_revision,x
        lda bitmap_base_hi,x
        clc
        adc #$1d
        sta sp_bitmap_store+2
        lda sp_ttl
        beq sp_blank
        ldy sp_message_id
        lda sp_message_lo,y
        sta sp_bitmap_read+1
        lda sp_message_hi,y
        sta sp_bitmap_read+2
        ldy #55
sp_bitmap_loop:
sp_bitmap_read:
        lda $ffff,y
sp_bitmap_store:
        sta $3dc0,y
        dey
        bpl sp_bitmap_loop
        jmp sp_draw_colors
sp_blank:
        lda #0
        ldy #55
sp_blank_loop:
        sta $3dc0,y
        dey
        bpl sp_blank_loop
        ; Patch both stores together, below, so all three slots are cleared.
sp_draw_colors:
        ldx render_slot
        lda v3_screen_hi,x
        clc
        adc #3
        sta sp_color_store+2
        lda #$10
        ldx sp_ttl
        beq sp_color_ready
        ldx sp_message_id
        cpx #3
        bcc sp_normal_color
        lda #$20
        cpx #4
        beq sp_color_ready
        ldx tick_counter
        txa
        and #8
        beq sp_red
        lda #$10
        bne sp_color_ready
sp_red:
        lda #$20
        bne sp_color_ready
sp_normal_color:
        lda v3_background
        cmp #1
        beq sp_black_text
        lda #$10
        bne sp_color_ready
sp_black_text:
        lda #0
sp_color_ready:
        ora v3_background
        ldy #6
sp_color_loop:
sp_color_store:
        sta $07b8,y
        dey
        bpl sp_color_loop
        rts
sp_level: .byte 3
sp_held: .byte 0
sp_row: .byte 0
sp_ttl: .byte 0
sp_message_id: .byte 0
sp_revision: .byte 0
sp_slot_revision: .byte 0,0,0
sp_started: .byte 0
sp_remaining: .byte 0
sp_cost: .byte 0
sp_waits: .byte 0
sp_wait_start: .byte 0
sp_last_poll: .byte 0
sp_skips: .byte {','.join(str(n) for n,d in rates)}
sp_dividers: .byte {','.join(str(d) for n,d in rates)}
sp_message_lo: .byte <sp_inc,<sp_dec,<sp_rst,<sp_max_text,<sp_min_text,<sp_wow
sp_message_hi: .byte >sp_inc,>sp_dec,>sp_rst,>sp_max_text,>sp_min_text,>sp_wow
'''
    code=code.replace('        sta sp_bitmap_store+2\n','        sta sp_bitmap_store+2\n        sta sp_blank_store+2\n')
    code=code.replace('sp_blank_loop:\n        sta','sp_blank_loop:\nsp_blank_store:\n        sta')
    for label,message in [('inc','SPD.INC'),('dec','SPD.DEC'),('rst','SPD.RST'),('max_text','SPD.MAX'),('min_text','SPD.MIN'),('wow','WOW!   ')]:
        pixels=bytearray(bitmap_text(message));pixels[24:32]=bytes([0x18,0x18,0x18,0x18,0,0x18,0x18,0] if label=='wow' else [0,0,0,0,0,0x18,0x18,0])
        code+=f'sp_{label}:\n'+'\n'.join(bytes_lines(pixels))+'\n'
    code+='''sp_end:
.if * > $9800
.error "Interactive speed module exceeds private RAM"
.endif
.here
'''
    code+='* = $2200\nsp_boot_copy:\n        ldx #0\nsp_boot_copy_loop:\n'+copy+'        inx\n        bne sp_boot_copy_loop\n        rts\n'
    return source+code


def describe(manifest,samples):
    manifest['interactive_cart']['keys'].update({'+':'increase rotation speed','-':'decrease rotation speed','0':'reset rotation speed'})
    manifest['interactive_cart']['speed']=dict(default_level=3,levels=[dict(skip=n,hold_factor=d) for n,d in levels(samples)],
        maximum_step=max(n for n,d in levels(samples)),hold='extra wait proportional to just-completed production time; starfield IRQ continues',
        feedback=['SPD.INC','SPD.DEC','SPD.RST','SPD.MAX','SPD.MIN'],max_feedback='WOW! then white/red SPD.MAX text flash',
        message_position=[256,184],message_pal_ticks=50,ram=[0x9000,0x9800],boot_staging=[0x3000,0x4000])
