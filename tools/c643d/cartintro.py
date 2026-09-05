"""Generate an optional native C64 bitmap introduction for the scene cart.

Code/data occupy $8000-$99ff in RAM, loaded from unused ROMH bank 0 space.
No image assets or host-rendered movie frames are used by this title routine.
"""
from .font import FONT, glyph
from .emit import bytes_lines

LOWER={
 'b':['10000','10000','10110','11001','10001','10001','11110'],
 'c':['00000','00000','01111','10000','10000','10000','01111'],
 'm':['00000','00000','11010','10101','10101','10101','10101'],
 'o':['00000','00000','01110','10001','10001','10001','01110'],
 'u':['00000','00000','10001','10001','10001','10011','01101'],
 '.':['00000','00000','00000','00000','00000','00100','00100'],
 'a':['00000','00000','01110','00001','01111','10001','01111'],
 'd':['00001','00001','01111','10001','10001','10001','01111'],
 'e':['00000','00000','01110','10001','11111','10000','01111'],
 'g':['00000','01111','10001','10001','01111','00001','01110'],
 'h':['10000','10000','10110','11001','10001','10001','10001'],
 'i':['00100','00000','01100','00100','00100','00100','01110'],
 'l':['01100','00100','00100','00100','00100','00100','01110'],
 'n':['00000','00000','10110','11001','10001','10001','10001'],
 'p':['00000','11110','10001','10001','11110','10000','10000'],
 'r':['00000','00000','10110','11001','10000','10000','10000'],
 's':['00000','00000','01111','10000','01110','00001','11110'],
 't':['00100','00100','11111','00100','00100','00101','00010'],
 'y':['00000','00000','10001','10001','01111','00001','01110'],
}


def scaled_text(text,scale):
    rows=[]
    for y in range(8):
        row=[]
        for ch in text:
            raw=[int(r,2)<<2 for r in LOWER[ch]]+[0] if ch in LOWER else glyph(ch)
            for x in range(8):row += [bool(raw[y]&(128>>x))]*scale
        rows += [row]*scale
    out=[]
    for cy in range(scale):
        for cx in range(len(text)*scale):
            for y in range(8):
                out.append(sum(128>>x for x in range(8) if rows[cy*8+y][cx*8+x]))
    return out


