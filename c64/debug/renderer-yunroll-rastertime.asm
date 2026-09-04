; -----------------------------------------------------------------------------
; C64-3D-TOOLKIT GENERATED SPINNER - RASTERTIME PROFILER DEBUG VARIANT
; renderer-yunroll.asm
;
; Stock PAL Commodore 64 / 6510, no accelerator.
; Target assembler: 64tass 1.59+.
;
; v0.9 experimental: v0.8 byte chunks plus unrolled Y-major scanline phases.
;
;   1) Full 8-pixel X-major chunks are now BYTE-ORIENTED. A 2 KiB LUT combines
;      all pixels that land in the same VIC-II bitmap byte, so a typical full
;      chunk performs about 3.6 bitmap read/modify/writes instead of 8.
;
;   2) Partial X-major chunks and Y-major lines retain the proven v0.7 path.
;      The generated geometry, hidden-line removal, triple buffering and raster
;      IRQ presentation therefore remain unchanged.
;
; Across the generated 48-frame fast mesh, 27,936 X-major pixels fall into full
; chunks but occupy only 12,545 bitmap bytes: 55.1% fewer bitmap RMW operations
; for that hot subset. This remains vector line rasterisation, not bitmap frames.
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
; DEBUG DERIVATIVE: border is green while host-precomputed vector data is being
; cleared/coloured/rasterised by the 6510 main loop, black while idle/queued.
; This measures the real renderer workload; the production yunroll ASM is not
; conditionally instrumented and therefore pays zero bytes/cycles for this.
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
CHUNK_COUNT = $f6
CHUNK_LEVELS= $f7

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
        jsr init_static_hud
        jsr init_fps_label

        lda #0
        sta frame_index
        sta frame_counter
        sta tick_counter
        sta last_tick
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
        lda #5                      ; green border = renderer CPU busy
        sta $d020
        jsr prepare_render_buffer
.if COLORS_ENABLED
        jsr apply_current_frame_colors
.endif
        jsr draw_current_lines
        lda #0                      ; black border = render work complete
        sta $d020

        ; Remember which angular frame now occupies this physical bitmap.
        ldx render_slot
        lda frame_index
        sta slot_frame,x

        ; Queue the completed buffer and immediately take the free third buffer.
        jsr publish_completed_frame

        inc frame_counter
        inc frame_index
        lda frame_index
        cmp #FRAME_COUNT
        bcc frame_index_ok
        lda #0
        sta frame_index
frame_index_ok:
        jsr maybe_update_fps
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
        inc tick_counter

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
        ; Y already contains the starting y mod 8.  v0.9 patches a computed
        ; jump into the matching unrolled Y-major scanline phase, avoiding
        ; INY/CPY/BCC loop-control on every pixel.
        lda line_ctl_temp
        and #7
        tax
        lda pixel_masks,x
        sta LINE_MASK

        tya
        tax
        lda line_ctl_temp
        bmi del_y_negative
        lda ymp_entry_lo,x
        sta del_y_jump+1
        lda ymp_entry_hi,x
        sta del_y_jump+2
        jmp del_y_ready
del_y_negative:
        lda ymn_entry_lo,x
        sta del_y_jump+1
        lda ymn_entry_hi,x
        sta del_y_jump+2
del_y_ready:
        ldx line_count_temp
del_y_jump:
        jmp $ffff

; -----------------------------------------------------------------------------
; X-major, minor y direction positive.  Eight x masks are fully unrolled.
; Entry can be at any block according to x mod 8.
; -----------------------------------------------------------------------------
xmp0:
        ; v0.8 fast path: once aligned to an 8-pixel X cell, combine all
        ; pixels on each touched scanline into one bitmap-byte OR.
        cpx #8
        bcc xmp0_slow
        jmp xchunk_pos
xmp0_slow:
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
        ; Same byte-combining path for negative minor-Y direction.
        cpx #8
        bcc xmn0_slow
        jmp xchunk_neg
xmn0_slow:
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
; v0.8 full-cell X-major byte combiners.
;
; xchunk_maskN[STEP_BITS] is the complete 8-bit X mask for relative Y level N
; within one aligned 8-pixel X chunk. The generator proves these masks reconstruct
; exactly the same eight pixels as the v0.7 per-pixel step-mask path.
; -----------------------------------------------------------------------------
xchunk_pos:
        stx CHUNK_COUNT
        ldx STEP_BITS
        lda xchunk_levels,x
        sta CHUNK_LEVELS

