; c64-3d-toolkit EasyFlash demo in-animation/menu control shim.
;
; Loaded to $0200 for the cartridge demo. The host patcher redirects each
; generated yunroll raster IRQ vector to $0200 and records the original IRQ
; address in $02F8/$02F9. With no control key pressed, this shim preserves
; A/X/Y and tail-jumps to the production renderer IRQ.
;
; Controls while an animation is running:
;   F1 or RUN/STOP  return to the cartridge menu
;   SPACE           launch the next demo (wraps at the end)
;
; Controls while the cartridge menu is running:
;   F1              cycle default -> decorative -> demoscene -> default
;
; The three 2 KiB menu runtimes live together in EasyFlash bank 1 ROMH. The
; shim copies the selected runtime into $C800-$CFFF before handing control back
; to the menu. The ordinary .prg files on disk are never modified.

EF_BANK        = $de00
EF_CONTROL     = $de02
EF_OFF         = $04
EF_16K         = $07

CONTROL_ORIG_LO = $02f8
CONTROL_ORIG_HI = $02f9
CONTROL_CURRENT = $02fa
CONTROL_LATCH   = $02fb
CONTROL_STYLE   = $02fc

; Scratch zero-page is safe on the hard handoff path because the current menu
; or renderer is being abandoned and the freshly loaded runtime reinitializes
; its own state immediately afterwards.
CTRL_SRC_LO     = $f9
CTRL_SRC_HI     = $fa
CTRL_DST_LO     = $fb
CTRL_DST_HI     = $fc

STYLE_BANK      = $01
STYLE_ROMH      = $a000
RUNTIME_DST     = $c800
RUNTIME_MENU    = $c803
RUNTIME_NEXT    = $c806
STYLE_COUNT     = 3

* = $0200
; Fixed entry table. Cartridge PRGs are patched to $0200; the menu itself uses
; $0203 to request a live style cycle.
cart_control_irq:
    jmp cart_control_irq_impl
cart_control_cycle:
    jmp control_cycle_style

cart_control_irq_impl:
    pha
    txa
    pha
    tya
    pha

    ; F1 is row 0 bit 4. Active-low keyboard matrix.
    lda #$fe
    sta $dc00
    lda $dc01
    and #$10
    beq control_menu_key

    ; SPACE is row 7 bit 4; RUN/STOP is row 7 bit 7.
    lda #$7f
    sta $dc00
    lda $dc01
    tax
    lda #$ff
    sta $dc00

    txa
    and #$80
    beq control_menu_key
    txa
    and #$10
    beq control_next_key

    ; No relevant key: arm the next keypress and continue the production IRQ.
    lda #0
    sta CONTROL_LATCH
control_chain:
    pla
    tay
    pla
    tax
    pla
    jmp (CONTROL_ORIG_LO)

control_menu_key:
    lda #$ff
    sta $dc00
    lda CONTROL_LATCH
    bne control_chain
    lda #1
    sta CONTROL_LATCH
    lda #<RUNTIME_MENU
    sta control_resume+1
    lda #>RUNTIME_MENU
    sta control_resume+2
    jmp control_abort_and_reload

control_next_key:
    lda CONTROL_LATCH
    bne control_chain
    lda #1
    sta CONTROL_LATCH
    lda #<RUNTIME_NEXT
    sta control_resume+1
    lda #>RUNTIME_NEXT
    sta control_resume+2
    jmp control_abort_and_reload

; Entered from the menu with JMP $0203. This is a hard handoff: increment the
; style, reload that style's runtime, and return through runtime_menu_entry.
control_cycle_style:
    inc CONTROL_STYLE
    lda CONTROL_STYLE
    cmp #STYLE_COUNT
    bcc control_cycle_ok
    lda #0
    sta CONTROL_STYLE
control_cycle_ok:
    lda #<RUNTIME_MENU
    sta control_resume+1
    lda #>RUNTIME_MENU
    sta control_resume+2

; Abandon the interrupted renderer/menu mainline and reload the currently
; selected style runtime from EasyFlash bank 1 ROMH. In 16K mode ROMH appears
; at $A000-$BFFF. Runtime N starts at $A000 + N*$0800.
control_abort_and_reload:
    sei
    ldx #$ff
    txs
    lda #0
    sta $d01a                  ; disable VIC raster IRQ while switching worlds
    lda #$0f
    sta $d019                  ; acknowledge pending VIC IRQ flags

    lda #$37
    sta $01
    lda #STYLE_BANK
    sta EF_BANK
    lda #EF_16K
    sta EF_CONTROL

    lda #0
    sta CTRL_SRC_LO
    sta CTRL_DST_LO
    lda CONTROL_STYLE
    asl
    asl
    asl                        ; style * 8 pages = style * $0800
    clc
    adc #>STYLE_ROMH
    sta CTRL_SRC_HI
    lda #>RUNTIME_DST
    sta CTRL_DST_HI

    ldx #8
control_copy_page:
    ldy #0
control_copy_byte:
    lda (CTRL_SRC_LO),y
    sta (CTRL_DST_LO),y
    iny
    bne control_copy_byte
    inc CTRL_SRC_HI
    inc CTRL_DST_HI
    dex
    bne control_copy_page

    lda #EF_OFF
    sta EF_CONTROL
control_resume:
    jmp $ffff

.if * > $02f8
    .error "EasyFlash demo control code overlaps control variables at $02F8"
.endif
.fill $0300-*, $ff
