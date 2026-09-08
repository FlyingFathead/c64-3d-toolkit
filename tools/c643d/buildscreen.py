"""Compact native white-on-black, SPACE-skippable build identification screen."""
from .emit import bytes_lines


def screen_codes(text):
    # VIC lowercase/uppercase ROM character set at bank-zero $1800.
    return [ord(c)-96 if 'a' <= c <= 'z' else ord(c) for c in text]


def build_screen_lines(version, renderer):
    texts = [('toolkit', 'c64-3d-toolkit', 7), ('version', 'v. '+version, 10),
             ('renderer', renderer, 12),
             ('github', 'github.com/FlyingFathead/c64-3d-toolkit', 16),
             ('skip', 'SPACE to start', 20)]
    lines = ['build_screen_start:', '        lda #$0b', '        sta $d011',
             '        lda #3', '        sta $dd02', '        lda $dd00', '        ora #3', '        sta $dd00',
             '        lda #8', '        sta $d016', '        lda #0', '        sta $d020', '        sta $d021', '        sta $d015',
             '        ldx #0', 'build_screen_clear:', '        lda #32']
    lines += [f'        sta ${a:04x},x' for a in (0x400,0x500,0x600,0x700)]
    lines += ['        lda #1']+[f'        sta ${a:04x},x' for a in (0xd800,0xd900,0xda00,0xdb00)]
    lines += ['        inx', '        bne build_screen_clear', '        lda #$16', '        sta $d018']
    for name, text, row in texts:
        if len(text) > 40:
            raise ValueError('build screen line exceeds 40 characters')
        address = 0x400+row*40+(40-len(text))//2
        lines += [f'        ldx #{len(text)-1}', f'build_screen_copy_{name}:',
                  f'        lda build_screen_text_{name},x', f'        sta ${address:04x},x',
                  '        dex', f'        bpl build_screen_copy_{name}']
    lines += ['        lda #$ff', '        sta $dc02', '        lda #0', '        sta $dc03',
              '        lda #$7f', '        sta $dc00', '        lda #$1b', '        sta $d011',
              'build_screen_visible:', '        ldx #150', 'build_screen_leave:',
              '        lda $dc01', '        and #$10', '        beq build_screen_done',
              '        lda $d012', '        cmp #250', '        beq build_screen_leave',
              'build_screen_enter:', '        lda $dc01', '        and #$10', '        beq build_screen_done',
              '        lda $d012', '        cmp #250', '        bne build_screen_enter',
              '        dex', '        bne build_screen_leave', 'build_screen_done:',
              '        lda #$0b', '        sta $d011', '        lda #$ff', '        sta $dc00',
              '        lda #$18', '        sta $d018', '        rts']
    if renderer.startswith(('hors-render-v1', 'yunroll-v10')):
        # Keep instruction lengths and labels; branch unconditionally back
        # to keyboard polling. SPACE is the only exit.
        for i in range(len(lines)-1):
            if lines[i] == '        dex' and lines[i+1] == '        bne build_screen_leave':
                lines[i] = '        clc'
                lines[i+1] = '        bcc build_screen_leave'
    for name, text, _ in texts:
        lines += [f'build_screen_text_{name}:']+bytes_lines(screen_codes(text))
    return lines


def play_all_thanks_lines(version):
    """Ten PAL seconds between PLAY ALL rounds; native F1 returns to menu."""
    texts = [('title', 'THANK YOU FOR WATCHING', 6),
             ('version', 'c64-3d-toolkit v' + version, 10),
             ('cart', 'DEMO CART', 12),
             ('github', 'github.com/flyingfathead/c64-3d-toolkit', 16),
             ('exit', 'F1 TO RETURN TO MENU', 20)]
    lines = ['play_all_thanks_start:', '        sei', '        lda #$0b', '        sta $d011',
             '        lda #$37', '        sta $01',
             '        lda #$7f', '        sta $dc0d', '        sta $dd0d',
             '        lda $dc0d', '        lda $dd0d',
             '        lda #0', '        sta $d01a', '        sta $d015',
             '        sta $d020', '        sta $d021',
             '        lda #3', '        sta $dd02', '        lda $dd00', '        ora #3', '        sta $dd00',
             '        lda #8', '        sta $d016',
             '        ldx #0', 'play_all_thanks_clear:', '        lda #32']
    lines += [f'        sta ${a:04x},x' for a in (0x400, 0x500, 0x600, 0x700)]
    lines += ['        lda #1'] + [f'        sta ${a:04x},x' for a in (0xd800, 0xd900, 0xda00, 0xdb00)]
    lines += ['        inx', '        bne play_all_thanks_clear', '        lda #$16', '        sta $d018']
    for name, text, row in texts:
        if len(text) > 40:
            raise ValueError('PLAY ALL thank-you line exceeds 40 characters')
        address = 0x400 + row * 40 + (40 - len(text)) // 2
        lines += [f'        ldx #{len(text)-1}', f'play_all_thanks_copy_{name}:',
                  f'        lda play_all_thanks_text_{name},x', f'        sta ${address:04x},x',
                  '        dex', f'        bpl play_all_thanks_copy_{name}']
    lines += ['        lda #$ff', '        sta $dc02', '        lda #0', '        sta $dc03',
              '        lda #$fe', '        sta $dc00', '        lda #$1b', '        sta $d011',
              'play_all_thanks_visible:', '        ldy #10', '        ldx #50',
              'play_all_thanks_leave:', '        lda $dc01', '        and #$10', '        beq play_all_thanks_exit',
              '        lda $d012', '        cmp #250', '        beq play_all_thanks_leave',
              'play_all_thanks_enter:', '        lda $dc01', '        and #$10', '        beq play_all_thanks_exit',
              '        lda $d012', '        cmp #250', '        bne play_all_thanks_enter',
              '        dex', '        bne play_all_thanks_leave', '        ldx #50',
              '        dey', '        bne play_all_thanks_leave',
              'play_all_thanks_timeout:', '        clc', '        bcc play_all_thanks_done',
              'play_all_thanks_exit:',
              # Consume release so F1 does not also cycle the restored menu style.
              'play_all_thanks_key_release:', '        lda $dc01', '        and #$10',
              '        beq play_all_thanks_key_release', '        sec',
              'play_all_thanks_done:', '        lda #$0b', '        sta $d011',
              '        lda #$ff', '        sta $dc00', '        rts']
    for name, text, _ in texts:
        lines += [f'play_all_thanks_text_{name}:'] + bytes_lines(screen_codes(text))
    return lines
