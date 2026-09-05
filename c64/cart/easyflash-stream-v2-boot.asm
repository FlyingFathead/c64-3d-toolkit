; Standalone V2 reset. Bank 0 ROMH -> EasyFlash RAM trampoline.
; Three ROML banks hold the padded RAM image $0800-$4fff (72 pages).
* = $e000
boot:
        sei
        cld
        ldx #$ff
        txs
        lda #$2f
        sta $00
        lda #$37
        sta $01
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        lda #0
        sta $d01a
        sta $d011
        ldx #0
boot_copy:
        lda trampoline,x
        sta $df00,x
        inx
        cpx #trampoline_end-trampoline
        bne boot_copy
        jmp $df00
trampoline:
.logical $df00
        lda #$06
        sta $de02
        lda #0
        sta $de00
        sta $f0
        sta $f2
        sta $f4
        lda #$80
        sta $f1
        lda #$08
        sta $f3
        ldx #72
copy_page:
        ldy #0
copy_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne copy_byte
        inc $f3
        inc $f1
        lda $f1
        cmp #$a0
        bne same_bank
        inc $f4
        lda $f4
        sta $de00
        lda #$80
        sta $f1
same_bank:
        dex
        bne copy_page
        lda #$04
        sta $de02
        lda #$35
        sta $01
        jmp $080d
.here
trampoline_end:
.if trampoline_end-trampoline > 255
    .error "boot trampoline exceeds EasyFlash RAM"
.endif
        .fill $fffa-*, $ff
        .word boot,boot,boot
