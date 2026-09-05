; c64-3d-toolkit EasyFlash bank-switch smoke test.
;
; This is intentionally tiny and boring. It proves the native EasyFlash reset
; path, RAM-resident mapper transition, bank selection, ROML reads, and direct
; CRT boot before yunroll-cart frame streaming is connected to the backend.
;
; Hardware behaviour follows the EasyFlash Programmer's Reference:
;   $DE00 = write-only bank register
;   $DE02 = write-only control register
;   $04   = cartridge ROM off
;   $06   = 8K cartridge mode, ROML at $8000-$9FFF
; Native EasyFlash reset starts in Ultimax with bank 0 selected and ROMH visible
; at $E000-$FFFF, so the reset vector below lives in ROMH bank 0.
;
; VICE_DEBUGCART is supplied by the host assembler. Normal builds use 0. The
; automated emulator check uses 1 so a successful mapper test can terminate
; VICE through its optional debug-cart $D7FF exit hook.

EF_BANK        = $de00
EF_CONTROL     = $de02
EF_OFF         = $04
EF_8K          = $06
DEBUGCART_EXIT = $d7ff
RAM_CODE       = $df00
ZP_BANK        = $02
ZP_SCREEN      = $fb
ZP_SCREEN_HI   = $fc

* = $e000
boot:
    sei
    cld
    ldx #$ff
    txs

    ; Initialize the 6510 CPU port so I/O is visible before touching the
    ; EasyFlash registers. These are the normal C64 port/DDR values.
    lda #$37
    sta $01
    lda #$2f
    sta $00

    ; Native EasyFlash starts in Ultimax, so switching the mapper would bank
    ; this ROMH code out. EasyFlash provides 256 bytes of cartridge RAM at
    ; $DF00 which is always visible, including when cartridge ROM is hidden.
    ; Copy the mapper diagnostic there before changing modes. The routine is
    ; position-independent apart from fixed hardware/zero-page addresses.
    ldx #0
copy_ramcode:
    lda ramcode,x
    sta RAM_CODE,x
    inx
    cpx #ramcode_end-ramcode
    bne copy_ramcode
    jmp RAM_CODE

ramcode:
    ; Leave Ultimax. No KERNAL initialization is required for this diagnostic;
    ; setting up a plain text screen directly avoids relying on routines that
    ; may use/clear the same low RAM needed by the mapper trampoline.
    lda #EF_OFF
    sta EF_CONTROL

    ; VIC bank 0 ($0000-$3fff): CIA2 port bits 0-1 = %11 and outputs.
    lda $dd02
    ora #$03
    sta $dd02
    lda $dd00
    ora #$03
    sta $dd00

    ; 25-row text mode, 40 columns, screen at $0400, character ROM at $1000.
    lda #$1b
    sta $d011
    lda #$08
    sta $d016
    lda #$14
    sta $d018
    lda #$00
    sta $d020
    sta $d021

    ; Clear one full 1 KiB screen page and initialize matching color RAM.
    ldx #$00
clear_screen:
    lda #$20
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    lda #$01
    sta $d800,x
    sta $d900,x
    sta $da00,x
    sta $db00,x
    inx
    bne clear_screen

    lda #<$0400
    sta ZP_SCREEN
    lda #>$0400
    sta ZP_SCREEN_HI

    ; Banks 1..3 contain an ASCII marker at $8000 and their bank number at
    ; $8100. The sentinel makes the test prove actual bank selection rather
    ; than merely proving that some ROML data is readable.
    ldx #1
next_bank:
    stx ZP_BANK
    txa
    sta EF_BANK
    lda #EF_8K
    sta EF_CONTROL

    txa
    cmp $8100
    bne bank_fail

    ; Copy the NUL-terminated marker to screen RAM. Uppercase ASCII/PETSCII
    ; letters become C64 screen codes by clearing bit 6; digits/space/hyphen
    ; already use the desired screen-code values.
    ldy #0
print_byte:
    lda $8000,y
    beq bank_done
    cmp #$40
    bcc store_byte
    and #$3f
store_byte:
    sta (ZP_SCREEN),y
    iny
    bne print_byte

bank_done:
    ; Advance the output pointer by one 40-column text row.
    clc
    lda ZP_SCREEN
    adc #40
    sta ZP_SCREEN
    bcc screen_ptr_ok
    inc ZP_SCREEN_HI
screen_ptr_ok:
    ldx ZP_BANK
    inx
    cpx #4
    bne next_bank

    ; Leave the cartridge hidden after the test. Production/real-hardware
    ; builds simply remain on the successful screen.
    lda #EF_OFF
    sta EF_CONTROL
.if VICE_DEBUGCART
    lda #0
    sta DEBUGCART_EXIT
.endif
success_hang:
    clc
    bcc success_hang

bank_fail:
    lda #EF_OFF
    sta EF_CONTROL
    lda #2
    sta $d020
    sta $d021
.if VICE_DEBUGCART
    lda #1
    sta DEBUGCART_EXIT
.endif
fail_hang:
    clc
    bcc fail_hang
ramcode_end:

.if ramcode_end-ramcode > 255
    .error "EasyFlash smoke RAM routine must fit in the 256-byte $DF00 cartridge RAM"
.endif

    ; Keep unused bytes erased-looking in the raw flash image.
    .fill $fffa-*, $ff

; Native EasyFlash boot vectors at the end of ROMH bank 0.
* = $fffa
    .word boot     ; NMI fallback during the smoke test
    .word boot     ; RESET
    .word boot     ; IRQ/BRK while boot IRQs are disabled
