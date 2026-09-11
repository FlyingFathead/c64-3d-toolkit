; Shared scene reset with collision-free EasyAPI/name metadata.
.weak
EXTENSION_PAGES = 28
.endweak
; Three ROML banks hold the padded RAM image $0800-$5fff (88 pages).
* = $e000
boot:
        sei
        cld
        ldx #$ff
        txs
        ; Set the output latch before enabling the port outputs (EasyFlash guide).
        lda #$37
        sta $01
        lda #$2f
        sta $00
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
        ldx #88
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
        ; Optional native intro, ROMH bank 0 offset $0400 -> RAM $8000.
        ; Copying the reserved area is harmless in carts without an intro.
        lda #0
        sta $de00
        sta $f0
        sta $f2
        lda #$07
        sta $de02
        lda #$a4
        sta $f1
        lda #$80
        sta $f3
        ldx #EXTENSION_PAGES
intro_copy_page:
        ldy #0
intro_copy_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne intro_copy_byte
        inc $f1
        inc $f3
        dex
        bne intro_copy_page
        ; Metadata occupies ROMH $1800-$1bff. Restore the displaced
        ; RAM $9400-$97ff from ROML bank 2's unused $1800-$1bff tail.
        lda #2
        sta $de00
        lda #0
        sta $f0
        sta $f2
        lda #$98
        sta $f1
        lda #$94
        sta $f3
        ldx #4
metadata_restore_page:
        ldy #0
metadata_restore_byte:
        lda ($f0),y
        sta ($f2),y
        iny
        bne metadata_restore_byte
        inc $f1
        inc $f3
        dex
        bne metadata_restore_page
        lda #$04
        sta $de02
        lda #$35
        sta $01
        jmp $080d
.here
trampoline_end:
.if * > $e400
    .error "bootstrap overlaps reserved cartridge content"
.endif
.if trampoline_end-trampoline > 255
    .error "boot trampoline exceeds EasyFlash RAM"
.endif
        .fill $fffa-*, $ff
        .word boot,boot,boot
