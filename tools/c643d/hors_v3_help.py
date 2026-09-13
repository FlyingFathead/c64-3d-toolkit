"""On-demand native text help; bitmap buffers and animation state stay intact."""
from .buildscreen import screen_codes
from .emit import bytes_lines
from .demo_colors import once


def help_lines(version, *, effects=False, modes=False, variants=(), hud=True):
    lines = [f'c64-3d-toolkit v{version}', 'interactive mode help',
             'STOP/ESC / SHIFT+H  open / close help',
             'SPACE         close help / start',
             'CURSOR / JOY1/2 L/R  direction',
             '+ / - / 0     speed up / down / reset',
             'F2            reset presentation',
             'F4            next background colour',
             'F5            background cycle on/off',
             'F6 / F7       slower / faster cycle',
             'F8            border black / follow',
             'CTRL+F7       next border colour']
    if effects: lines += ['SHIFT+S       starfield on / off',
                          '1 / 2 / 3     stars reset / more / less',
                          '4             light / full starfield']
    if modes: lines += ['F3            next logo colour overlay',
                        'SHIFT+T / W   solid on white, no stars',
                        'SHIFT+G       gradient, black + stars' if effects else 'SHIFT+G       gradient on black',
                        'SHIFT+R       axis spin / space crawl']
    if 'card' in variants: lines += ['SHIFT+B       white card / gradient']
    if 'outline' in variants: lines += ['SHIFT+O       solid outline / gradient']
    if hud: lines += ['SHIFT+I       name and V/E counts on/off',
              'SHIFT+F       FPS/speed messages on/off',
              'SHIFT+U       all HUD text on/off']
    lines += ['F2/4/6/8 = SHIFT + F1/3/5/7']
    lines[0] = lines[0].ljust(30) + 'pg 1/2 >'
    if len(lines)>25 or any(len(line)>40 for line in lines):
        raise ValueError('Interactive help exceeds 40x25 text screen')
    return lines


def help_pages(version, *, interval=5, **options):
    return [help_lines(version, **options), [
        f'c64-3d-toolkit v{version}'.ljust(30)+'pg 2/2 <',
        'interactive mode help',
        '5   exhibition on / off',
        '6   ordered / random selection',
        '7/8 interval -/+5s (5..60s)',
        f'Default: {interval}s. HUD/stars off on entry.',
        'Star keys still work. Help pauses timer.',
        'LEFT/RIGHT: page. STOP/ESC: close.',
    ]]


def packed_help(pages):
    # Length-prefixed rows omit right padding and share the common header.
    result=[]; offsets=[]
    for page in pages:
        offsets.append(len(result))
        for line in page:
            codes=screen_codes(line)
            packed=[]; i=0
            while i<len(codes):
                j=i
                while j<len(codes) and codes[j]==32: j+=1
                if j-i>=3:
                    packed.extend((254,j-i));i=j
                else:
                    packed.append(codes[i]);i+=1
            result += [len(codes),*packed]
        result.append(255)
    if len(result)>1024: raise ValueError('Packed help exceeds 1 KiB')
    return result,offsets


def help_screen_codes(lines):
    codes = screen_codes(''.join(line.ljust(40) for line in lines).ljust(1024))
    # Reverse glyphs include reversed spaces, giving two full-width stripes.
    # Black letter cutouts remain legible against light blue and cyan.
    codes[:80] = [code | 128 for code in codes[:80]]
    return codes