xchunk_pos_level0:
        lda xchunk_mask0,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more0
        jmp xchunk_pos_after_levels
xchunk_pos_more0:
        iny
        cpy #8
        bcc xchunk_pos_adv0_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv0_nowrap:

xchunk_pos_level1:
        lda xchunk_mask1,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more1
        jmp xchunk_pos_after_levels
xchunk_pos_more1:
        iny
        cpy #8
        bcc xchunk_pos_adv1_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv1_nowrap:

xchunk_pos_level2:
        lda xchunk_mask2,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more2
        jmp xchunk_pos_after_levels
xchunk_pos_more2:
        iny
        cpy #8
        bcc xchunk_pos_adv2_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv2_nowrap:

xchunk_pos_level3:
        lda xchunk_mask3,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more3
        jmp xchunk_pos_after_levels
xchunk_pos_more3:
        iny
        cpy #8
        bcc xchunk_pos_adv3_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv3_nowrap:

xchunk_pos_level4:
        lda xchunk_mask4,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more4
        jmp xchunk_pos_after_levels
xchunk_pos_more4:
        iny
        cpy #8
        bcc xchunk_pos_adv4_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv4_nowrap:

xchunk_pos_level5:
        lda xchunk_mask5,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more5
        jmp xchunk_pos_after_levels
xchunk_pos_more5:
        iny
        cpy #8
        bcc xchunk_pos_adv5_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv5_nowrap:

xchunk_pos_level6:
        lda xchunk_mask6,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_pos_more6
        jmp xchunk_pos_after_levels
xchunk_pos_more6:
        iny
        cpy #8
        bcc xchunk_pos_adv6_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_adv6_nowrap:

xchunk_pos_level7:
        lda xchunk_mask7,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        jmp xchunk_pos_after_levels
xchunk_pos_after_levels:
        ; STEP_BITS bit 0 is the minor-axis move after pixel 7. It changes
        ; the starting Y of the next X cell but contributes no pixel here.
        txa
        and #1
        beq xchunk_pos_no_final_step
        iny
        cpy #8
        bcc xchunk_pos_final_nowrap
        ldy #0
        clc
        lda PTR_LO
        adc #$40
        sta PTR_LO
        lda PTR_HI
        adc #1
        sta PTR_HI
xchunk_pos_final_nowrap:
xchunk_pos_no_final_step:

        ; Dominant X crossed into the next VIC bitmap character cell.
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc xchunk_pos_x_ok
        inc PTR_HI
xchunk_pos_x_ok:

        lda CHUNK_COUNT
        sec
        sbc #8
        tax
        beq xchunk_pos_done

        ; Load the step mask for the next dominant-axis cell.
        sty saved_y
        ldy #0
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne xchunk_pos_stream_ok
        inc STREAM_HI
xchunk_pos_stream_ok:
        ldy saved_y
        jmp xmp0
xchunk_pos_done:
        rts

xchunk_neg:
        stx CHUNK_COUNT
        ldx STEP_BITS
        lda xchunk_levels,x
        sta CHUNK_LEVELS

xchunk_neg_level0:
        lda xchunk_mask0,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more0
        jmp xchunk_neg_after_levels
xchunk_neg_more0:
        dey
        bpl xchunk_neg_adv0_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv0_nowrap:

xchunk_neg_level1:
        lda xchunk_mask1,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more1
        jmp xchunk_neg_after_levels
xchunk_neg_more1:
        dey
        bpl xchunk_neg_adv1_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv1_nowrap:

xchunk_neg_level2:
        lda xchunk_mask2,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more2
        jmp xchunk_neg_after_levels
xchunk_neg_more2:
        dey
        bpl xchunk_neg_adv2_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv2_nowrap:

xchunk_neg_level3:
        lda xchunk_mask3,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more3
        jmp xchunk_neg_after_levels
xchunk_neg_more3:
        dey
        bpl xchunk_neg_adv3_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv3_nowrap:

xchunk_neg_level4:
        lda xchunk_mask4,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more4
        jmp xchunk_neg_after_levels
xchunk_neg_more4:
        dey
        bpl xchunk_neg_adv4_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv4_nowrap:

xchunk_neg_level5:
        lda xchunk_mask5,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more5
        jmp xchunk_neg_after_levels
xchunk_neg_more5:
        dey
        bpl xchunk_neg_adv5_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv5_nowrap:

