; -----------------------------------------------------------------------------
; C64-3D-TOOLKIT GENERATED SPINNER - NO TEXT OVERLAY VARIANT
; renderer-step.asm
;
; Stock PAL Commodore 64 / 6510, no accelerator.
; Target assembler: 64tass 1.59+.
;
; v0.7.0 attacks two remaining costs measured after v0.6.0 reached 9-12 FPS:
;
;   1) DDA arithmetic in every line pixel is replaced by precomputed 1-bit
;      minor-axis step decisions.  The C64 still plots every actual pixel; the
;      tables only tell the hot loop whether the minor coordinate moves.
;
;   2) The renderer is now triple-buffered. A 50 Hz raster IRQ flips a completed
;      bitmap while the CPU immediately starts drawing into a third free bitmap,
;      eliminating the synchronous wait-for-vblank at the end of every frame.
;
; Additional change: clear tables now split holes into contiguous touched-cell
; runs, reducing the average clear from ~1650 to ~1085 bytes/frame.
;
; This remains vector/raster data, NOT pre-rendered bitmap animation.  Each line
; record contains a start address, pixel count, orientation bits, and packed
; minor-axis decisions. The 6510 performs every bitmap OR itself.
;
; Generated variable-length line record:
;   0: start character-cell bitmap offset low
;   1: start character-cell bitmap offset high
;   2: number of pixels in this visible run (2..127)
;   3: control byte:
;        bits 0..2 = x mod 8
;        bits 3..5 = y mod 8
;        bit 6     = 0 x-major, 1 y-major
;        bit 7     = minor axis negative
;   4..: MSB-first minor-axis step masks, one per dominant-axis 8-pixel cell.
;
; The Python generator decodes every record back to pixels and rejects any
; mismatch before writing the include file.
;
; DERIVATIVE BUILD: removes HUD/FPS code entirely. Production renderer source
; remains untouched; this variant carries no overlay runtime/code-size cost.
;
; -----------------------------------------------------------------------------

FRAME_COUNT = 48
SCREEN_COLOR = $10              ; high nibble=foreground, low nibble=background
COLORS_ENABLED = 0              ; 1 adds generated per-cell source colours

SCREEN0     = $0400
BITMAP0     = $2000
SCREEN1     = $4400
BITMAP1     = $6000
SCREEN2     = $c800
BITMAP2     = $e000

; Hot zero-page state. KERNAL is banked out after startup and CIA IRQs are
; disabled, so this standalone demo owns this workspace.
STREAM_LO   = $f0
STREAM_HI   = $f1
PTR_LO      = $f2
PTR_HI      = $f3
STEP_BITS   = $f4
LINE_MASK   = $f5

* = $0801

; BASIC line: 10 SYS2061
        .word basic_end
        .word 10
        .byte $9e
        .text "2061"
        .byte 0
basic_end:
        .word 0

; -----------------------------------------------------------------------------
; Entry point at $080d / decimal 2061
; -----------------------------------------------------------------------------
start:
        sei
        cld

        lda #1
        sta $cc                     ; suppress BASIC cursor activity

        lda #0
        sta $d020
        sta $d021

        ; $35: RAM under BASIC + KERNAL, I/O still visible.  This gives the
        ; renderer unrestricted access to the third bitmap at $e000.
        lda #$35
        sta $01

        ; Disable both CIA interrupt sources.  v0.7 supplies its own 50 Hz
        ; raster IRQ, so it no longer depends on the KERNAL jiffy IRQ.
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d

        ; VIC bank 0 initially, screen=$0400 and bitmap=$2000.
        lda $dd00
        and #$fc
        ora #$03
        sta $dd00

        lda #$18
        sta $d018

        lda $d011
        and #$7f                    ; raster compare < 256
        ora #$20                    ; hires bitmap mode
        sta $d011

        lda $d016
        and #$ef                    ; no multicolour
        sta $d016

        ; Per-build foreground/background colour in every bitmap cell, all 3 banks.
        lda #SCREEN_COLOR
        ldx #0
