; c64-3d-toolkit EasyFlash demo cartridge bootstrap.
;
; Native EasyFlash reset starts in Ultimax mode with bank 0 selected and ROMH
; visible at $E000-$FFFF.  In Ultimax, normal high RAM such as $C800 is not a
; safe destination, so use the always-visible 256-byte EasyFlash RAM at $DF00
; as a tiny mapper/copy trampoline.  The trampoline switches to 8K mode, where
; bank 0 ROML appears at $8000 and normal C64 RAM at $C800 is accessible, copies
; the menu/loader runtime there, hides the cartridge, and jumps to $C800.
;
; Bank 0 layout:
;   ROMH $E000-$FFFF  this bootstrap + reset vectors
;   ROML $8000-$87FF  2048-byte menu/loader runtime (host packed)

EF_BANK        = $de00
EF_CONTROL     = $de02
EF_OFF         = $04
EF_8K          = $06
RAM_CODE       = $df00
RUNTIME_SRC    = $8000
RUNTIME_DST    = $c800

* = $e000
boot:
    sei
    cld
    ldx #$ff
    txs

    lda #$37
    sta $01
    lda #$2f
    sta $00

    ; Copy the mapper-safe trampoline before changing out of Ultimax.  EasyFlash
    ; RAM at $DF00 remains visible in every cartridge mapping mode.
    ldx #0
copy_ramcode:
    lda ramcode,x
    sta RAM_CODE,x
    inx
    cpx #ramcode_end-ramcode
    bne copy_ramcode
    jmp RAM_CODE

ramcode:
    lda #0
    sta EF_BANK
    lda #EF_8K
    sta EF_CONTROL

    ; Eight 256-byte pages: bank 0 ROML $8000-$87FF -> C64 RAM $C800-$CFFF.
    ldx #0
copy_runtime:
    lda RUNTIME_SRC+$000,x
    sta RUNTIME_DST+$000,x
    lda RUNTIME_SRC+$100,x
    sta RUNTIME_DST+$100,x
    lda RUNTIME_SRC+$200,x
    sta RUNTIME_DST+$200,x
    lda RUNTIME_SRC+$300,x
    sta RUNTIME_DST+$300,x
    lda RUNTIME_SRC+$400,x
    sta RUNTIME_DST+$400,x
    lda RUNTIME_SRC+$500,x
    sta RUNTIME_DST+$500,x
    lda RUNTIME_SRC+$600,x
    sta RUNTIME_DST+$600,x
    lda RUNTIME_SRC+$700,x
    sta RUNTIME_DST+$700,x
    inx
    bne copy_runtime

    lda #EF_OFF
    sta EF_CONTROL
    jmp RUNTIME_DST
ramcode_end:

.if ramcode_end-ramcode > 255
    .error "EasyFlash demo bootstrap trampoline must fit in $DF00-$DFFF RAM"
.endif

    .fill $fffa-*, $ff
    .word boot                 ; NMI fallback
    .word boot                 ; RESET
    .word boot                 ; IRQ/BRK fallback