xchunk_neg_level6:
        lda xchunk_mask6,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        bne xchunk_neg_more6
        jmp xchunk_neg_after_levels
xchunk_neg_more6:
        dey
        bpl xchunk_neg_adv6_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_adv6_nowrap:

xchunk_neg_level7:
        lda xchunk_mask7,x
        ora (PTR_LO),y
        sta (PTR_LO),y
        dec CHUNK_LEVELS
        jmp xchunk_neg_after_levels
xchunk_neg_after_levels:
        ; STEP_BITS bit 0 is the minor-axis move after pixel 7. It changes
        ; the starting Y of the next X cell but contributes no pixel here.
        txa
        and #1
        beq xchunk_neg_no_final_step
        dey
        bpl xchunk_neg_final_nowrap
        ldy #7
        sec
        lda PTR_LO
        sbc #$40
        sta PTR_LO
        lda PTR_HI
        sbc #1
        sta PTR_HI
xchunk_neg_final_nowrap:
xchunk_neg_no_final_step:

        ; Dominant X crossed into the next VIC bitmap character cell.
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc xchunk_neg_x_ok
        inc PTR_HI
xchunk_neg_x_ok:

        lda CHUNK_COUNT
        sec
        sbc #8
        tax
        beq xchunk_neg_done

        ; Load the step mask for the next dominant-axis cell.
        sty saved_y
        ldy #0
        lda (STREAM_LO),y
        sta STEP_BITS
        inc STREAM_LO
        bne xchunk_neg_stream_ok
        inc STREAM_HI
xchunk_neg_stream_ok:
        ldy saved_y
        jmp xmn0
xchunk_neg_done:
        rts

; -----------------------------------------------------------------------------
; v0.9 Y-major unrolled: dominant y positive, minor x positive.
; -----------------------------------------------------------------------------
ymp0:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp0_cont
        rts
ymp0_cont:
        asl STEP_BITS
        bcc ymp0_no_x
        lsr LINE_MASK
        bne ymp0_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp0_no_x
        inc PTR_HI
ymp0_no_x:
        iny
        jmp ymp1

ymp1:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp1_cont
        rts
ymp1_cont:
        asl STEP_BITS
        bcc ymp1_no_x
        lsr LINE_MASK
        bne ymp1_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp1_no_x
        inc PTR_HI
ymp1_no_x:
        iny
        jmp ymp2

ymp2:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp2_cont
        rts
ymp2_cont:
        asl STEP_BITS
        bcc ymp2_no_x
        lsr LINE_MASK
        bne ymp2_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp2_no_x
        inc PTR_HI
ymp2_no_x:
        iny
        jmp ymp3

ymp3:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp3_cont
        rts
ymp3_cont:
        asl STEP_BITS
        bcc ymp3_no_x
        lsr LINE_MASK
        bne ymp3_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp3_no_x
        inc PTR_HI
ymp3_no_x:
        iny
        jmp ymp4

ymp4:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp4_cont
        rts
ymp4_cont:
        asl STEP_BITS
        bcc ymp4_no_x
        lsr LINE_MASK
        bne ymp4_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp4_no_x
        inc PTR_HI
ymp4_no_x:
        iny
        jmp ymp5

ymp5:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp5_cont
        rts
ymp5_cont:
        asl STEP_BITS
        bcc ymp5_no_x
        lsr LINE_MASK
        bne ymp5_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp5_no_x
        inc PTR_HI
ymp5_no_x:
        iny
        jmp ymp6

ymp6:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp6_cont
        rts
ymp6_cont:
        asl STEP_BITS
        bcc ymp6_no_x
        lsr LINE_MASK
        bne ymp6_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp6_no_x
        inc PTR_HI
ymp6_no_x:
        iny
        jmp ymp7

ymp7:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymp7_cont
        rts
ymp7_cont:
        asl STEP_BITS
        bcc ymp7_no_x
        lsr LINE_MASK
        bne ymp7_no_x
        lda #$80
        sta LINE_MASK
        clc
        lda PTR_LO
        adc #8
        sta PTR_LO
        bcc ymp7_no_x
        inc PTR_HI
ymp7_no_x:
        ; y 7 -> 0: advance one VIC bitmap character row (+320).
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
        bne ymp7_mask_ok
        inc STREAM_HI
ymp7_mask_ok:
        jmp ymp0

