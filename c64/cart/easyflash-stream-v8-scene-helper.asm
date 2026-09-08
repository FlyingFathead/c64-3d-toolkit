; V8 copy helpers in $4100-$42ff; dispatch high bytes occupy $4300-$43ff. Included after the existing $4000 colour reset.
.if * > $4100
    .error "colour helper overlaps cart-v8 helper"
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
        jsr scene_select_rom
        ; The recycled slot is already clear. Send its metadata directly
        ; to the slot cache, then stage only the line-count/record stream.
        lda cart_length_lo,x
        sec
        sbc cart_meta_lo,x
        sta cart_line_bytes_lo
        lda cart_length_hi,x
        sbc cart_meta_hi,x
        sta cart_line_bytes_hi
        lda cart_meta_lo,x
        sta cart_tail
        lda cart_meta_hi,x
        sta cart_pages
        ldx render_slot
        lda cart_cache_hi,x
        sta PTR_HI
        lda #0
        sta PTR_LO
        jsr cart_copy_frame_part
        lda #0
        sta PTR_LO
        lda #$a0
        sta PTR_HI
        lda cart_line_bytes_lo
        sta cart_tail
        lda cart_line_bytes_hi
        sta cart_pages
        ; Fall through for the line records; the source was advanced by the
        ; exact metadata length, including an unaligned partial-page tail.
cart_copy_frame_part:
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
        clc
        lda STREAM_LO
        adc cart_tail
        sta STREAM_LO
        bcc cart_fetch_done
        inc STREAM_HI
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
        lda scene_rom_mode
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

; V8 retains four 64-byte sections, one index update per group.
; Source/destination may start at any byte. Patch carries separately.
cart_patch_copy:
        lda STREAM_LO
        sta cart_copy_load0+1
        sta cart_tail_load+1
        lda STREAM_HI
        sta cart_copy_load0+2
        sta cart_tail_load+2
        lda PTR_LO
        sta cart_copy_store0+1
        sta cart_tail_store+1
        lda PTR_HI
        sta cart_copy_store0+2
        sta cart_tail_store+2
        lda cart_copy_count
        beq cart_patch_full
        rts
cart_patch_full:
        clc
        lda STREAM_LO
        adc #64
        sta cart_copy_load1+1
        lda STREAM_HI
        adc #0
        sta cart_copy_load1+2
        clc
        lda STREAM_LO
        adc #128
        sta cart_copy_load2+1
        lda STREAM_HI
        adc #0
        sta cart_copy_load2+2
        clc
        lda STREAM_LO
        adc #192
        sta cart_copy_load3+1
        lda STREAM_HI
        adc #0
        sta cart_copy_load3+2
        clc
        lda PTR_LO
        adc #64
        sta cart_copy_store1+1
        lda PTR_HI
        adc #0
        sta cart_copy_store1+2
        clc
        lda PTR_LO
        adc #128
        sta cart_copy_store2+1
        lda PTR_HI
        adc #0
        sta cart_copy_store2+2
        clc
        lda PTR_LO
        adc #192
        sta cart_copy_store3+1
        lda PTR_HI
        adc #0
        sta cart_copy_store3+2
        rts
cart_fast_copy:
        ldy #0
        lda cart_copy_count
        bne cart_tail_load
cart_copy_full:
cart_copy_load0:
        lda $ffff,y
cart_copy_store0:
        sta $ffff,y
cart_copy_load1:
        lda $ffff,y
cart_copy_store1:
        sta $ffff,y
cart_copy_load2:
        lda $ffff,y
cart_copy_store2:
        sta $ffff,y
cart_copy_load3:
        lda $ffff,y
cart_copy_store3:
        sta $ffff,y
        iny
        cpy #64
        bne cart_copy_full
        rts
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
cart_line_hi: .byte $a0
cart_line_bytes_lo: .byte 0
cart_line_bytes_hi: .byte 0
cart_pages = $ef
cart_tail: .byte 0
cart_selected_bank: .byte 0
cart_copy_count = $ee
.if V8_BYTE_SPANS
; Independent sparse bitmap byte spans, after recycling the target slot.
v8_draw_bytes:
        and #$7f
        sta lines_remaining+1
        ora lines_remaining
        beq v8_bytes_done
        lda lines_remaining
        beq v8_batches_ready
        inc lines_remaining+1
v8_batches_ready:
        lda #2
        jsr v8_advance
v8_span:
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
        sta line_count_temp
        lda #3
        jsr v8_advance
        ldy #0
v8_byte:
        lda (STREAM_LO),y
        sta (PTR_LO),y
        iny
        cpy line_count_temp
        bne v8_byte
        tya
        jsr v8_advance
        dec lines_remaining
        bne v8_span
        dec lines_remaining+1
        bne v8_span
v8_bytes_done:
        rts
v8_advance:
        clc
        adc STREAM_LO
        sta STREAM_LO
        bcc v8_advanced
        inc STREAM_HI
v8_advanced:
        rts
.endif


.if * > $4300
    .error "cart helper overlaps v8 dispatch table"
.endif

; This extension is loaded by the scene-only bootstrap. The V5 LUTs,
; buffers, metadata and all rasterisation kernels retain their addresses.
* = $5c00
scene_select_rom:
        cmp #$a0
        lda #$06
        bcc scene_rom_selected
        lda #$07
scene_rom_selected:
        sta scene_rom_mode
        rts

scene_advance_frame:
        inc frame_index
        bne scene_compare_end
        inc frame_index_hi
scene_compare_end:
        lda frame_index_hi
        cmp #>FRAME_COUNT
        bne scene_advance_done
        lda frame_index
        cmp #<FRAME_COUNT
        bne scene_advance_done
        lda #0
        sta frame_index
        sta frame_index_hi
scene_advance_done:
        rts

; One 1792-byte directory page handles 256 frames. Four pages per ROMH
; bank, banks 1 and 2 reserved. Fetch only at startup, page changes or wrap.
scene_load_directory:
        lda frame_index_hi
        cmp scene_directory_page
        beq scene_directory_done
        sta scene_directory_page
        lsr a
        lsr a
        clc
        adc #1
        sta cart_selected_bank
        lda frame_index_hi
        and #3
        tax
        lda scene_directory_source_hi,x
        sta STREAM_HI
        lda #0
        sta STREAM_LO
        sta PTR_LO
        sta cart_copy_count
        lda #$48
        sta PTR_HI
        lda #$07
        sta scene_rom_mode
        sta scene_pages
scene_directory_copy:
        jsr cart_rom_page
        inc STREAM_HI
        inc PTR_HI
        dec scene_pages
        bne scene_directory_copy
scene_directory_done:
        rts
scene_directory_source_hi: .byte $a0,$a7,$ae,$b5
frame_index_hi: .byte 0
scene_directory_page: .byte $ff
scene_rom_mode: .byte $06
scene_pages: .byte 0
scene_hold: .byte 0
.if * > $6000
.error "scene extension overlaps bitmap 1"
.endif