def configure(source, *, version, effects=False, modes=False, stars=False, variants=(), hud=True, interval=5):
    # FX already scans Shift. RUN/STOP reuses the density row when stars exist;
    # otherwise it needs one short row7 scan per speed poll. Help draws on demand.
    if effects:
        source=once(source,'        beq fx_keys_released\n',
                    '        beq fx_keys_released\n        jsr hp_shifted\n')
    else:
        source=once(source,'sp_poll:\n','sp_poll:\n        jsr hp_poll\n')
    if not stars:
        source=once(source,'sp_row5_read:\n','sp_row5_read:\n        pha\n        jsr hp_stop_poll\n        pla\n')
    code='''
* = $3800
.logical $9800
hp_stop_poll:
        lda #$7f
        sta $dc00
        lda $dc01
hp_stop_read:
        and #$80
        bne hp_stop_return
        jmp hp_open
hp_stop_return:
        rts
hp_poll:
        jsr v3_shift
        beq hp_return
hp_shifted:
        lda #$f7
        sta $dc00
        lda $dc01
hp_h_read:
        and #$20
        bne hp_return
hp_open:
        php
        sei
        jsr hp_save
        lda #0
        sta hp_page
        sta hp_nav_held
        jsr hp_paint
        jsr hp_display
hp_visible:
        jsr hp_release
hp_wait:
        jsr hp_navigation
        jsr hp_exit_key
        beq hp_wait
        jsr hp_release
        jsr hp_restore
        lda #1
        sta $d019
        plp
hp_return:
        rts
hp_exit_key:
        lda #$7f
        sta $dc00
        lda $dc01
hp_space_read:
        and #$90
        cmp #$90
        bne hp_pressed
        jsr v3_shift
        beq hp_no_key
        lda #$f7
        sta $dc00
        lda $dc01
hp_close_h_read:
        and #$20
        beq hp_pressed
hp_no_key:
        lda #0
        rts
hp_pressed:
        lda #1
        rts
hp_release:
        jsr hp_exit_key
        bne hp_release
        rts
hp_save:
'''
    regs=(0xd011,0xd016,0xd018,0xdd00,0xd020,0xd021,0xd015)
    for i,reg in enumerate(regs):
        code+=f'        lda ${reg:04x}\n'
        if reg==0xd011: code+='        and #$7f\n'
        code+=f'        sta hp_saved+{i}\n'
    code+='        rts\nhp_restore:\n        lda #$0b\n        sta $d011\n'
    for i,reg in reversed(list(enumerate(regs))):
        code+=f'        lda hp_saved+{i}\n        sta ${reg:04x}\n'
    code+='''        lda #$ff
        sta $dc00
        sta $dc02
hp_restored:
        rts
hp_display:
        lda #$0b
        sta $d011
        lda #0
        sta $d015
        sta $d020
        sta $d021
        sta $dc03
        lda #$ff
        sta $dc02
        lda #3
        sta $dd02
        lda $dd00
        and #$fc
        ora #1
        sta $dd00
        lda #$16
        sta $d018
        lda #8
        sta $d016
        ldx #0
        lda #1
hp_white:
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $db00,x
        inx
        bne hp_white
        ldx #39
hp_header_colors:
        lda #14
        sta $d800,x
        lda #3
        sta $d828,x
        dex
        bpl hp_header_colors
        lda #$1b
        sta $d011
        rts
hp_navigation:
        lda #$fe
        sta $dc00
        lda $dc01
hp_cursor_read:
        and #4
        beq hp_cursor_pressed
        lda #0
        sta hp_nav_held
        rts
hp_cursor_pressed:
        lda hp_nav_held
        bne hp_navigation_done
        inc hp_nav_held
        jsr v3_shift
        eor #1
        cmp hp_page
        beq hp_navigation_done
        sta hp_page
        jmp hp_paint
hp_navigation_done:
        rts
hp_paint:
        ldx #0
        lda #32
hp_clear_text:
        sta $8400,x
        sta $8500,x
        sta $8600,x
        sta $8700,x
        inx
        bne hp_clear_text
        ldx hp_page
        lda hp_page_lo,x
        sta hp_read+1
        lda hp_page_hi,x
        sta hp_read+2
        lda #0
        sta hp_write+1
        sta hp_row
        lda #$84
        sta hp_write+2
hp_line:
        jsr hp_read_byte
        cmp #255
        beq hp_invert
        tax
        ldy #0
        cpx #0
        beq hp_next_line
hp_letters:
        jsr hp_read_byte
        cmp #254
        bne hp_write
        jsr hp_read_byte
        sta hp_row
hp_space_run:
        iny
        dex
        dec hp_row
        bne hp_space_run
        cpx #0
        beq hp_next_line
        bne hp_letters
hp_write:
        sta $8400,y
        iny
        dex
        bne hp_letters
hp_next_line:
        clc
        lda hp_write+1
        adc #40
        sta hp_write+1
        bcc hp_line
        inc hp_write+2
        bne hp_line
hp_invert:
        ldx #79
hp_invert_loop:
        lda $8400,x
        ora #128
        sta $8400,x
        dex
        bpl hp_invert_loop
        rts
hp_read_byte:
hp_read:
        lda $ffff
        inc hp_read+1
        bne hp_read_done
        inc hp_read+2
hp_read_done:
        rts
hp_saved: .fill 7,0
hp_page: .byte 0
hp_nav_held: .byte 0
hp_row: .byte 0
hp_end:
.if * > $9c00
.error "Interactive help overlaps density RAM"
.endif
.here
* = $3c00
.logical $c000
hp_packed:
'''
    pages=help_pages(version,effects=stars,modes=modes,variants=variants,hud=hud,interval=interval)
    packed,offsets=packed_help(pages)
    code+='\n'.join(bytes_lines(packed))+'\nhp_page_lo: .byte <hp_packed,<('+str(offsets[1])+'+hp_packed)\nhp_page_hi: .byte >hp_packed,>('+str(offsets[1])+'+hp_packed)\n.if * > $c400\n.error \"Help data exceeds private page store\"\n.endif\n.here\nhp_text = $8400\n'
    for page in range(4):
        source=once(source,f'sta ${0x8400+page*256:04x},x\n',f'sta ${0xc000+page*256:04x},x\n')
    return source+code


def describe(manifest,version,*,effects=False,modes=False,variants=(),hud=True,interval=5):
    for key in ('Shift+H','RUN/STOP (Esc in VICE)'):
        manifest['interactive_cart']['keys'][key]='pause/open or close help; Space also closes; return to intro until SPACE starts playback'
    manifest['interactive_cart']['help']=dict(version=version,lines=help_lines(version,effects=effects,modes=modes,variants=variants,hud=hud),
        startup='original build screen waits for SPACE; press SHIFT+H for help on the row above',screen_ram=[0x8400,0x8800],
        pages=help_pages(version,effects=effects,modes=modes,variants=variants,hud=hud,interval=interval),
        packed_text_ram=[0xc000,0xc400],
        navigation='C64 cursor right / Shift+cursor right (left); host arrows in VICE',
        code_ram=[0x9800,0x9c00],extra_reserved_RAM_bytes=3072,
        header=dict(rows=2,width=40,background_colors=[14,3],text_color=0,implementation='reverse ROM glyphs; event-only color RAM writes'),
        pause='producer and raster IRQ pause; bitmap buffers and presentation settings preserved',
        idle='RUN/STOP reuses density row7: 9 extra CPU cycles per idle input poll, no new CIA read' if effects else 'RUN/STOP adds one row7 read per input poll (34 CPU cycles including saved A); Shift+H also checks Shift')