init_screen_colours:
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        sta $4400,x
        sta $4500,x
        sta $4600,x
        sta $4700,x
        sta $c800,x
        sta $c900,x
        sta $ca00,x
        sta $cb00,x
        inx
        bne init_screen_colours

        jsr clear_bitmap0_all
        jsr clear_bitmap1_all
        jsr clear_bitmap2_all

        lda #0
        sta frame_index
        sta display_slot

        lda #1
        sta render_slot
        lda #2
        sta free_slot
        lda #$ff
        sta ready_slot
        sta slot_frame+0
        sta slot_frame+1
        sta slot_frame+2

        ; Raster IRQ at line 250.  It flips a completed buffer if one is queued,
        ; but the main renderer never waits for vblank unless it has outrun the
        ; display queue (which at ~10+ FPS vs 50 Hz should be essentially never).
        lda #250
        sta $d012
        lda #<raster_irq
        sta $fffe
        lda #>raster_irq
        sta $ffff
        lda #$0f
        sta $d019
        lda #$01
        sta $d01a

        cli

main_loop:
frame_begin:
        jsr prepare_render_buffer
.if COLORS_ENABLED
        jsr apply_current_frame_colors
.endif
        jsr draw_current_lines

        ; Remember which angular frame now occupies this physical bitmap.
        ldx render_slot
        lda frame_index
        sta slot_frame,x

        ; Queue the completed buffer and immediately take the free third buffer.
        jsr publish_completed_frame

        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc frame_index_ok
        lda #0
        sta frame_index
frame_index_ok:
frame_end:
        jmp main_loop

; -----------------------------------------------------------------------------
; Triple-buffer producer/consumer handoff.
; -----------------------------------------------------------------------------
publish_completed_frame:
publish_wait:
        lda ready_slot
        cmp #$ff
        bne publish_wait
        lda free_slot
        cmp #$ff
        beq publish_wait

        sei
        ldx render_slot
        stx ready_slot
        ldx free_slot
        stx render_slot
        lda #$ff
        sta free_slot
        cli
        rts

; -----------------------------------------------------------------------------
; 50 Hz raster IRQ.  No KERNAL is mapped in, so this owns the hardware vector.
; It never touches the renderer's zero-page workspace.
; -----------------------------------------------------------------------------
raster_irq:
        pha
        txa
        pha
        tya
        pha

        lda #$01
        sta $d019                    ; acknowledge raster IRQ

        lda ready_slot
        cmp #$ff
        beq irq_no_flip
        tax

        lda display_slot
        sta free_slot
        stx display_slot

        lda $dd00
        and #$fc
        ora vic_bank_bits,x
        sta $dd00
        lda vic_d018_values,x
        sta $d018

        lda #$ff
        sta ready_slot

irq_no_flip:
        pla
        tay
        pla
        tax
        pla
        rti

vic_bank_bits:
        .byte $03,$02,$00            ; slots 0,1,2 -> VIC banks 0,1,3
vic_d018_values:
        .byte $18,$18,$28            ; screen $0400/$4400/$c800, bitmap +$2000

; -----------------------------------------------------------------------------
; Prepare the current render bitmap. Each slot remembers the angular frame it
; still contains, so we clear only the character cells touched by that old frame.
; -----------------------------------------------------------------------------
prepare_render_buffer:
        ldx render_slot
        lda bitmap_base_hi,x
        sta draw_base_hi
        lda slot_frame,x
        cmp #$ff
        beq prb_done
        tax
.if COLORS_ENABLED
        stx color_old_frame_temp
.endif
        jsr clear_old_frame_spans
.if COLORS_ENABLED
        ; Screen RAM is triple-buffered alongside the bitmaps. Restore the old
        ; frame's material cells before applying the new frame's colours.
        ldx color_old_frame_temp
        jsr reset_old_frame_colors
.endif
prb_done:
        rts

bitmap_base_hi:
        .byte $20,$60,$e0

clear_old_frame_spans:
        lda frame_clear_ptr_lo,x
        sta STREAM_LO
        lda frame_clear_ptr_hi,x
        sta STREAM_HI

        ldy #0
        lda (STREAM_LO),y
        sta clear_spans_remaining
        beq cofs_done

        inc STREAM_LO
        bne cofs_span
        inc STREAM_HI

cofs_span:
        ldy #0
        lda (STREAM_LO),y
        sta PTR_LO
        iny
        lda (STREAM_LO),y
        clc
        adc draw_base_hi
        sta PTR_HI
        iny
        lda (STREAM_LO),y
        sta clear_cells_temp

        ; Advance span stream before using X/Y for the clear itself.
        clc
        lda STREAM_LO
        adc #3
        sta STREAM_LO
        bcc cofs_stream_ok
        inc STREAM_HI
