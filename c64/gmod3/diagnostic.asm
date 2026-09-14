; Read-only banking, mapping, IRQ/NMI and timing probe. Independent of players.
; GMOD3=0 builds the identical base timing workload on EasyFlash for comparison.
; Results $3000..$30ff; no physical-cartridge timing claims from VICE.
.weak
GMOD3 = 1
BANK_GROUPS = 8
.endweak
* = $0801
        .word basic_end,10
        .byte $9e
        .text "2061"
        .byte 0
basic_end: .word 0
        jmp start
* = $1000
start:
        sei
        cld
        lda #$37
        sta $01
.if !GMOD3
        lda #$07
        sta $de02
.endif
        lda #0
        sta $d011
        sta $d015
        sta $d01a
        sta $d020
        sta $d021
        ldx #0
clear_results:
        sta $3000,x
        inx
        bne clear_results
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        ldx #0
        ldy #0
check_bank:
        txa
.if GMOD3
        sta $de00,y
        cmp $9fe0              ; immediately consume the newly selected bank
        bne fail_bank
        cmp $de00
        bne fail_bank
        tya
        cmp $de08
        bne fail_bank
.else
        sta $de00
.endif
        txa
        cmp $9fe0
        bne fail_bank
        cmp $9ffc
        bne fail_bank
        eor #$ff
        cmp $9fe2
        bne fail_bank
        tya
        cmp $9fe1
        bne fail_bank
        cmp $9ffd
        bne fail_bank
        eor #$ff
        cmp $9fe3
        bne fail_bank
        cmp $9fff
        bne fail_bank
        inc $3002
        bne bank_counted
        inc $3003
bank_counted:
        inx
.if GMOD3
        bne check_bank
        iny
        cpy #BANK_GROUPS
        bne check_bank
.else
        cpx #64
        bne check_bank
.endif
        lda #1
        sta $3001
        jmp mapping
fail_bank:
        stx $3004
        sty $3005
        lda #1
        jmp failure
mapping:
.if GMOD3
        lda #$35
        sta $01
        lda #$a5
        sta $8000
        lda #$5a
        sta $e000
        lda #$37
        sta $01
        lda #0
        sta $de00
        ldx #0
map_loop:
        lda ports,x
        sta $01
        lda $8000
        sta $3010,x
        lda $e000
        sta $3014,x
        inx
        cpx #3
        bne map_loop
        lda #$40
        sta $de08
        lda $8000
        sta $3013
        lda #0
        sta $de08
        lda #$35
        sta $01
        jsr vector_test
.endif
        jmp prepare_bench
ports: .byte $35,$36,$37

.if GMOD3
vector_test:
        lda #$4c
        sta $0008
        sta $000c
        lda #<nmi
        sta $0009
        lda #>nmi
        sta $000a
        lda #<irq
        sta $000d
        lda #>irq
        sta $000e
        lda #$20
        sta $de08
        lda $fffa
        sta $3018
        lda $fffe
        sta $3019
        lda #$37
        sta $01
        lda $fffa
        sta $301a
        lda $fffe
        sta $301b
        ; Independent CIA1 IRQ and CIA2 NMI while mainline banks ROM.
        lda #$ff
        sta $dc04
        sta $dd04
        lda #3
        sta $dc05
        lda #1
        sta $dd05
        lda #$81
        sta $dc0d
        sta $dd0d
        lda #$11
        sta $dc0e
        sta $dd0e
        ldx #0
        cli
irq_bank_loop:
        txa
        sta $de00
        cmp $9fe0
        bne irq_bank_fail
        inx
        bne irq_no_wrap
        inc $3025
        beq irq_bank_fail      ; bounded failure when NMI delivery never starts
irq_no_wrap:
        lda $3022
        cmp #32
        bcc irq_bank_loop
        jmp stop_timers
irq_bank_fail:
        inc $3024
stop_timers:
        sei
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda #0
        sta $dc0e
        sta $dd0e
        lda $dc0d
        lda $dd0d
        lda #0
        sta $de08
        lda #$35
        sta $01
        rts
irq:
        pha
        lda $dc0d
        inc $3020
        pla
        rti
nmi:
        pha
        lda $dd0d
        inc $3022
        pla
        rti
.endif

prepare_bench:
        lda #$37
        sta $01
        lda #0
        sta $de00
        ldx #0
init_ram_source:
        lda $9e00,x
        sta $6200,x
        inx
        bne init_ram_source
        lda #$03
        sta $dd02
        lda $dd00
        and #$fc
        ora #3
        sta $dd00
        lda #$14
        sta $d018
        lda #8
        sta $d016
        ldx #0
