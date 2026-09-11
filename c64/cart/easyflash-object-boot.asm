; Shared object reset. Historical renderer kernels keep their RAM layout.
; BOOT_PAGES is 72 for V2-V4 and 88 for V5-V10/HORS V1/V2.
.weak
BOOT_PAGES = 88
.endweak
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
        ; Reset may arrive with active CIA timers/interrupts. SEI alone
        ; does not mask CIA2 NMI. Quiesce sources before copying the loader.
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
        lda $dc0d
        lda $dd0d
        lda #$0f
        sta $d019
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
        ldx #BOOT_PAGES
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
.if * > $f800
    .error "bootstrap overlaps reserved cartridge content"
.endif
.if trampoline_end-trampoline > 255
    .error "boot trampoline exceeds EasyFlash RAM"
.endif
        .fill $fffa-*, $ff
        .word boot,boot,boot