cofs_stream_ok:

        ; Each character cell contributes eight contiguous bitmap bytes.
        ; Unroll those eight stores: one DEX/BNE per cell, not per byte.
        lda #0
        ldx clear_cells_temp
        ldy #0
cofs_cell:
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        sta (PTR_LO),y
        iny
        dex
        bne cofs_cell

        dec clear_spans_remaining
        bne cofs_span
cofs_done:
        rts

.if COLORS_ENABLED
; Apply the current frame's host-resolved hires colours to the screen RAM paired
; with the render bitmap. RGB/MTL/SVG work is already gone: each table entry is
; just screen offset, cell count, and a ready-to-store VIC-II screen byte.
apply_current_frame_colors:
        ldx frame_index
        lda frame_clear_ptr_lo,x
        sta STREAM_LO
        lda frame_clear_ptr_hi,x
        sta STREAM_HI

        ; Skip the old-frame clear list: one count byte plus 3 bytes per span.
        ldy #0
        lda (STREAM_LO),y
        sta color_skip_temp
        inc STREAM_LO
        bne acfc_skip_test
        inc STREAM_HI
acfc_skip_test:
        lda color_skip_temp
        beq acfc_read_count
acfc_skip_span:
        clc
        lda STREAM_LO
        adc #3
        sta STREAM_LO
        bcc acfc_skip_ok
        inc STREAM_HI
acfc_skip_ok:
        dec color_skip_temp
        bne acfc_skip_span

acfc_read_count:
        ldy #0
        lda (STREAM_LO),y
        sta color_spans_remaining
        beq acfc_done
        inc STREAM_LO
        bne acfc_count_advanced
        inc STREAM_HI
acfc_count_advanced:
        ldx render_slot
        lda screen_base_hi,x
        sta color_screen_base_hi

acfc_span:
        ldy #0
        lda (STREAM_LO),y
        sta PTR_LO
        iny
        lda (STREAM_LO),y
        clc
        adc color_screen_base_hi
        sta PTR_HI
        iny
        lda (STREAM_LO),y
        sta color_cells_temp
        iny
        lda (STREAM_LO),y
        sta color_value_temp

        clc
        lda STREAM_LO
        adc #4
        sta STREAM_LO
        bcc acfc_stream_ok
        inc STREAM_HI
acfc_stream_ok:
        ldy #0
        ldx color_cells_temp
        lda color_value_temp
acfc_store:
        sta (PTR_LO),y
        iny
        dex
        bne acfc_store

        dec color_spans_remaining
        bne acfc_span
acfc_done:
        rts

screen_base_hi:
        .byte $04,$44,$c8
.endif

; Startup-only complete bitmap clears.
clear_bitmap0_all:
        lda #0
        sta PTR_LO
        lda #$20
        sta PTR_HI
        ldx #32
        lda #0
cb0_page:
        ldy #0
cb0_byte:
        sta (PTR_LO),y
        iny
        bne cb0_byte
        inc PTR_HI
        dex
        bne cb0_page
        rts

clear_bitmap1_all:
        lda #0
        sta PTR_LO
        lda #$60
        sta PTR_HI
        ldx #32
        lda #0
cb1_page:
        ldy #0
cb1_byte:
        sta (PTR_LO),y
        iny
        bne cb1_byte
        inc PTR_HI
        dex
        bne cb1_page
        rts

clear_bitmap2_all:
        lda #0
        sta PTR_LO
        lda #$e0
        sta PTR_HI
        ldx #32
        lda #0
cb2_page:
        ldy #0
cb2_byte:
        sta (PTR_LO),y
        iny
        bne cb2_byte
        inc PTR_HI
        dex
        bne cb2_page
        rts

; -----------------------------------------------------------------------------
; Stream pre-clipped vector runs with precomputed minor-axis step masks.
; -----------------------------------------------------------------------------
draw_current_lines:
        ldx frame_index
        lda frame_line_ptr_lo,x
        sta STREAM_LO
        lda frame_line_ptr_hi,x
        sta STREAM_HI

        ldy #0
        lda (STREAM_LO),y
        sta lines_remaining
        beq dcl_done

        inc STREAM_LO
        bne dcl_loop
        inc STREAM_HI