; -----------------------------------------------------------------------------
; v0.9 Y-major unrolled: dominant y positive, minor x negative.
; -----------------------------------------------------------------------------
ymn0:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn0_cont
        rts
ymn0_cont:
        asl STEP_BITS
        bcc ymn0_no_x
        asl LINE_MASK
        bne ymn0_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn0_no_x
        dec PTR_HI
ymn0_no_x:
        iny
        jmp ymn1

ymn1:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn1_cont
        rts
ymn1_cont:
        asl STEP_BITS
        bcc ymn1_no_x
        asl LINE_MASK
        bne ymn1_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn1_no_x
        dec PTR_HI
ymn1_no_x:
        iny
        jmp ymn2

ymn2:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn2_cont
        rts
ymn2_cont:
        asl STEP_BITS
        bcc ymn2_no_x
        asl LINE_MASK
        bne ymn2_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn2_no_x
        dec PTR_HI
ymn2_no_x:
        iny
        jmp ymn3

ymn3:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn3_cont
        rts
ymn3_cont:
        asl STEP_BITS
        bcc ymn3_no_x
        asl LINE_MASK
        bne ymn3_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn3_no_x
        dec PTR_HI
ymn3_no_x:
        iny
        jmp ymn4

ymn4:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn4_cont
        rts
ymn4_cont:
        asl STEP_BITS
        bcc ymn4_no_x
        asl LINE_MASK
        bne ymn4_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn4_no_x
        dec PTR_HI
ymn4_no_x:
        iny
        jmp ymn5

ymn5:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn5_cont
        rts
ymn5_cont:
        asl STEP_BITS
        bcc ymn5_no_x
        asl LINE_MASK
        bne ymn5_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn5_no_x
        dec PTR_HI
ymn5_no_x:
        iny
        jmp ymn6

ymn6:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn6_cont
        rts
ymn6_cont:
        asl STEP_BITS
        bcc ymn6_no_x
        asl LINE_MASK
        bne ymn6_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn6_no_x
        dec PTR_HI
ymn6_no_x:
        iny
        jmp ymn7

ymn7:
        lda LINE_MASK
        ora (PTR_LO),y
        sta (PTR_LO),y
        dex
        bne ymn7_cont
        rts
ymn7_cont:
        asl STEP_BITS
        bcc ymn7_no_x
        asl LINE_MASK
        bne ymn7_no_x
        lda #$01
        sta LINE_MASK
        sec
        lda PTR_LO
        sbc #8
        sta PTR_LO
        bcs ymn7_no_x
        dec PTR_HI
ymn7_no_x:
        ; y 7 -> 0: advance one VIC bitmap character row (+320).
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
        bne ymn7_mask_ok
        inc STREAM_HI
ymn7_mask_ok:
        jmp ymn0

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

ymp_entry_lo:
        .byte <ymp0,<ymp1,<ymp2,<ymp3,<ymp4,<ymp5,<ymp6,<ymp7
ymp_entry_hi:
        .byte >ymp0,>ymp1,>ymp2,>ymp3,>ymp4,>ymp5,>ymp6,>ymp7
ymn_entry_lo:
        .byte <ymn0,<ymn1,<ymn2,<ymn3,<ymn4,<ymn5,<ymn6,<ymn7
ymn_entry_hi:
        .byte >ymn0,>ymn1,>ymn2,>ymn3,>ymn4,>ymn5,>ymn6,>ymn7

; -----------------------------------------------------------------------------
; Guest-side PAL FPS counter.  Our raster IRQ increments tick_counter at 50 Hz.
; -----------------------------------------------------------------------------
maybe_update_fps:
        lda tick_counter
        sta current_tick
        sec
        sbc last_tick
        cmp #50
        bcc fps_not_yet

        lda current_tick
        sta last_tick
        jsr display_fps
        lda #0
        sta frame_counter
fps_not_yet:
        rts

display_fps:
        lda frame_counter
        ldx #0
fps_hundreds_loop:
        cmp #100
        bcc fps_hundreds_done
        sec
        sbc #100
        inx
        jmp fps_hundreds_loop
fps_hundreds_done:
        stx fps_hundreds
        sta fps_remainder

        lda fps_remainder
        ldx #0
fps_tens_loop:
        cmp #10
        bcc fps_tens_done
        sec
        sbc #10
        inx
        jmp fps_tens_loop
fps_tens_done:
        stx fps_tens
        sta fps_ones

        jsr render_fps_digits
        rts

