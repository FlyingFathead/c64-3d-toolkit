; Cold helpers in $4100-$43ff. Included after the existing $4000 colour reset.
.if * > $4100
    .error "colour helper overlaps cart-v2 helper"
.endif
* = $4100
cart_fetch_frame:
        ldx frame_index
        lda cart_bank,x
        sta cart_selected_bank
        lda cart_source_lo,x
        sta STREAM_LO
        lda cart_source_hi,x
        sta STREAM_HI
        lda #0
        sta PTR_LO
        lda #$a0
        sta PTR_HI
        lda cart_length_lo,x
        sta cart_tail
        lda cart_length_hi,x
        sta cart_pages
        lda cart_meta_lo,x
        sta cart_line_lo
        lda cart_meta_hi,x
        clc
        adc #$a0
        sta cart_line_hi
cart_fetch_pages:
        lda cart_pages
        beq cart_fetch_tail
        lda #0
        sta cart_copy_count
        jsr cart_rom_page
        inc STREAM_HI
        inc PTR_HI
        dec cart_pages
        jmp cart_fetch_pages
cart_fetch_tail:
        lda cart_tail
        beq cart_fetch_done
        sta cart_copy_count
        jsr cart_rom_page
cart_fetch_done:
        rts

; <=256 bytes per critical section, ~4.5k cycles (< one PAL raster period).
; Restore RAM IRQ vector and all rendering RAM before re-enabling interrupts.
; The IRQ preserves A/X/Y and never uses STREAM/PTR or changes the cart mapping.
cart_rom_page:
        sei
        lda #$37
        sta $01
        lda cart_selected_bank
        sta $de00
        lda #$06
        sta $de02
        ldy #0
        lda cart_copy_count
        bne cart_rom_byte
; Four-byte unroll avoids the per-byte count compare on complete pages.
cart_rom_full:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        bne cart_rom_full
        jmp cart_rom_restore
cart_rom_byte:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        cpy cart_copy_count
        bne cart_rom_byte
cart_rom_restore:
        lda #$04
        sta $de02
        lda #$35
        sta $01
        cli
        nop
        rts

cart_old_metadata_ptr:
        ldx render_slot
        lda #0
        sta STREAM_LO
        lda cart_cache_hi,x
        sta STREAM_HI
        rts

; Save metadata belonging to the frame about to occupy render_slot. The other
; two slots' copies must survive: their bitmaps can remain queued/displayed.
cart_cache_metadata:
        ldx frame_index
        lda cart_meta_hi,x
        sta cart_pages
        lda cart_meta_lo,x
        sta cart_tail
        ldx render_slot
        lda cart_cache_hi,x
        sta PTR_HI
        lda #0
        sta PTR_LO
        sta STREAM_LO
        lda #$a0
        sta STREAM_HI
cart_cache_pages:
        lda cart_pages
        beq cart_cache_tail
        lda #0
        sta cart_copy_count
        jsr cart_ram_page
        inc STREAM_HI
        inc PTR_HI
        dec cart_pages
        jmp cart_cache_pages
cart_cache_tail:
        lda cart_tail
        beq cart_cache_done
        sta cart_copy_count
        jsr cart_ram_page
cart_cache_done:
        rts
cart_ram_page:
        ldy #0
        lda cart_copy_count
        bne cart_ram_byte
cart_ram_full:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        bne cart_ram_full
        rts
cart_ram_byte:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        cpy cart_copy_count
        bne cart_ram_byte
        rts
cart_cache_hi: .byte $50,$54,$58
cart_line_lo: .byte 0
cart_line_hi: .byte 0
cart_pages: .byte 0
cart_tail: .byte 0
cart_selected_bank: .byte 0
cart_copy_count: .byte 0
.if * > $4400
    .error "cart helper overlaps screen RAM"
.endif