dcl_loop:
        ldy #0
        lda (STREAM_LO),y           ; start character-cell offset low
        sta PTR_LO
        iny
        lda (STREAM_LO),y           ; start character-cell offset high
        clc
        adc draw_base_hi
        sta PTR_HI
        iny
        lda (STREAM_LO),y           ; pixel count
        sta line_count_temp
        iny
        lda (STREAM_LO),y           ; packed x/y mods + axis/direction
        sta line_ctl_temp

        ; Advance to the first precomputed minor-step mask.  The line routine
        ; consumes subsequent mask bytes as its dominant coordinate crosses
        ; 8-pixel character boundaries.  When it returns, STREAM therefore
        ; already points at the next variable-length record.
        clc
        lda STREAM_LO
        adc #4
        sta STREAM_LO
        bcc dcl_header_ok
        inc STREAM_HI
dcl_header_ok:
        ldy #0
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne dcl_first_mask_ok
        inc STREAM_HI
dcl_first_mask_ok:
        jsr draw_encoded_line

        dec lines_remaining
        bne dcl_loop

dcl_done:
        rts

; -----------------------------------------------------------------------------
; Dispatch one encoded line.
; -----------------------------------------------------------------------------
draw_encoded_line:
        ; Y = starting y mod 8.
        lda line_ctl_temp
        lsr a
        lsr a
        lsr a
        and #7
        tay

        lda line_ctl_temp
        and #$40
        bne del_y_major

        ; X-major. Patch an Elite-style computed JMP into the correct one of
        ; eight unrolled pixel-mask positions.
        lda line_ctl_temp
        and #7
        tax

        lda line_ctl_temp
        bmi del_x_negative

        lda xmp_entry_lo,x
        sta del_x_jump+1
        lda xmp_entry_hi,x
        sta del_x_jump+2
        jmp del_x_ready

del_x_negative:
        lda xmn_entry_lo,x
        sta del_x_jump+1
        lda xmn_entry_hi,x
        sta del_x_jump+2

del_x_ready:
        ldx line_count_temp

del_x_jump:
        jmp $ffff                   ; self-modified to xmp0..7 or xmn0..7

del_y_major:
        lda line_ctl_temp
        and #7
        tax
        lda pixel_masks,x
        sta LINE_MASK
        ldx line_count_temp

        lda line_ctl_temp
        bpl del_y_positive
        jmp ymajor_xminus
del_y_positive:
        jmp ymajor_xplus

; -----------------------------------------------------------------------------
; X-major, minor y direction positive.  Eight x masks are fully unrolled.
; Entry can be at any block according to x mod 8.
; -----------------------------------------------------------------------------
xmp0:
        lda #$80
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp0_cont
        rts
xmp0_cont:
        asl STEP_BITS
        bcc xmp0_no_minor
        iny
        cpy #8
        bcc xmp0_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp0_minor_done:
        clc
xmp0_no_minor:

xmp1:
        lda #$40
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp1_cont
        rts
xmp1_cont:
        asl STEP_BITS
        bcc xmp1_no_minor
        iny
        cpy #8
        bcc xmp1_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp1_minor_done:
        clc
xmp1_no_minor:

xmp2:
        lda #$20
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp2_cont
        rts
xmp2_cont:
        asl STEP_BITS
        bcc xmp2_no_minor
        iny
        cpy #8
        bcc xmp2_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp2_minor_done:
        clc
xmp2_no_minor:

xmp3:
        lda #$10
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp3_cont
        rts
xmp3_cont:
        asl STEP_BITS
        bcc xmp3_no_minor
        iny
        cpy #8
        bcc xmp3_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp3_minor_done:
        clc
xmp3_no_minor:

xmp4:
        lda #$08
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp4_cont
        rts
xmp4_cont:
        asl STEP_BITS
        bcc xmp4_no_minor
        iny
        cpy #8
        bcc xmp4_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp4_minor_done:
        clc
xmp4_no_minor:

xmp5:
        lda #$04
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp5_cont
        rts
xmp5_cont:
        asl STEP_BITS
        bcc xmp5_no_minor
        iny
        cpy #8
        bcc xmp5_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp5_minor_done:
        clc
xmp5_no_minor:

xmp6:
        lda #$02
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp6_cont
        rts