; Static generated object HUD in bottom-left character row.
; The FPS label occupies cells 32..39, so HUD is capped at 31 cells.
init_static_hud:
        ldx #0
ish_loop:
        lda hud_static_bitmap,x
        sta $3e00,x
        sta $7e00,x
        sta $fe00,x
        inx
        cpx #HUD_STATIC_LEN
        bne ish_loop
        rts

; Same glyphs are kept in BOTH bitmap banks so the label doesn't blink.
init_fps_label:
        ldx #7
ifl_loop:
        lda glyph_f,x
        sta $3f00,x
        sta $7f00,x
        sta $ff00,x
        lda glyph_p,x
        sta $3f08,x
        sta $7f08,x
        sta $ff08,x
        lda glyph_s,x
        sta $3f10,x
        sta $7f10,x
        sta $ff10,x
        lda glyph_colon,x
        sta $3f18,x
        sta $7f18,x
        sta $ff18,x
        lda glyph_blank,x
        sta $3f20,x
        sta $7f20,x
        sta $ff20,x
        lda digit_glyphs,x
        sta $3f28,x
        sta $3f30,x
        sta $3f38,x
        sta $7f28,x
        sta $7f30,x
        sta $7f38,x
        sta $ff28,x
        sta $ff30,x
        sta $ff38,x
        dex
        bpl ifl_loop
        rts

render_fps_digits:
        lda fps_hundreds
        asl a
        asl a
        asl a
        tax
        ldy #0
rfd_hundreds:
        lda digit_glyphs,x
        sta $3f28,y
        sta $7f28,y
        sta $ff28,y
        inx
        iny
        cpy #8
        bne rfd_hundreds

        lda fps_tens
        asl a
        asl a
        asl a
        tax
        ldy #0
rfd_tens:
        lda digit_glyphs,x
        sta $3f30,y
        sta $7f30,y
        sta $ff30,y
        inx
        iny
        cpy #8
        bne rfd_tens

        lda fps_ones
        asl a
        asl a
        asl a
        tax
        ldy #0
rfd_ones:
        lda digit_glyphs,x
        sta $3f38,y
        sta $7f38,y
        sta $ff38,y
        inx
        iny
        cpy #8
        bne rfd_ones
        rts

; -----------------------------------------------------------------------------
; Mutable state / temporaries
; -----------------------------------------------------------------------------
frame_index:            .byte 0
frame_counter:          .byte 0
tick_counter:           .byte 0
last_tick:              .byte 0
current_tick:           .byte 0

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

fps_hundreds:           .byte 0
fps_tens:               .byte 0
fps_ones:               .byte 0
fps_remainder:          .byte 0

pixel_masks:
        .byte $80,$40,$20,$10,$08,$04,$02,$01

; -----------------------------------------------------------------------------
; Tiny 8x8 bitmap font used only by the FPS counter.
; -----------------------------------------------------------------------------
glyph_f:
        .byte $7e,$60,$60,$7c,$60,$60,$60,$00
glyph_p:
        .byte $7c,$66,$66,$7c,$60,$60,$60,$00
glyph_s:
        .byte $3c,$66,$60,$3c,$06,$66,$3c,$00
glyph_colon:
        .byte $00,$18,$18,$00,$00,$18,$18,$00
glyph_blank:
        .byte $00,$00,$00,$00,$00,$00,$00,$00

digit_glyphs:
        .byte $3c,$66,$6e,$76,$66,$66,$3c,$00 ; 0
        .byte $18,$38,$18,$18,$18,$18,$7e,$00 ; 1
        .byte $3c,$66,$06,$0c,$30,$60,$7e,$00 ; 2
        .byte $3c,$66,$06,$1c,$06,$66,$3c,$00 ; 3
        .byte $0c,$1c,$3c,$6c,$7e,$0c,$0c,$00 ; 4
        .byte $7e,$60,$7c,$06,$06,$66,$3c,$00 ; 5
        .byte $1c,$30,$60,$7c,$66,$66,$3c,$00 ; 6
        .byte $7e,$06,$0c,$18,$30,$30,$30,$00 ; 7
        .byte $3c,$66,$66,$3c,$66,$66,$3c,$00 ; 8
        .byte $3c,$66,$66,$3e,$06,$0c,$38,$00 ; 9

renderer_hud_start:
        .include "generated/hud.inc"

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
