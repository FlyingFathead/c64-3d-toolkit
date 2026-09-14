"""GMod3-only directory paging and fractional PAL playback pacing."""
from .demo_colors import once


def configure(source, *, pages=1, directory_bank=0, interactive=True, target_fps=None):
    if pages > 1 and not 1 < pages <= 8:raise ValueError('Paged directory requires 2..8 pages')
    code=[]
    if pages>1:
        source=once(source,'frame_begin:\n','frame_begin:\n        jsr gp_update\n')
        if interactive:
            source=once(source,'v3_reset:\n','v3_reset:\n        lda #0\n        sta gp_page\n        sta gp_previous\n        jsr gp_load\n')
        code += ['gp_page: .byte 0','gp_previous: .byte 0','gp_update:',
            '        lda frame_index','        cmp gp_previous','        beq gp_done']
        if interactive:
            code += ['        lda v3_step','        bmi gp_reverse','        lda frame_index',
                '        cmp gp_previous','        bcs gp_done','        inc gp_page','        lda gp_page',
                f'        cmp #{pages}','        bcc gp_change','        lda #0','        sta gp_page',
                '        beq gp_change','gp_reverse:','        lda frame_index','        cmp gp_previous',
                '        bcc gp_done','        lda gp_page','        bne gp_decrement',f'        lda #{pages}',
                '        sta gp_page','gp_decrement:','        dec gp_page']
        else:
            code += ['        bcs gp_done','        inc gp_page','        lda gp_page',f'        cmp #{pages}',
                '        bcc gp_change','        lda #0','        sta gp_page']
        code += ['gp_change:','        jsr gp_load','gp_done:','        lda frame_index','        sta gp_previous',
            '        rts','gp_load:','        sei','        lda #$37','        sta $01',
            f'        ldy #{directory_bank>>8}',f'        lda #{directory_bank&255}','        sta $de00,y',
            '        lda gp_page','        asl a','        asl a','        clc','        adc #$80',
            '        sta gp_read+2','        lda #$48','        sta gp_write+2','        ldy #4','        ldx #0',
            'gp_copy:','gp_read:','        lda $8000,x','gp_write:','        sta $4800,x','        inx','        bne gp_copy',
            '        inc gp_read+2','        inc gp_write+2','        dey','        bne gp_copy',
            '        lda #$35','        sta $01','        ldx #127','gp_high:','        lda $4b80,x',
            '        sta $a000,x','        dex','        bpl gp_high','        cli','        rts']
    if target_fps:
        # PAL targets are represented exactly as numerator/denominator. The
        # raster gate applies at display publication, not at producer startup.
        from fractions import Fraction
        ticks=Fraction(50/target_fps).limit_denominator(50)
        whole,rem=divmod(ticks.numerator,ticks.denominator)
        source=once(source,'        inc tick_counter\n','''        inc tick_counter
        lda gp_hold
        beq gp_can_flip
        dec gp_hold
        bne irq_no_flip
gp_can_flip:
''')
        source=once(source,'        stx display_slot\n','        stx display_slot\n        jsr gp_next_hold\n')
        code += ['gp_hold: .byte 0','gp_phase: .byte 0','gp_next_hold:',f'        lda #{whole}',
            '        sta gp_hold','        lda gp_phase','        clc',f'        adc #{rem}',
            f'        cmp #{ticks.denominator}','        bcc gp_phase_ok',f'        sbc #{ticks.denominator}',
            '        inc gp_hold','gp_phase_ok:','        sta gp_phase','        rts']
    if not code:return source
    # Private high RAM is clear of menu ($a100..$bfff), help ($c000..$c3ff)
    # and VIC screen 2 ($c800..$cbff). Stage before bitmap 0 is cleared.
    stage=0x2000 if interactive else 0x2600
    source += f'\n* = ${stage:04x}\n.logical $c400\n'+'\n'.join(code)+'\n.if * > $c600\n.error "GMod3 pager exceeds RAM"\n.endif\n.here\n'
    copy=f'        lda ${stage:04x},x\n        sta $c400,x\n        lda ${stage+256:04x},x\n        sta $c500,x\n'
    if interactive:
        source=once(source,'sp_boot_copy_loop:\n','sp_boot_copy_loop:\n'+copy)
    else:
        source=once(source,'        sei\n        cld\n','        sei\n        cld\n        jsr gp_boot\n')
        source+='\n* = $2800\ngp_boot:\n        ldx #0\ngp_boot_loop:\n'+copy+'        inx\n        bne gp_boot_loop\n        rts\n'
    return source