xmp6_cont:
        asl STEP_BITS
        bcc xmp6_no_minor
        iny
        cpy #8
        bcc xmp6_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp6_minor_done:
        clc
xmp6_no_minor:

xmp7:
        lda #$01
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmp7_cont
        rts
xmp7_cont:
        asl STEP_BITS
        bcc xmp7_no_minor
        iny
        cpy #8
        bcc xmp7_minor_done
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xmp7_minor_done:
        clc
xmp7_no_minor:
        ; x crossed an 8-pixel character boundary: +8 bytes
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc xmp7_xbyte_ok
        inc PTR_HI
xmp7_xbyte_ok:
        sty saved_y
        ldy #0
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne xmp7_mask_ok
        inc STREAM_HI
xmp7_mask_ok:
        ldy saved_y
        jmp xmp0

; -----------------------------------------------------------------------------
; X-major, minor y direction negative.
; -----------------------------------------------------------------------------
xmn0:
        lda #$80
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn0_cont
        rts
xmn0_cont:
        asl STEP_BITS
        bcc xmn0_no_minor
        dey
        bpl xmn0_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn0_minor_done:
        clc
xmn0_no_minor:

xmn1:
        lda #$40
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn1_cont
        rts
xmn1_cont:
        asl STEP_BITS
        bcc xmn1_no_minor
        dey
        bpl xmn1_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn1_minor_done:
        clc
xmn1_no_minor:

xmn2:
        lda #$20
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn2_cont
        rts
xmn2_cont:
        asl STEP_BITS
        bcc xmn2_no_minor
        dey
        bpl xmn2_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn2_minor_done:
        clc
xmn2_no_minor:

xmn3:
        lda #$10
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn3_cont
        rts
xmn3_cont:
        asl STEP_BITS
        bcc xmn3_no_minor
        dey
        bpl xmn3_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn3_minor_done:
        clc
xmn3_no_minor:

xmn4:
        lda #$08
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn4_cont
        rts
xmn4_cont:
        asl STEP_BITS
        bcc xmn4_no_minor
        dey
        bpl xmn4_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn4_minor_done:
        clc
xmn4_no_minor:

xmn5:
        lda #$04
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn5_cont
        rts
xmn5_cont:
        asl STEP_BITS
        bcc xmn5_no_minor
        dey
        bpl xmn5_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn5_minor_done:
        clc
xmn5_no_minor:

xmn6:
        lda #$02
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn6_cont
        rts
xmn6_cont:
        asl STEP_BITS
        bcc xmn6_no_minor
        dey
        bpl xmn6_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn6_minor_done:
        clc
xmn6_no_minor:

xmn7:
        lda #$01
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne xmn7_cont
        rts
xmn7_cont:
        asl STEP_BITS
        bcc xmn7_no_minor
        dey
        bpl xmn7_minor_done
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xmn7_minor_done:
        clc
xmn7_no_minor:
        ; x crossed an 8-pixel character boundary: +8 bytes
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc xmn7_xbyte_ok
        inc PTR_HI
xmn7_xbyte_ok:
        sty saved_y
        ldy #0
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne xmn7_mask_ok
        inc STREAM_HI
xmn7_mask_ok:
        ldy saved_y
        jmp xmn0

; -----------------------------------------------------------------------------
; Y-major, dominant y positive, minor x positive.
; -----------------------------------------------------------------------------
ymajor_xplus:
ymp_loop:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp_continue
        rts

ymp_continue:
        asl STEP_BITS
        bcc ymp_no_x_step

        ; x++
        lsr LINE_MASK
        bne ymp_x_step_done
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp_x_step_done
        inc PTR_HI
ymp_x_step_done:
        clc

ymp_no_x_step:
        ; dominant y++
        iny
        cpy #8
        bcc ymp_loop

        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne ymp_mask_ok
        inc STREAM_HI
ymp_mask_ok:
        jmp ymp_loop

; -----------------------------------------------------------------------------
; Y-major, dominant y positive, minor x negative.
; -----------------------------------------------------------------------------
ymajor_xminus:
ymn_loop:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn_continue
        rts

ymn_continue:
        asl STEP_BITS
        bcc ymn_no_x_step

        ; x--
        asl LINE_MASK
        bne ymn_x_step_done
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn_x_step_done
        dec PTR_HI
ymn_x_step_done:
        clc