def emit_intro(path, *, ending=False):
    definitions=[('brand','FlyingFathead',2,7,9),('presents','presents',2,12,13),('dont',"DON'T",3,5,9),('lose','LOSE',3,23,9),('your','YOUR',3,2,14),('marbles','MARBLES',3,17,14),('machine','A COMMODORE 64',2,6,10),('format','CARTRIDGE DEMO',2,6,13)]
    if ending:definitions += [('thanks','THANK YOU',2,11,9),('watching','FOR WATCHING',2,8,12),('url','github.com/FlyingFathead',1,8,17)]
    descriptors=[];compact=False
    lines=['* = $8000','intro_start:','        lda #$0b','        sta $d011','        lda #0','        sta intro_stage','        sta $d020','        sta $d021','        jsr intro_clear','        lda #$00','        jsr intro_all_colors']
    def wait(n):lines.extend([f'        ldx #{n}','        jsr intro_wait'])
    def stage(n):lines.extend([f'intro_stage_{n}:',f'        lda #{n}','        sta intro_stage'])
    def setup(name,row=None):
        _,text,scale,col,cy=next(x for x in definitions if x[0]==name)
        if row is not None:cy=row
        bm=0x2000+cy*320+col*8;sc=0x0400+cy*40+col
        values=[('intro_src',f'<intro_{name}_data'),('intro_src+1',f'>intro_{name}_data'),('intro_dst',f'${bm&255:02x}'),('intro_dst+1',f'${bm>>8:02x}'),('intro_col',f'${sc&255:02x}'),('intro_col+1',f'${sc>>8:02x}'),('intro_width',str(len(text)*scale*8)),('intro_columns',str(len(text)*scale)),('intro_rows',str(scale))]
        if compact:
            label=f'outro_rect_{len(descriptors)}'
            descriptors.append((label,[v for _,v in values]))
            lines.extend([f'        lda #<{label}','        sta $f6',f'        lda #>{label}','        sta $f7','        jsr outro_setup'])
            return
        for dest,val in values:
            lines.extend([f'        lda #{val}',f'        sta {dest}'])
    def draw(name,row=None):setup(name,row);lines.append('        jsr intro_draw')
    def fade_box(name):
        for color in (0,11,12,15,1):
            setup(name);lines.extend([f'        lda #${color<<4:02x}','        jsr intro_box_color']);wait(5)
    def fade_white(background=False):
        for c in (0,11,12,15,1):
            value=0x10|c if background else (c<<4)|1
            lines.extend([f'        lda #${value:02x}','        jsr intro_all_colors',f'        lda #{c if background else 1}','        sta $d020']);wait(4)
    lines.extend(['        lda #$3b','        sta $d011'])
    wait(15);stage(1);draw('brand');fade_box('brand');wait(28)
    stage(2);draw('presents');fade_box('presents');wait(35)
    stage(3);fade_white(True);lines.append('        jsr intro_clear');wait(10)
    lines.extend(['        lda #$01','        jsr intro_all_colors'])
    for i,name in enumerate(('dont','lose','your','marbles'),4):
        stage(i)
        row=next(d[4] for d in definitions if d[0]==name)
        for pos,delay in ((row-2,2),(row+1,2)):
            draw(name,pos);wait(delay);setup(name,pos);lines.append('        jsr intro_erase')
        draw(name);wait(17)
    wait(45);stage(8);fade_white();lines.append('        jsr intro_clear');wait(9)
    stage(9);draw('machine');draw('format')
    for c in (1,15,12,11,0):
        lines.extend([f'        lda #${(c<<4)|1:02x}','        jsr intro_all_colors']);wait(4)
    wait(65);stage(10);fade_white();wait(8)
    stage(11);lines.extend(['        lda #$0b','        sta $d011','        lda #0','        sta $d020','        sta $d021','        rts'])
    if ending:
        lines.extend(['intro_resume = *','* = $5c80','outro_start:',
            '        sei','        lda #0','        sta $d01a','        lda #1','        sta $d019',
            # Preserve the last displayed bitmap: fade all physical screens first.
            '        ldx #50','        jsr intro_wait', # hold the settled constellation for one second
            '        lda #$11','        ldx #0','outro_white_loop:',
            '        sta $0400,x','        sta $0500,x','        sta $0600,x','        sta $0700,x',
            '        sta $4400,x','        sta $4500,x','        sta $4600,x','        sta $4700,x',
            '        sta $c800,x','        sta $c900,x','        sta $ca00,x','        sta $cb00,x',
            '        inx','        bne outro_white_loop','        lda #1','        sta $d020'])
        wait(8)
        lines.extend(['        lda $dd00','        and #$fc','        ora #3','        sta $dd00',
            '        lda #$1b','        sta $d011','        lda #$14','        sta $d018',
            '        lda #0','        sta $d020','        sta $d021','        ldx #0','greeting_clear:',
            '        lda #32','        sta $0400,x','        sta $0500,x','        sta $0600,x','        sta $0700,x',
            '        lda #1','        sta $d800,x','        sta $d900,x','        sta $da00,x','        sta $db00,x',
            '        inx','        bne greeting_clear','        ldy #0','greeting_type:',
            '        lda greeting_text,y','        sta $0590,y','        lda #160','        sta $0591,y'])
        wait(2)
        lines.extend(['        iny','        cpy #GREETING_LEN','        bne greeting_type','greeting_oops:'])
        wait(30)
        lines.extend(['greeting_backspace:','        lda #32','        sta $0590,y','        dey',
            '        lda #160','        sta $0590,y'])
        wait(3)
        lines.extend(['        cpy #GREETING_LEN-5','        bne greeting_backspace','        ldy #0','greeting_correct:',
            '        lda greeting_replacement,y','        sta $0590+GREETING_LEN-5,y',
            '        lda #160','        sta $0591+GREETING_LEN-5,y'])
        wait(3)
        lines.extend(['        iny','        cpy #9','        bne greeting_correct','greeting_done:',
            '        lda #32','        sta $0590+GREETING_LEN+4'])
        wait(45)
        lines.extend(['        lda #$3b','        sta $d011','        lda #1','        sta $d020'])
        lines.extend(['        lda $dd00','        and #$fc','        ora #3','        sta $dd00',
            '        lda #$18','        sta $d018','        jsr intro_clear',
            '        lda #$01','        jsr intro_all_colors'])
        compact=True
        for name,row in [('thanks',9),('watching',12)]:
            for pos in (row-1,row+1):
                draw(name,pos);wait(2);setup(name,pos);lines.append('        jsr intro_erase')
            draw(name);wait(13)
        draw('url');lines.append('outro_credits_visible:');wait(70)
        # Credits disappear into white, then the machine goes dark before BASIC.
        for c in (11,12,15,1):
            lines.extend([f'        lda #${(c<<4)|1:02x}','        jsr intro_all_colors']);wait(3)
        for c in (15,12,11,0):
            lines.extend([f'        lda #${c*17:02x}','        jsr intro_all_colors',f'        lda #{c}','        sta $d020']);wait(3)
        wait(15)
        lines.extend(['fake_basic_start:',
            '        lda #$1b','        sta $d011','        lda #$14','        sta $d018',
            '        lda #6','        sta $d021','        lda #14','        sta $d020',
            '        ldx #0','fake_basic_clear:',
            '        lda #32','        sta $0400,x','        sta $0500,x','        sta $0600,x','        sta $0700,x',
            '        lda #14','        sta $d800,x','        sta $d900,x','        sta $da00,x','        sta $db00,x',
            '        inx','        bne fake_basic_clear',
            '        ldx #0','fake_basic_banner:',
            '        lda fake_banner,x','        sta $0428,x','        lda fake_memory,x','        sta $0478,x',
            '        inx','        cpx #40','        bne fake_basic_banner',
            '        ldx #0','fake_ready_copy:','        lda fake_ready,x','        sta $04c8,x',
            '        inx','        cpx #6','        bne fake_ready_copy','fake_basic_ready:'])
        # Convincing pause at READY. with a blinking cursor.
        lines.extend(['        lda #160','        sta $0518']);wait(25)
        lines.extend(['        lda #32','        sta $0518']);wait(25)
        lines.extend(['        lda #160','        sta $0518']);wait(25)
        lines.extend(['        ldy #0','ghost_type_next:',
            '        lda ghost_message,y','        sta $0518,y','        lda #160','        sta $0519,y'])
        wait(4)
        lines.extend(['        iny','        cpy #GHOST_LEN','        bne ghost_type_next',
            'ghost_message_done:','        lda #32','        sta $0518+GHOST_LEN',
            'ghost_idle:','        lda #160','        sta $0540'])
        wait(25)
        lines.extend(['        lda #32','        sta $0540']);wait(25)
        lines.extend(['        jmp ghost_idle',
            'outro_setup:','        ldy #0','outro_setup_ptrs:',
            '        lda ($f6),y','        sta $f0,y','        iny','        cpy #6','        bne outro_setup_ptrs',
            '        lda ($f6),y','        sta intro_width','        iny','        lda ($f6),y',
            '        sta intro_columns','        iny','        lda ($f6),y','        sta intro_rows','        rts',
            '.if * > $6000','.error "ending code overlaps bitmap"','.endif','* = intro_resume'])
        compact=False
    lines.append('''
intro_wait:
        lda $d012
        cmp #250
        beq intro_wait
intro_wait_line:
        lda $d012
        cmp #250
        bne intro_wait_line
        dex
        bne intro_wait
        rts
intro_all_colors:
        ldx #0
intro_all_loop:
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        inx
        bne intro_all_loop
        rts
intro_clear:
        lda #0
        sta intro_dst
        lda #$20
        sta intro_dst+1
        ldx #32
        ldy #0
        lda #0
intro_clear_loop:
        sta (intro_dst),y
        iny
        bne intro_clear_loop
        inc intro_dst+1
        dex
        bne intro_clear_loop
        rts
intro_draw:
        ldx intro_rows
intro_draw_row:
        ldy #0
intro_draw_byte:
        lda (intro_src),y
        sta (intro_dst),y
        iny
        cpy intro_width
        bne intro_draw_byte
        clc
        lda intro_src
        adc intro_width
        sta intro_src
        bcc intro_source_ok
        inc intro_src+1
intro_source_ok:
        jsr intro_next_row
        dex
        bne intro_draw_row
        rts
intro_erase:
        ldx intro_rows
intro_erase_row:
        ldy #0
        lda #0
intro_erase_byte:
        sta (intro_dst),y
        iny
        cpy intro_width
        bne intro_erase_byte
        jsr intro_next_row
        dex
        bne intro_erase_row
        rts
intro_next_row:
        clc
        lda intro_dst
        adc #$40
        sta intro_dst
        lda intro_dst+1
        adc #1
        sta intro_dst+1
        rts
intro_box_color:
        sta intro_color
        ldx intro_rows
intro_color_row:
        ldy #0
        lda intro_color
intro_color_byte:
        sta (intro_col),y
        iny
        cpy intro_columns
        bne intro_color_byte
        clc
        lda intro_col
        adc #40
        sta intro_col
        bcc intro_color_next
        inc intro_col+1
intro_color_next:
        dex
        bne intro_color_row
        rts
intro_src = $f0
intro_dst = $f2
intro_col = $f4
intro_width: .byte 0
intro_columns: .byte 0
intro_rows: .byte 0
intro_color: .byte 0
intro_stage: .byte 0
''')
    for name,text,scale,col,row in definitions:
        lines += [f'intro_{name}_data:']+bytes_lines(scaled_text(text,scale))
    if ending:
        for label,values in descriptors:
            lines += [label+':','        .byte '+','.join(values)]
        def screen(text,width=None):
            if width:text=text.ljust(width)
            return [(ord(c)-64 if 64<=ord(c)<=95 else ord(c)) for c in text]
        for label,text,width in [('greeting_text','GREETINGS TO ALL OLD DEMOSCENE WANKE',None),('greeting_replacement','WANDERERS',None),('fake_banner','    **** COMMODORE 64 BASIC V2 ****',40),('fake_memory',' 64K RAM SYSTEM  38911 BASIC BYTES FREE',40),('fake_ready','READY.',None),('ghost_message',"HEY... DON'T LOSE YOUR MARBLES. :-)",None)]:
            lines += [label+':']+bytes_lines(screen(text,width))
        lines += ['GREETING_LEN = '+str(len('GREETINGS TO ALL OLD DEMOSCENE WANKE'))]
        lines += ['GHOST_LEN = '+str(len("HEY... DON'T LOSE YOUR MARBLES. :-)"))]
    lines+=['intro_end:','.if * > $9a00','.error "intro exceeds bank-zero bootstrap allocation"','.endif']
    path.write_text('\n'.join(lines)+'\n')
