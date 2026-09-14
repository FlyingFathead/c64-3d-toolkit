; Normal 8K CBM80 autostart. Runtime banks 1..3 -> $0800..$5fff.
; Loader runs in ordinary RAM $0200; no EasyFlash $DF00 RAM assumption.
.weak
BOOT_PAGES = 88
.endweak
* = $8000
        .word boot,boot
        .byte $c3,$c2,$cd,$38,$30
        .fill $800c-*, $ff
boot:
        sei
        cld
        ldx #$ff
        txs
        lda #$37
        sta $01
        lda #$2f
        sta $00
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda #0
        sta $dc0e
        sta $dc0f
        sta $dd0e
        sta $dd0f
        sta $d01a
        sta $d011
        sta $de08              ; ROM enabled; no vector override or SPI mode
        lda $dc0d
        lda $dd0d
        lda #$0f
        sta $d019
        ldx #0
copy_loader:
        lda loader,x
        sta $0200,x
        inx
        cpx #loader_end-loader
        bne copy_loader
        jmp $0200
loader:
.logical $0200
        lda #1
        sta $de00
        sta $f4
        lda #0
        sta $f0
        sta $f2
        lda #$80
        sta $f1
        lda #$08
        sta $f3
        ldx #BOOT_PAGES
copy_page:
        ldy #0
copy_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne copy_byte
        inc $f1
        inc $f3
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
        lda #$35
        sta $01
        ldx #0
gmod3_copy_high:
        lda $2300,x
        sta $a000,x
        inx
        bne gmod3_copy_high
        jmp $080d
.here
loader_end:
.if loader_end-loader > 256
        .error "GMod3 loader exceeds RAM $0200 page"
.endif
        .fill $a000-*, $ff
