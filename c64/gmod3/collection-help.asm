; Main-menu help, using the same packed baseline pages as runtime help.
; No demo is launched. Selection survives; closing returns to the SPACE menu.
menu_help_poll:
        jsr menu_help_shift
        beq menu_help_return
        lda #$f7
        sta $dc00
        lda $dc01
        and #$20
        bne menu_help_return
        lda #0
        sta menu_help_page
        sta menu_help_held
        jsr menu_help_paint
        jsr menu_help_release
menu_help_wait:
        lda #$fe
        sta $dc00
        lda $dc01
        and #4
        bne menu_help_nav_release
        lda menu_help_held
        bne menu_help_exit_poll
        inc menu_help_held
        jsr menu_help_shift
        eor #1
        cmp menu_help_page
        beq menu_help_exit_poll
        sta menu_help_page
        jsr menu_help_paint
        jmp menu_help_exit_poll
menu_help_nav_release:
        lda #0
        sta menu_help_held
menu_help_exit_poll:
        jsr menu_help_exit_key
        beq menu_help_wait
        jsr menu_help_release
        jmp collection_menu ; resets stack, repaints selected page and highlight
menu_help_return:
        rts
menu_help_shift:
        lda #$fd
        sta $dc00
        lda $dc01
        and #$80
        beq menu_help_shift_yes
        lda #$bf
        sta $dc00
        lda $dc01
        and #$10
        beq menu_help_shift_yes
        lda #0
        rts
menu_help_shift_yes:
        lda #1
        rts
menu_help_exit_key:
        lda #$7f
        sta $dc00
        lda $dc01
        and #$90
        cmp #$90
        bne menu_help_pressed
        lda #$fe
        sta $dc00
        lda $dc01
        and #$10
        beq menu_help_pressed
        jsr menu_help_shift
        beq menu_help_return
        lda #$f7
        sta $dc00
        lda $dc01
        and #$20
        beq menu_help_pressed
        lda #0
        rts
menu_help_pressed:
        lda #1
        rts
menu_help_release:
        jsr menu_help_exit_key
        bne menu_help_release
        rts
menu_help_paint:
        ldx #0
menu_help_clear:
        lda #32
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        lda #1
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $db00,x
        inx
        bne menu_help_clear
        ldx #39
menu_help_stripes:
        lda #14
        sta $d800,x
        lda #3
        sta $d828,x
        dex
        bpl menu_help_stripes
        ldx menu_help_page
        lda menu_help_lo,x
        sta menu_help_read+1
        lda menu_help_hi,x
        sta menu_help_read+2
        lda #0
        sta $f2
        lda #4
        sta $f3
menu_help_line:
        jsr menu_help_read
        cmp #255
        beq menu_help_invert
        tax
        ldy #0
menu_help_letter:
        jsr menu_help_read
        cmp #254
        bne menu_help_write
        jsr menu_help_read
        sta menu_help_spaces
menu_help_space:
        iny
        dex
        dec menu_help_spaces
        bne menu_help_space
        cpx #0
        beq menu_help_next_line
        bne menu_help_letter
menu_help_write:
        sta ($f2),y
        iny
        dex
        bne menu_help_letter
menu_help_next_line:
        clc
        lda $f2
        adc #40
        sta $f2
        bcc menu_help_line
        inc $f3
        bne menu_help_line
menu_help_invert:
        ldx #79
menu_help_reverse:
        lda $0400,x
        ora #128
        sta $0400,x
        dex
        bpl menu_help_reverse
        rts
menu_help_read:
        lda $ffff
        inc menu_help_read+1
        bne menu_help_read_done
        inc menu_help_read+2
menu_help_read_done:
        rts
menu_help_page: .byte 0
menu_help_held: .byte 0
menu_help_spaces: .byte 0
