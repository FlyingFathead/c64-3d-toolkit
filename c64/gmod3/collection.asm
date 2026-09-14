; GMod3 collection front door. Bank 0, normal 8K CBM80 reset.
; RAM $a100..$bfff holds menu, collection navigation and text pages.
; RAM $0334 loader is outside the runtime's $0200 colour lookup table.
.include "collection-config.inc"
selected = $0330
held = $0331
page = $0332
stop_pending = $0333 ; $80 idle / $00 RUN/STOP latched by the raster IRQ
* = $8000
.word reset,reset
.byte $c3,$c2,$cd,$38,$30
.fill $800c-*, $ff
reset:
        lda #0
        sta selected
soft_reset:
        sei
        cld
        ldx #$ff
        txs
        lda #$37
        sta $01
        lda #$2f
        sta $00
        lda #0
        sta $de00
        sta $de08
        sta $d01a
        sta $d011
        sta $d015
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        ldx #0
copy_loader:
        lda loader_code-$2000,x
        sta $0334,x
        inx
        cpx #loader_end-$0334
        bne copy_loader
        lda #$81
        sta $f1
        lda #$a1
        sta $f3
        lda #0
        sta $f0
        sta $f2
        ldx #31
copy_resident_page:
        ldy #0
copy_resident_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne copy_resident_byte
        inc $f1
        inc $f3
        dex
        bne copy_resident_page
        jmp collection_enter_menu
.if * > $8100
.error "Collection boot header exceeds reserved page"
.endif
* = $8100
.logical $a100
collection_menu:
        sei
        ldx #$ff
        txs
        lda #0
        sta $d015
        sta $d020
        sta $d021
        lda #3
        sta $dd00
        lda #$16 ; lowercase/uppercase ROM set, matching screen_codes()
        sta $d018
        lda #$08
        sta $d016
        lda #$1b
        sta $d011
        lda #$ff
        sta $dc02
        lda #0
        sta $dc03
        lda #1
        sta held
        lda selected
        cmp #ENTRY_COUNT
        bcc menu_redraw
        lda #0
        sta selected
menu_redraw:
        lda selected
        ldx #0
menu_page_loop:
        cmp #15
        bcc menu_page_found
        sec
        sbc #15
        inx
        bne menu_page_loop
menu_page_found:
        sta menu_row
        stx page
        lda screen_lo,x
        sta $f0
        lda screen_hi,x
        sta $f1
        lda #0
        sta $f2
        lda #4
        sta $f3
        ldx #4
menu_copy_page:
        ldy #0
menu_copy_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne menu_copy_byte
        inc $f1
        inc $f3
        dex
        bne menu_copy_page
        ldx #0
        lda #15
menu_color:
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $db00,x
        inx
        bne menu_color
        ldx menu_row
        lda row_lo,x
        sta $f0
        lda row_hi,x
        sta $f1
        ldy #39
menu_highlight:
        lda ($f0),y
        ora #$80
        sta ($f0),y
        dey
        bpl menu_highlight
menu_poll:
        lda #$7f
        sta $dc00
        lda $dc01
menu_space_read:
        and #$10
        beq menu_space
        lda #$fe
        sta $dc00
        lda $dc01
.if INTERACTIVE
        and #2
        beq menu_enter
        lda $dc01
.endif
menu_cursor_read:
        and #$84
        cmp #$84
        bne menu_move
.if INTERACTIVE
        jsr menu_help_poll
.endif
        lda #0
        sta held
        jmp menu_poll
menu_space:
        lda held
        bne menu_poll
menu_space_release:
        lda $dc01
        and #$10
        beq menu_space_release
        jmp collection_start
.if INTERACTIVE
menu_enter:
        lda held
        bne menu_poll
menu_enter_release:
        lda $dc01
        and #2
        beq menu_enter_release
        jmp collection_start
.endif
menu_move:
        lda held
        bne menu_poll
        inc held
        lda #$fd
        sta $dc00
        lda $dc01
menu_shift_read:
        and #$80
        beq menu_previous
        lda #$bf
        sta $dc00
        lda $dc01
        and #$10
        beq menu_previous
        inc selected
        lda selected
        cmp #ENTRY_COUNT
        bcc menu_changed
        lda #0
        sta selected
        beq menu_changed
menu_previous:
        lda selected
        bne menu_decrement
        lda #ENTRY_COUNT
        sta selected
menu_decrement:
        dec selected
menu_changed:
        jmp menu_redraw
menu_row: .byte 0
row_lo: .byte <($0400+160),<($0400+200),<($0400+240),<($0400+280),<($0400+320),<($0400+360),<($0400+400),<($0400+440),<($0400+480),<($0400+520),<($0400+560),<($0400+600),<($0400+640),<($0400+680),<($0400+720)
row_hi: .byte >($0400+160),>($0400+200),>($0400+240),>($0400+280),>($0400+320),>($0400+360),>($0400+400),>($0400+440),>($0400+480),>($0400+520),>($0400+560),>($0400+600),>($0400+640),>($0400+680),>($0400+720)
.if * > $a400
.error "Collection menu exceeds RAM region"
.endif
.if INTERACTIVE
.include "collection-help.asm"
.if * > $a400
.error "Collection menu help exceeds RAM region"
.endif
.endif
.here
* = $8400
.logical $a400
collection_start:
.if INTERACTIVE
        lda #$80
        sta stop_pending
