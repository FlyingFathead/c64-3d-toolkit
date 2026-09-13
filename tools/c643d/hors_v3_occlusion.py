"""Optional conservative sprite masks for opaque black SVG paint.

VIC priority cannot distinguish black ink from black empty space. A per-picture
painted bounding box hides stars in solid/card presentations, including holes.
The normal gradient presentations bypass the box test. All data is copied into
RAM before bitmap initialization; the IRQ never reads cartridge ROM.
"""
from .demo_colors import once
from .emit import bytes_lines


def configure(source, bounds):
    if not 1 <= len(bounds) <= 255:
        raise ValueError('Opaque sprite masks require 1..255 picture bounds')
    for box in bounds:
        if box is not None and not (len(box)==4 and 0<=box[0]<=box[1]<256 and 0<=box[2]<=box[3]<192):
            raise ValueError(f'Invalid painted bounds: {box}')
    # Move the 1 KiB trajectories out of the cramped effects code region.
    first,last=source.index('fx_x0:\n'),source.index('fx_end:\n')
    paths=source[first:last]
    source=source[:first]+source[last:]
    source=once(source,'fx_irq_active:\n        ldx display_slot\n', '''fx_irq_active:
        ldx display_slot
        ldy slot_frame,x
        sty fx_box_frame+1
        lda fx_box_xmin,y
        cmp #255
        lda #0
        rol a
        eor #1
        sta fx_box_enabled+1
''')
    source=once(source,'        sta fx_y\n        lsr a\n', '''        sta fx_y
fx_box_enabled:
        lda #0
        beq fx_no_box
        jsr fx_box_test
        bcs fx_hidden
fx_no_box:
        lda fx_y
        lsr a
''')
    source=once(source,'fx_end:\n', '''fx_box_test:
fx_box_frame:
        ldy #0
        lda fx_x
        cmp fx_box_xmin,y
        bcc fx_box_outside
        cmp fx_box_xmax,y
        beq fx_box_check_y
        bcs fx_box_outside
fx_box_check_y:
        lda fx_y
        cmp fx_box_ymin,y
        bcc fx_box_outside
        cmp fx_box_ymax,y
        beq fx_box_inside
        bcs fx_box_outside
fx_box_inside:
        sec
        rts
fx_box_outside:
        clc
        rts
fx_end:
''')
    copies=''.join(f'        lda ${0x2800+p*256:04x},x\n        sta ${0x8800+p*256:04x},x\n' for p in range(8))
    source=once(source,'sp_boot_copy_loop:\n','sp_boot_copy_loop:\n'+copies)
    source=once(source,'        bne sp_boot_copy_loop\n',
        '        beq sp_boot_copy_done\n        jmp sp_boot_copy_loop\nsp_boot_copy_done:\n')
    source+='\n* = $2800\n.logical $8800\n'
    for i,name in enumerate(('xmin','xmax','ymin','ymax')):
        values=[box[i] if box is not None else 255 for box in bounds]
        values+=[255]*(256-len(values))
        source+=f'fx_box_{name}:\n'+'\n'.join(bytes_lines(values))+'\n'
    source+=paths+'''fx_box_data_end:
.if * != $9000
.error "Opaque mask and star path RAM layout changed"
.endif
.here
'''
    return source