init_screen:
        lda #$20
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x
        lda #1
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $db00,x
        inx
        bne init_screen
        jsr benches
        lda #$1b
        sta $d011
        jsr benches
        ; Same read/copy work with eight overlapping sprite DMA streams.
        ldx #0
init_sprites:
        lda #50
        sta $d001,x
        lda #80
        sta $d000,x
        inx
        inx
        cpx #16
        bne init_sprites
        ldx #7
sprite_pointers:
        lda #$d0
        sta $07f8,x
        dex
        bpl sprite_pointers
        lda #$ff
        sta $d015
        jsr benches
        lda #0
        sta $d015
        lda #$35
        sta $01
        lda #1
        sta $3000
        lda #5
        sta $d020
        ldx #0
show_pass:
        lda pass_text,x
        sta $0400,x
        inx
        cpx #pass_end-pass_text
        bne show_pass
diagnostic_done:
        jmp diagnostic_done
failure:
        sta $3000
        ora #$80
        sta $3000
        lda #2
        sta $d020
diagnostic_failed:
        jmp diagnostic_failed
pass_text:
.if GMOD3
        .byte 7,13,15,4,51,32,2,1,14,11,19,32,15,11,32,32,19,5,5,32,10,19,15,14,32,20,9,13,9,14,7,19
.else
        .byte 5,1,19,25,6,12,1,19,8,32,2,1,14,11,19,32,15,11,32,32,19,5,5,32,10,19,15,14
.endif
pass_end:

; Every timing interval is bracketed by named labels. Monitor stopwatch counts
; include the loop but exclude JSR/RTS and setup. Empty loop is subtracted.
* = $4000
benches:
        jsr sync_raster
        ldy #0
        ldx #0
bench_empty_start:
empty_loop:
        txa
        dex
        bne empty_loop
bench_empty_end:
        nop
        jsr sync_raster
        ldx #0
bench_fixed_start:
fixed_loop:
        txa
        sta $de00
        dex
        bne fixed_loop
bench_fixed_end:
        nop
        jsr sync_raster
.if GMOD3
        ldy #BANK_GROUPS-1
.else
        ldy #0
.endif
        ldx #0
bench_indexed_start:
indexed_loop:
        txa
        sta $de00,y
        dex
        bne indexed_loop
bench_indexed_end:
        nop
        lda #0
        sta $de00
        jsr sync_raster
        ldx #0
bench_read_start:
read_loop:
        lda $9e00,x
        dex
        bne read_loop
bench_read_end:
        nop
        jsr sync_raster
        ldx #0
bench_ram_read_start:
ram_read_loop:
        lda $6200,x
        dex
        bne ram_read_loop
bench_ram_read_end:
        nop
        jsr sync_raster
        ldx #63
bench_copy_start:
copy_loop:
        lda $9e00,x
        sta $6000,x
        lda $9e40,x
        sta $6040,x
        lda $9e80,x
        sta $6080,x
        lda $9ec0,x
        sta $60c0,x
        dex
        bpl copy_loop
bench_copy_end:
        nop
        jsr sync_raster
        ldx #63
bench_ram_copy_start:
ram_copy_loop:
        lda $6200,x
        sta $6000,x
        lda $6240,x
        sta $6040,x
        lda $6280,x
        sta $6080,x
        lda $62c0,x
        sta $60c0,x
        dex
        bpl ram_copy_loop
bench_ram_copy_end:
        nop
        jsr sync_raster
        ldx #0
bench_mapping_start:
mapping_loop:
        txa
        jsr probe_map_on
        jsr probe_map_off
        dex
        bne mapping_loop
bench_mapping_end:
        lda #$37
        sta $01
        rts
; Match the production mapper instruction sequences (including JSR/RTS).
probe_map_on:
        sei
        lda #$37
        sta $01
.if !GMOD3
        lda probe_bank
        sta $de00
        lda #$06
        sta $de02
.endif
        rts
probe_map_off:
.if !GMOD3
        lda #$04
        sta $de02
.endif
        lda #$35
        sta $01
        cli
        nop
        rts
probe_bank: .byte 0
sync_raster:
        lda $d011
        bmi sync_raster
sync_low:
        lda $d011
        bmi sync_low
        lda $d012
        cmp #48
        bne sync_low
        rts
.if * >= $4400
        .error "Diagnostic benchmark exceeds its RAM allocation"
.endif