.endif
        ldx selected
        lda runtime_lo,x
        sta $f4
        lda runtime_hi,x
        sta $f5
        lda #0
        sta collection_count
        sta collection_count+1
        lda #1
        sta held
        lda #$ff
        sta $dc00
        jmp $0334
; Relocatable loader; all IRQ sources are masked before switching the CPU port.
loader_code:
.here
.logical $0334
        sei
        lda #0
        sta $d01a
        sta $d011
        sta $d015
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        ldy $f5
        cpy #$ff
        beq collection_loader_menu
        lda #$37
        sta $01
        ldy $f5
        lda $f4
        sta $de00,y
        lda #0
        sta $f0
        sta $f2
        lda #$80
        sta $f1
        lda #$08
        sta $f3
        ldx #88
collection_copy_page:
        ldy #0
collection_copy_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne collection_copy_byte
        inc $f1
        inc $f3
        lda $f1
        cmp #$a0
        bne collection_same_bank
        inc $f4
        bne collection_no_carry
        inc $f5
collection_no_carry:
        ldy $f5
        lda $f4
        sta $de00,y
        lda #$80
        sta $f1
collection_same_bank:
        dex
        bne collection_copy_page
        lda #$35
        sta $01
        ldx #0
collection_copy_high:
        lda $2300,x
        sta $a000,x
        inx
        bne collection_copy_high
        jmp $080d
collection_loader_menu:
        lda #$37
        sta $01
        lda #0
        sta $de00
        jmp soft_reset
collection_enter_menu:
        lda #$35
        sta $01
        jmp collection_menu
loader_end:
.if * > $0400
.error "Collection loader exceeds $0334..$03ff"
.endif
.here
; Continue RAM address after physical loader bytes.
.logical $a400 + (*-$8400)
collection_count: .word 0
.if * > $a500
.error "Collection start overlaps input poll"
.endif
.here
* = $8500
.logical $a500
collection_poll:
.if INTERACTIVE
        lda stop_pending
        bne collection_poll_keys
        jmp collection_return
collection_poll_keys:
        lda #$ff
        sta $dc02
        lda #0
        sta $dc03
        lda #$ef
        sta $dc00
        lda $dc01
collection_n_read:
        and #$80
        beq collection_next_key
        lda #$df
        sta $dc00
        lda $dc01
collection_p_read:
        and #2
        beq collection_previous_key
        lda #$fb
        sta $dc00
        lda $dc01
collection_c_read:
        and #$10
        beq collection_shade_key
        lda #0
        sta held
collection_poll_done:
        lda #$ff
        sta $dc00
        rts
collection_next_key:
        lda held
        bne collection_poll_done
collection_next:
        inc selected
        lda selected
        cmp #ENTRY_COUNT
        bcc collection_changed
        lda #0
        sta selected
        beq collection_changed
collection_previous_key:
        lda held
        bne collection_poll_done
        lda selected
        bne collection_dec
        lda #ENTRY_COUNT
        sta selected
collection_dec:
        dec selected
        jmp collection_changed
collection_shade_key:
        lda held
        bne collection_poll_done
        ldx selected
        lda shade_next,x
        cmp #$ff
        beq collection_poll_done
        sta selected
collection_changed:
        jmp collection_start
.else
        ldx selected
        lda collection_count+1
        cmp sample_hi,x
        bne collection_count_more
        lda collection_count
        cmp sample_lo,x
        bne collection_count_more
        jmp $c600 ; entry-specific drain: display the last published picture
collection_count_more:
        inc collection_count
        bne collection_count_done
        inc collection_count+1
collection_count_done:
        rts
.endif
.if * > $a600
.error "Collection input poll exceeds RAM region"
.endif
.here
* = $8600
.logical $a600
collection_return:
.if INTERACTIVE
        lda #$ff
        sta $f5
        jmp $0334
.else
        inc selected
        lda selected
        cmp #ENTRY_COUNT
        bcc collection_bench_next
        lda #0
        sta selected
collection_bench_next:
        jmp collection_start
.endif
.if * > $a640
.error "Collection return overlaps priority input service"
.endif
.here
* = $8640
.logical $a640
.if INTERACTIVE
collection_input_service:
        lda stop_pending
        beq collection_stop_now
        lda #$7f
        sta $dc00
        lda $dc01
        and #$80
        beq collection_stop_now
        jmp $9000 ; baseline sp_poll; every generated runtime asserts this ABI
collection_stop_now:
        jmp collection_return
.if * > $a680
.error "Collection priority input service overlaps IRQ latch"
.endif
.endif
.here
* = $8680
.logical $a680
.if INTERACTIVE
collection_irq_inputs:
        ; The caller saves A/X/Y. Restore the CIA column so an interrupted
        ; foreground keyboard scan sees exactly the column it selected.
        lda $dc00
        pha
        lda #$7f
        sta $dc00
        lda $dc01
        and #$80
        bne collection_irq_no_stop
        sta stop_pending
collection_irq_no_stop:
        pla
        sta $dc00
        jmp $9094 ; baseline sp_tick; menu reload is deferred to foreground
.if * > $a700
.error "Collection IRQ latch overlaps tables"
.endif
.endif
.here
* = $8700
.logical $a700
.include "collection-tables.inc"
.if * > $a900
.error "Collection tables exceed RAM region"
.endif
.here
* = $8900
.logical $a900
.include "collection-screens.inc"
.if INTERACTIVE
.include "collection-help-data.inc"
.endif
.if * > $c000
.error "Collection screens exceed RAM region"
.endif
.here
.fill $a000-*, $ff
