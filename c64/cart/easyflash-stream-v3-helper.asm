; V3 copy helpers in $4100-$42ff; dispatch high bytes occupy $4300-$43ff. Included after the existing $4000 colour reset.
.if * > $4100
    .error "colour helper overlaps cart-v3 helper"
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

; At most 256 copied bytes per critical section, including the exact tail.
; Restore RAM IRQ vector and all rendering RAM before re-enabling interrupts.
; The IRQ preserves A/X/Y and never uses STREAM/PTR or changes the cart mapping.
cart_rom_page:
        jsr cart_patch_copy
        sei
        lda #$37
        sta $01
        lda cart_selected_bank
        sta $de00
        lda #$06
        sta $de02
        jsr cart_fast_copy
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
        jsr cart_patch_copy
        jmp cart_fast_copy
cart_patch_copy:
        lda STREAM_LO
        sta cart_copy_load0+1
        sta cart_copy_load1+1
        sta cart_copy_load2+1
        sta cart_copy_load3+1
        lda STREAM_HI
        sta cart_copy_load0+2
        sta cart_copy_load1+2
        sta cart_copy_load2+2
        sta cart_copy_load3+2
        lda PTR_LO
        sta cart_copy_store0+1
        sta cart_copy_store1+1
        sta cart_copy_store2+1
        sta cart_copy_store3+1
        lda PTR_HI
        sta cart_copy_store0+2
        sta cart_copy_store1+2
        sta cart_copy_store2+2
        sta cart_copy_store3+2
        rts
cart_fast_copy:
        ldy #0
        lda cart_copy_count
        bne cart_copy_tail
cart_copy_full:
cart_copy_load0:
        lda $ffff,y
cart_copy_store0:
        sta $ffff,y
        iny
cart_copy_load1:
        lda $ffff,y
cart_copy_store1:
        sta $ffff,y
        iny
cart_copy_load2:
        lda $ffff,y
cart_copy_store2:
        sta $ffff,y
        iny
cart_copy_load3:
        lda $ffff,y
cart_copy_store3:
        sta $ffff,y
        iny
        bne cart_copy_full
        rts
cart_copy_tail:
        ; Reuse the first patched pair through self-modified tail operands.
        lda cart_copy_load0+1
        sta cart_tail_load+1
        lda cart_copy_load0+2
        sta cart_tail_load+2
        lda cart_copy_store0+1
        sta cart_tail_store+1
        lda cart_copy_store0+2
        sta cart_tail_store+2
cart_tail_load:
        lda $ffff,y
cart_tail_store:
        sta $ffff,y
        iny
        cpy cart_copy_count
        bne cart_tail_load
        rts
cart_cache_hi: .byte $50,$54,$58
cart_line_lo: .byte 0
cart_line_hi: .byte 0
cart_pages = $ef
cart_tail: .byte 0
cart_selected_bank: .byte 0
cart_copy_count = $ee
.if * > $4300
    .error "cart helper overlaps v3 dispatch table"
.endif