ymn_no_x_step:
        ; dominant y++
        iny
        cpy #8
        bcc ymn_loop

        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne ymn_mask_ok
        inc STREAM_HI
ymn_mask_ok:
        jmp ymn_loop

; -----------------------------------------------------------------------------
; Entry address tables for the self-modified x-major JMP.
; -----------------------------------------------------------------------------
xmp_entry_lo:
        .byte <xmp0,<xmp1,<xmp2,<xmp3,<xmp4,<xmp5,<xmp6,<xmp7
xmp_entry_hi:
        .byte >xmp0,>xmp1,>xmp2,>xmp3,>xmp4,>xmp5,>xmp6,>xmp7
xmn_entry_lo:
        .byte <xmn0,<xmn1,<xmn2,<xmn3,<xmn4,<xmn5,<xmn6,<xmn7
xmn_entry_hi:
        .byte >xmn0,>xmn1,>xmn2,>xmn3,>xmn4,>xmn5,>xmn6,>xmn7

; -----------------------------------------------------------------------------
; Text overlay/FPS routines intentionally absent in this derivative.
; -----------------------------------------------------------------------------

; -----------------------------------------------------------------------------
; Mutable state / temporaries
; -----------------------------------------------------------------------------
frame_index:            .byte 0

display_slot:           .byte 0
render_slot:            .byte 1
free_slot:              .byte 2
ready_slot:             .byte $ff
slot_frame:             .byte $ff,$ff,$ff
draw_base_hi:           .byte $60
saved_y:                .byte 0

clear_spans_remaining:  .byte 0
clear_cells_temp:       .byte 0

lines_remaining:        .byte 0
line_count_temp:        .byte 0
line_ctl_temp:          .byte 0

.if COLORS_ENABLED
color_skip_temp:        .byte 0
color_spans_remaining:  .byte 0
color_screen_base_hi:   .byte 0
color_cells_temp:       .byte 0
color_value_temp:       .byte 0
color_old_frame_temp:   .byte 0
.endif


pixel_masks:
        .byte $80,$40,$20,$10,$08,$04,$02,$01

; -----------------------------------------------------------------------------
renderer_no_overlay_end:
; No HUD/font data in this derivative.

.if COLORS_ENABLED
; Cold-path helper in the unused $4000-$43ff gap between bitmap #0 and screen
; RAM #1. X is the old angular frame stored in the render slot being recycled.
* = $4000
reset_old_frame_colors:
        lda frame_clear_ptr_lo,x
        sta STREAM_LO
        lda frame_clear_ptr_hi,x
        sta STREAM_HI

        ; Skip the old frame's bitmap-clear list (count + 3 bytes per span).
        ldy #0
        lda (STREAM_LO),y
        sta color_skip_temp
        inc STREAM_LO
        bne rofc_skip_test
        inc STREAM_HI
rofc_skip_test:
        lda color_skip_temp
        beq rofc_read_count
rofc_skip_span:
        clc
        lda STREAM_LO
        adc #3
        sta STREAM_LO
        bcc rofc_skip_ok
        inc STREAM_HI
rofc_skip_ok:
        dec color_skip_temp
        bne rofc_skip_span

rofc_read_count:
        ldy #0
        lda (STREAM_LO),y
        sta color_spans_remaining
        beq rofc_done
        inc STREAM_LO
        bne rofc_count_advanced
        inc STREAM_HI
rofc_count_advanced:
        ldx render_slot
        lda screen_base_hi,x
        sta color_screen_base_hi

rofc_span:
        ldy #0
        lda (STREAM_LO),y
        sta PTR_LO
        iny
        lda (STREAM_LO),y
        clc
        adc color_screen_base_hi
        sta PTR_HI
        iny
        lda (STREAM_LO),y
        sta color_cells_temp

        ; Four bytes per source span; the fourth is the old colour value and
        ; can be skipped because every cell is restored to SCREEN_COLOR.
        clc
        lda STREAM_LO
        adc #4
        sta STREAM_LO
        bcc rofc_stream_ok
        inc STREAM_HI
rofc_stream_ok:
        ldy #0
        ldx color_cells_temp
        lda #SCREEN_COLOR
rofc_store:
        sta (PTR_LO),y
        iny
        dex
        bne rofc_store

        dec color_spans_remaining
        bne rofc_span
rofc_done:
        rts
.endif

        .include "generated/tables.inc"
