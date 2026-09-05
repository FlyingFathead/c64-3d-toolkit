; Uniform-renderer EasyFlash demo menu with a buffered scrolling viewport.
;
; This is an integration bridge, not the final yunroll-cart streamer.  It lets
; one EasyFlash CRT hold and launch several existing c64-3d-toolkit PRGs so the
; cartridge path is immediately useful while the true frame/table stream format
; is developed. RESET returns to the cartridge menu.
;
; The host generates cart-demo-data.inc with bank/length/load/checksum/name
; metadata for the PRGs packed into ROML banks 1..63. Cartridge copies are
; IRQ-patched to a small $0200 control shim so F1/RUN-STOP can return to this
; menu and SPACE can advance directly to the next animation. While the menu is
; active, F1 cycles default -> decorative -> demoscene -> default.

EF_BANK        = $de00
EF_CONTROL     = $de02
EF_OFF         = $04
EF_8K          = $06
EF_RAM         = $df00
DEBUGCART_EXIT = $d7ff

CONTROL_RAM       = $0200
CONTROL_ORIG_LO   = $02f8
CONTROL_ORIG_HI   = $02f9
CONTROL_CURRENT   = $02fa
CONTROL_LATCH     = $02fb
CONTROL_STYLE     = $02fc
CONTROL_CYCLE     = $0203
CONTROL_ROM       = $8800
RUNTIME_MENU      = $c803
RUNTIME_NEXT      = $c806

MENU_STYLE_DEFAULT    = 0
MENU_STYLE_DECORATIVE = 1
MENU_STYLE_DEMOSCENE  = 2
MENU_FONT_ROM         = $9000
MENU_FONT_RAM         = $2000

MENU_VISIBLE_ROWS = 10
.if MENU_STYLE == MENU_STYLE_DEFAULT
MENU_LIST_ROW = 2
MENU_LIST_COL = 0
.else
MENU_LIST_ROW = 5
MENU_LIST_COL = 3
.endif
MENU_HELP_ROW = MENU_LIST_ROW + MENU_VISIBLE_ROWS + 2
MENU_RESET_ROW = MENU_HELP_ROW + 1
MENU_SEPARATOR_ROW = MENU_HELP_ROW + 2
MENU_COPY_RASTER = 50 + (MENU_LIST_ROW + MENU_VISIBLE_ROWS)*8

; Menu/loader zero-page workspace. Existing yunroll PRGs replace/reinitialize
; their own state immediately after launch, so this is only live here.
ZP_SCREEN_LO   = $f1
ZP_SCREEN_HI   = $f2
ZP_SRC_LO      = $f3
ZP_SRC_HI      = $f4
ZP_DST_LO      = $f5
ZP_DST_HI      = $f6
ZP_REM_LO      = $f7
ZP_REM_HI      = $f8
ZP_STR_LO      = $f9
ZP_STR_HI      = $fa
ZP_BANK        = $fb
ZP_SUM_LO      = $fc
ZP_SUM_HI      = $fd
ZP_TMP         = $fe

* = $c800
; Fixed entry jump table.  The low-RAM control shim reloads this 2 KiB runtime
; from bank 0 and jumps here after aborting a running animation.
runtime_start:
    jmp runtime_cold
runtime_menu_entry:
    jmp runtime_return_menu
runtime_next_entry:
    jmp runtime_next_demo

runtime_common:
    sei
    cld

    ; Get the cartridge out of the normal C64 map before touching normal RAM.
    lda #EF_OFF
    sta EF_CONTROL
    lda #$37
    sta $01
    lda #$2f
    sta $00
    rts

runtime_cold:
    jsr runtime_common
    ; The live style-cycle entry lives in the $0200 cart-control shim, so the
    ; menu needs that shim installed even before the first animation launch.
    jsr install_control_shim
    ; The shim installer deliberately leaves $02F8-$02FF alone so persistent
    ; control state survives later menu/style reloads. Seed cold-start state.
    lda #MENU_STYLE
    sta CONTROL_STYLE
    lda #0
    sta CONTROL_CURRENT

.if VICE_DEBUGCART
    ; Automated validation mode: load every packed PRG through the exact same
    ; banked/staged path, checksum the resulting RAM, and tell VICE success only
    ; after all entries match their host-generated checksum.
    jmp debug_validate_all
.endif

    jsr init_menu_screen
    lda #0
    sta selected_entry
.if AUTO_LAUNCH < DEMO_ENTRY_COUNT
    lda #AUTO_LAUNCH
    sta selected_entry
    jmp menu_launch_nowait
.endif
    jmp menu_full_redraw

runtime_return_menu:
    jsr runtime_common
    jsr init_menu_screen
    lda CONTROL_CURRENT
    cmp #DEMO_ENTRY_COUNT
    bcc runtime_menu_index_ok
    lda #0
runtime_menu_index_ok:
    sta selected_entry
    jmp menu_full_redraw

runtime_next_demo:
    jsr runtime_common
    lda CONTROL_CURRENT
    clc
    adc #1
    cmp #DEMO_ENTRY_COUNT
    bcc runtime_next_index_ok
    lda #0
runtime_next_index_ok:
    sta selected_entry
    jmp menu_launch_nowait

menu_full_redraw:
    ; Preserve the highlighted entry across live menu-style swaps.
    lda selected_entry
    sta CONTROL_CURRENT
    lda #$d4
    sta color_page_delta
    jsr clear_screen

.if MENU_STYLE == MENU_STYLE_DEFAULT
    ; Keep the original simple utility-menu layout as the default style.
    lda #$03                    ; cyan title
    sta text_color
    lda #<($0400+0*40)
    sta ZP_SCREEN_LO
    lda #>($0400+0*40)
    sta ZP_SCREEN_HI
    lda #<title_default
    sta ZP_STR_LO
    lda #>title_default
    sta ZP_STR_HI
    jsr print_z_line

    lda #<($0400+2*40)
    sta ZP_SCREEN_LO
    lda #>($0400+2*40)
    sta ZP_SCREEN_HI
.else
    jsr draw_decorations

    lda #$03                    ; base cyan; gradient paint follows
    sta text_color
    lda #<($0400+1*40+10)
    sta ZP_SCREEN_LO
    lda #>($0400+1*40+10)
    sta ZP_SCREEN_HI
    lda #<title_fancy
    sta ZP_STR_LO
    lda #>title_fancy
    sta ZP_STR_HI
    jsr print_z_line

    lda #$0e                    ; light blue subtitle
    sta text_color
    lda #<($0400+2*40+8)
    sta ZP_SCREEN_LO
    lda #>($0400+2*40+8)
    sta ZP_SCREEN_HI
    lda #<subtitle_fancy
    sta ZP_STR_LO
    lda #>subtitle_fancy
    sta ZP_STR_HI
    jsr print_z_line

    jsr paint_menu_gradient

    lda #<($0400+5*40+3)
    sta ZP_SCREEN_LO
    lda #>($0400+5*40+3)
    sta ZP_SCREEN_HI
.endif

    jsr draw_list_borders
    jsr draw_menu_window

.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #$0e
    sta text_color
    lda #<($0400+MENU_HELP_ROW*40)
    sta ZP_SCREEN_LO
    lda #>($0400+MENU_HELP_ROW*40)
    sta ZP_SCREEN_HI
.else
    lda #$03
    sta text_color
    lda #<($0400+MENU_HELP_ROW*40+5)
    sta ZP_SCREEN_LO
    lda #>($0400+MENU_HELP_ROW*40+5)
    sta ZP_SCREEN_HI
.endif
    lda #<help_text
    sta ZP_STR_LO
    lda #>help_text
    sta ZP_STR_HI
    jsr print_z_line

.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #<($0400+MENU_RESET_ROW*40)
    sta ZP_SCREEN_LO
    lda #>($0400+MENU_RESET_ROW*40)
    sta ZP_SCREEN_HI
.else
    lda #$0c
    sta text_color
    lda #<($0400+MENU_RESET_ROW*40+2)
    sta ZP_SCREEN_LO
    lda #>($0400+MENU_RESET_ROW*40+2)
    sta ZP_SCREEN_HI
.endif
    lda #<reset_text
    sta ZP_STR_LO
    lda #>reset_text
    sta ZP_STR_HI
    jsr print_z_line

    ; Common footer: present in every menu style.
    lda #$0c                    ; gray byline
    sta text_color
.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #<($0400+17*40+9)
    sta ZP_SCREEN_LO
    lda #>($0400+17*40+9)
    sta ZP_SCREEN_HI
.else
    lda #<($0400+20*40+9)
    sta ZP_SCREEN_LO
    lda #>($0400+20*40+9)
    sta ZP_SCREEN_HI
.endif
    lda #<byline_text
    sta ZP_STR_LO
    lda #>byline_text
    sta ZP_STR_HI
    jsr print_z_line

    lda #$0e                    ; light blue repository line
    sta text_color
.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #<($0400+19*40+2)
    sta ZP_SCREEN_LO
    lda #>($0400+19*40+2)
    sta ZP_SCREEN_HI
.else
    lda #<($0400+22*40+2)
    sta ZP_SCREEN_LO
    lda #>($0400+22*40+2)
    sta ZP_SCREEN_HI
.endif
    lda #<repo_text
    sta ZP_STR_LO
    lda #>repo_text
    sta ZP_STR_HI
    jsr print_z_line

.if MENU_STYLE != MENU_STYLE_DEFAULT
    jsr paint_menu_gradient
.endif

menu_wait_key:
    jsr scan_menu_key
    beq menu_wait_key
    cmp #1
    beq menu_down
    cmp #2
    beq menu_up
    cmp #3
    beq menu_launch
    cmp #4
    beq menu_cycle_style
    bne menu_wait_key

menu_down:
    jsr wait_menu_key_release
    inc selected_entry
    lda selected_entry
    cmp #DEMO_ENTRY_COUNT
    bcs menu_down_wrap
    jmp menu_redraw
menu_down_wrap:
    lda #0
    sta selected_entry
    jmp menu_redraw

menu_up:
    jsr wait_menu_key_release
    lda selected_entry
    bne menu_up_dec
    lda #DEMO_ENTRY_COUNT-1
    sta selected_entry
    jmp menu_redraw
menu_up_dec:
    dec selected_entry
    jmp menu_redraw

menu_cycle_style:
    jsr wait_menu_key_release
    jmp CONTROL_CYCLE

menu_launch:
    jsr wait_menu_key_release
menu_launch_nowait:
    sei
    ldx selected_entry
    jsr load_entry_x
    jsr install_control_shim
    ; Reassert the compile-time style ID before handing control to the
    ; animation. The shim installer preserves the state tail, so this is now
    ; explicit launch-state setup rather than a repair for overwritten bytes.
    lda #MENU_STYLE
    sta CONTROL_STYLE

    ; Tell the control shim which production IRQ to tail-chain to and which demo
    ; is currently active. The host patched only the cartridge copy of each PRG
    ; so its IRQ-vector install points to CONTROL_RAM instead of the original.
    ldx selected_entry
    lda demo_irq_lo,x
    sta CONTROL_ORIG_LO
    lda demo_irq_hi,x
    sta CONTROL_ORIG_HI
    txa
    sta CONTROL_CURRENT
    lda #0
    sta CONTROL_LATCH

    ; Current production yunroll PRGs enter ML at $080D. The address is carried
    ; in metadata so future demo entries need not depend on that convention.
    ldx selected_entry
    lda demo_entry_lo,x
    sta launch_jump+1
    lda demo_entry_hi,x
    sta launch_jump+2

    lda #EF_OFF
    sta EF_CONTROL
    lda #$37
    sta $01
launch_jump:
    jmp $ffff

; Install the 256-byte cart-control IRQ shim from bank 0 ROML $8800-$88FF.
; Runtime code executes at $C800, so it can safely keep running while ROML is
; visible at $8000-$9FFF.
install_control_shim:
    ; $02F8-$02FF is persistent control state, not part of the executable shim.
    ; Copy only $0200-$02F7 so reinstalling the shim while returning to the
    ; menu cannot erase CONTROL_STYLE/CONTROL_CURRENT/etc.  Copying the whole
    ; 256-byte page made every F1 cycle see style $FF and reload default.
    lda #0
    sta EF_BANK
    lda #EF_8K
    sta EF_CONTROL
    ldx #0
install_control_loop:
    lda CONTROL_ROM,x
    sta CONTROL_RAM,x
    inx
    cpx #$f8
    bne install_control_loop
    lda #EF_OFF
    sta EF_CONTROL
    rts

; -----------------------------------------------------------------------------
; Plain text-mode setup.  This intentionally avoids KERNAL reset/editor state:
; native EasyFlash boot replaces the normal KERNAL reset path, so direct VIC/CIA
; setup is both smaller and more deterministic for this cartridge menu.
; -----------------------------------------------------------------------------
init_menu_screen:
    jsr load_menu_shared
    jsr install_control_shim
    lda #$7f
    sta $dc0d
    sta $dd0d
    lda $dc0d
    lda $dd0d
    lda #0
    sta $d01a
    sta $d015
    sta $d020
    sta $d021

    ; VIC bank 0, screen=$0400. Default keeps the built-in upper/lower ROM
    ; character set; decorative styles install the compact HUD-derived 5x7 set
    ; at $2000.
    lda $dd02
    ora #$03
    sta $dd02
    lda $dd00
    ora #$03
    sta $dd00
    lda #$1b
    sta $d011
    lda #$08
    sta $d016
.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #$16                    ; screen $0400, lower/upper char ROM at $1800
    sta $d018
.else
    jsr install_menu_charset
    lda #$18                    ; screen $0400, custom charset RAM at $2000
    sta $d018
    lda #$06                    ; blue border around the black menu field
    sta $d020
.endif

    ; CIA1 keyboard matrix: port A outputs row select, port B inputs columns.
    lda #$ff
    sta $dc02
    sta $dc00
    lda #$00
    sta $dc03

.if MENU_STYLE == MENU_STYLE_DEMOSCENE
    jsr install_menu_irq
.endif
    rts

.if MENU_STYLE != MENU_STYLE_DEFAULT
; Copy the menu-only 2 KiB compact character set from bank-0 ROML $9000 to
; ordinary C64 RAM $2000. The runtime lives at $C800, so this direct copy does
; not need the $DF00 staging page used by arbitrary PRG payloads.
install_menu_charset:
    lda #0
    sta EF_BANK
    lda #EF_8K
    sta EF_CONTROL
    ldx #0
install_font_loop:
    lda MENU_FONT_ROM+$000,x
    sta MENU_FONT_RAM+$000,x
    lda MENU_FONT_ROM+$100,x
    sta MENU_FONT_RAM+$100,x
    lda MENU_FONT_ROM+$200,x
    sta MENU_FONT_RAM+$200,x
    lda MENU_FONT_ROM+$300,x
    sta MENU_FONT_RAM+$300,x
    lda MENU_FONT_ROM+$400,x
    sta MENU_FONT_RAM+$400,x
    lda MENU_FONT_ROM+$500,x
    sta MENU_FONT_RAM+$500,x
    lda MENU_FONT_ROM+$600,x
    sta MENU_FONT_RAM+$600,x
    lda MENU_FONT_ROM+$700,x
    sta MENU_FONT_RAM+$700,x
    inx
    bne install_font_loop
    lda #EF_OFF
    sta EF_CONTROL
    rts

; Static frame/separators for decorative and demoscene menus.
draw_decorations:
    lda #$06
    sta text_color
    lda #<($0400+0*40)
    sta ZP_SCREEN_LO
    lda #>($0400+0*40)
    sta ZP_SCREEN_HI
    lda #<frame_line
    sta ZP_STR_LO
    lda #>frame_line
    sta ZP_STR_HI
    jsr print_z_line

    lda #$0e
    sta text_color
    lda #<($0400+(MENU_LIST_ROW-1)*40)
    sta ZP_SCREEN_LO
    lda #>($0400+(MENU_LIST_ROW-1)*40)
    sta ZP_SCREEN_HI
    jsr print_z_line

    lda #$06
    sta text_color
    lda #<($0400+MENU_SEPARATOR_ROW*40)
    sta ZP_SCREEN_LO
    lda #>($0400+MENU_SEPARATOR_ROW*40)
    sta ZP_SCREEN_HI
    jsr print_z_line

    lda #$0e
    sta text_color
    lda #<($0400+24*40)
    sta ZP_SCREEN_LO
    lda #>($0400+24*40)
    sta ZP_SCREEN_HI
    jsr print_z_line
    rts

; Paint header/subtitle/repo with a C64 palette gradient. Decorative uses a
; fixed phase; demoscene advances the phase from the menu raster IRQ.
paint_menu_gradient:
    ldx #0
paint_title_loop:
    txa
    clc
    adc gradient_phase
    and #$0f
    tay
    lda gradient_palette,y
    sta $d832,x                ; row 1, column 10
    inx
    cpx #20
    bne paint_title_loop

    ldx #0
paint_subtitle_loop:
    txa
    clc
    adc gradient_phase
    adc #4
    and #$0f
    tay
    lda gradient_palette,y
    sta $d858,x                ; row 2, column 8
    inx
    cpx #24
    bne paint_subtitle_loop

    ldx #0
paint_repo_loop:
    txa
    clc
    adc gradient_phase
    adc #8
    and #$0f
    tay
    lda gradient_palette,y
    sta $db72,x                ; row 22, column 2
    inx
    cpx #36
    bne paint_repo_loop
    rts

.if MENU_STYLE == MENU_STYLE_DEMOSCENE
install_menu_irq:
    lda #0
    sta gradient_phase
    sta gradient_divider
    ; Run a private raster IRQ with KERNAL ROM banked out. No KERNAL services
    ; are used by the cartridge menu.
    lda #$35
    sta $01
    lda #<menu_irq
    sta $fffe
    lda #>menu_irq
    sta $ffff
    lda #$fa
    sta $d012
    lda $d011
    and #$7f
    sta $d011
    lda #$01
    sta $d019
    sta $d01a
    cli
    rts

menu_irq:
    pha
    txa
    pha
    tya
    pha

    inc gradient_divider
    lda gradient_divider
    and #$03                   ; advance every four frames
    bne menu_irq_no_step
    inc gradient_phase
    lda gradient_phase
    and #$0f
    sta gradient_phase
menu_irq_no_step:
    jsr paint_menu_gradient
    ldx gradient_phase
    lda gradient_palette,x
    sta $d020                  ; slowly cycle the border too

    lda #$01
    sta $d019
    pla
    tay
    pla
    tax
    pla
    rti
.endif
.endif

clear_screen:
    ldx #0
clear_screen_loop:
    lda #$20
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #$01
.else
    lda #$0e
.endif
    sta $d800,x
    sta $d900,x
    sta $da00,x
    sta $db00,x
    inx
    bne clear_screen_loop
    rts

; Print a zero-terminated ASCII-ish menu string and colour the same cells.
; The default style uses the C64 lower/upper ROM set, where screen codes 1..26
; are lowercase and $41..$5a uppercase. The compact custom set deliberately uses
; the opposite arrangement to keep its uppercase mapping compatible with the
; historical HUD font.
print_z_line:
    lda ZP_SCREEN_LO
    sta ZP_SRC_LO
    lda ZP_SCREEN_HI
    clc
    adc color_page_delta
    sta ZP_SRC_HI
    ldy #0
print_z_line_loop:
    lda (ZP_STR_LO),y
    beq print_z_line_done

.if MENU_STYLE == MENU_STYLE_DEFAULT
    cmp #$61
    bcc print_default_not_lower
    cmp #$7b
    bcs print_default_not_lower
    sec
    sbc #$60                   ; lowercase ASCII -> screen 1..26
    jmp print_z_line_store
print_default_not_lower:
    ; Uppercase ASCII $41..$5a is already the desired lower/upper-ROM screen
    ; code. Digits, spaces and punctuation are also direct.
.else
    cmp #$41
    bcc print_custom_not_upper
    cmp #$5b
    bcs print_custom_not_upper
    and #$3f                   ; uppercase ASCII -> screen 1..26
    jmp print_z_line_store
print_custom_not_upper:
    cmp #$61
    bcc print_z_line_store
    cmp #$7b
    bcs print_z_line_store
    sec
    sbc #$20                   ; lowercase ASCII -> screen $41..$5a
.endif
print_z_line_store:
    sta (ZP_SCREEN_LO),y
    lda text_color
    sta (ZP_SRC_LO),y
    iny
    bne print_z_line_loop
print_z_line_done:
    rts

; Return A=0 none, 1 next/down/right, 2 previous/up/left, 3 RETURN, 4 F1 style.
; The physical C64 has CRSR DOWN and CRSR RIGHT keys; shifted variants are
; CRSR UP and CRSR LEFT. Accept either SHIFT key because host keymaps differ.
scan_menu_key:
    lda #$fe                    ; select keyboard row 0
    sta $dc00
    lda $dc01
    sta ZP_TMP
    lda #$ff
    sta $dc00

    lda ZP_TMP
    and #$10                    ; F1, row 0 bit 4
    beq scan_key_style

    lda ZP_TMP
    and #$02                    ; RETURN, row 0 bit 1
    beq scan_key_return

    lda ZP_TMP
    and #$80                    ; CRSR DOWN / shifted UP
    beq scan_key_vertical

    lda ZP_TMP
    and #$04                    ; CRSR RIGHT / shifted LEFT
    beq scan_key_horizontal

    lda #0
    rts

scan_key_vertical:
    jsr scan_shift_pressed
    bne scan_key_previous       ; shifted DOWN = UP
    lda #1
    rts

scan_key_horizontal:
    jsr scan_shift_pressed
    bne scan_key_previous       ; shifted RIGHT = LEFT
    lda #1                      ; unshifted RIGHT = next
    rts

scan_key_previous:
    lda #2
    rts
scan_key_return:
    lda #3
    rts
scan_key_style:
    lda #4
    rts

; Return A=1 if either C64 SHIFT key is down, otherwise A=0.
scan_shift_pressed:
    lda #$fd                    ; row 1, bit 7 = left SHIFT
    sta $dc00
    lda $dc01
    and #$80
    beq scan_shift_yes

    lda #$bf                    ; row 6, bit 4 = right SHIFT
    sta $dc00
    lda $dc01
    and #$10
    beq scan_shift_yes

    lda #$ff
    sta $dc00
    lda #0
    rts
scan_shift_yes:
    lda #$ff
    sta $dc00
    lda #1
    rts

wait_menu_key_release:
    lda #$fe
    sta $dc00
wait_menu_key_release_loop:
    lda $dc01
    and #$96                    ; F1 / RETURN / CRSR RIGHT / CRSR DOWN
    cmp #$96
    bne wait_menu_key_release_loop
    lda #$ff
    sta $dc00
    rts

; -----------------------------------------------------------------------------
; Load selected entry X from bank-aligned ROML payload into its PRG load address.
;
; The source is read in 256-byte pages through $8000-$9FFF. Each page is first
; copied to EasyFlash's always-visible $DF00-$DFFF RAM, the ROM is hidden, then
; the staging page is copied to C64 RAM. This avoids relying on writes to RAM
; hidden beneath cartridge ROM and handles destination $8000-$9FFF cleanly.
; -----------------------------------------------------------------------------
load_entry_x:
    lda demo_bank,x
    sta ZP_BANK
    lda #$00
    sta ZP_SRC_LO
    lda #$80
    sta ZP_SRC_HI
    lda demo_load_lo,x
    sta ZP_DST_LO
    lda demo_load_hi,x
    sta ZP_DST_HI
    lda demo_len_lo,x
    sta ZP_REM_LO
    lda demo_len_hi,x
    sta ZP_REM_HI

load_next_chunk:
    lda ZP_REM_LO
    ora ZP_REM_HI
    beq load_done

    lda ZP_BANK
    sta EF_BANK
    lda #EF_8K
    sta EF_CONTROL

    lda ZP_REM_HI
    beq load_partial_chunk

    ldy #0
load_full_to_stage:
    lda (ZP_SRC_LO),y
    sta EF_RAM,y
    iny
    bne load_full_to_stage

    lda #EF_OFF
    sta EF_CONTROL

    ldy #0
load_full_to_ram:
    lda EF_RAM,y
    sta (ZP_DST_LO),y
    iny
    bne load_full_to_ram

    inc ZP_DST_HI
    inc ZP_SRC_HI
    dec ZP_REM_HI

    lda ZP_SRC_HI
    cmp #$a0
    bne load_next_chunk
    lda #$80
    sta ZP_SRC_HI
    inc ZP_BANK
    jmp load_next_chunk

load_partial_chunk:
    ldx ZP_REM_LO
    ldy #0
load_partial_to_stage:
    lda (ZP_SRC_LO),y
    sta EF_RAM,y
    iny
    dex
    bne load_partial_to_stage

    lda #EF_OFF
    sta EF_CONTROL

    ldx ZP_REM_LO
    ldy #0
load_partial_to_ram:
    lda EF_RAM,y
    sta (ZP_DST_LO),y
    iny
    dex
    bne load_partial_to_ram

    lda #0
    sta ZP_REM_LO
    sta ZP_REM_HI

load_done:
    lda #EF_OFF
    sta EF_CONTROL
    rts

; -----------------------------------------------------------------------------
; Debug-only full cartridge validation.
; -----------------------------------------------------------------------------
debug_validate_all:
    lda #0
    sta selected_entry

debug_entry_loop:
    ldx selected_entry
    jsr load_entry_x
    ldx selected_entry
    jsr checksum_entry_x

    ldx selected_entry
    lda ZP_SUM_LO
    cmp demo_sum_lo,x
    bne debug_fail
    lda ZP_SUM_HI
    cmp demo_sum_hi,x
    bne debug_fail

    inc selected_entry
    lda selected_entry
    cmp #DEMO_ENTRY_COUNT
    bne debug_entry_loop

    lda #0
    sta DEBUGCART_EXIT
debug_success_hang:
    jmp debug_success_hang

debug_fail:
    lda selected_entry
    clc
    adc #1
    sta DEBUGCART_EXIT
debug_fail_hang:
    jmp debug_fail_hang

checksum_entry_x:
    ; Read RAM rather than BASIC/KERNAL ROM while verifying copied payloads.
    lda #$35
    sta $01

    lda demo_load_lo,x
    sta ZP_DST_LO
    lda demo_load_hi,x
    sta ZP_DST_HI
    lda demo_len_lo,x
    sta ZP_REM_LO
    lda demo_len_hi,x
    sta ZP_REM_HI
    lda #0
    sta ZP_SUM_LO
    sta ZP_SUM_HI

checksum_next_chunk:
    lda ZP_REM_LO
    ora ZP_REM_HI
    beq checksum_done
    lda ZP_REM_HI
    beq checksum_partial

    ldy #0
checksum_full_loop:
    lda (ZP_DST_LO),y
    clc
    adc ZP_SUM_LO
    sta ZP_SUM_LO
    lda ZP_SUM_HI
    adc #0
    sta ZP_SUM_HI
    iny
    bne checksum_full_loop
    inc ZP_DST_HI
    dec ZP_REM_HI
    jmp checksum_next_chunk

checksum_partial:
    ldx ZP_REM_LO
    ldy #0
checksum_partial_loop:
    lda (ZP_DST_LO),y
    clc
    adc ZP_SUM_LO
    sta ZP_SUM_LO
    lda ZP_SUM_HI
    adc #0
    sta ZP_SUM_HI
    iny
    dex
    bne checksum_partial_loop
    lda #0
    sta ZP_REM_LO
    sta ZP_REM_HI

checksum_done:
    lda #$37
    sta $01
    rts

load_menu_shared:
    lda #2
    sta $de00
    lda #$07
    sta $de02
    ldx #0
load_menu_shared_loop:
    lda $a000+MENU_STYLE*$0800+$0000,x
    sta $c000,x
    lda $a000+MENU_STYLE*$0800+$0100,x
    sta $c100,x
    lda $a000+MENU_STYLE*$0800+$0200,x
    sta $c200,x
    lda $a000+MENU_STYLE*$0800+$0300,x
    sta $c300,x
    lda $a000+MENU_STYLE*$0800+$0400,x
    sta $c400,x
    lda $a000+MENU_STYLE*$0800+$0500,x
    sta $c500,x
    lda $a000+MENU_STYLE*$0800+$0600,x
    sta $c600,x
    lda $a000+MENU_STYLE*$0800+$0700,x
    sta $c700,x
    inx
    bne load_menu_shared_loop
    lda #$04
    sta $de02
    rts

selected_entry:
    .byte 0
text_color:
    .byte 1
gradient_phase:
    .byte 0
gradient_divider:
    .byte 0

gradient_palette:
    .byte $06,$0e,$03,$0d,$07,$0a,$02,$04,$0a,$07,$0d,$03,$0e,$06,$0b,$0c

title_default:
    .text "C64 3D TOOLKIT 0.6.4  ALL V"
    .byte $30+RENDERER_VERSION
    .byte 0
title_fancy:
    .text "C64-3D-TOOLKIT 0.6.4"
    .byte 0
subtitle_fancy:
    .text "ALL DEMOS: CART V"
    .byte $30+RENDERER_VERSION
    .byte 0
help_text:
    .text "CURSORS SELECT RETURN PLAY F1 STYLE"
    .byte 0
reset_text:
    .text "IN DEMO: F1/RUNSTOP MENU  SPACE NEXT"
    .byte 0
byline_text:
    .text "by FlyingFathead, 2026"
    .byte 0
repo_text:
    .text "github: flyingfathead/c64-3d-toolkit"
    .byte 0
frame_line:
    .text "========================================"
    .byte 0

; Shared directory and viewport code is loaded from bank 2 by menu style.
.if * > $d000
    .error "scroll menu runtime exceeds $cfff"
.endif
.fill $d000-*, $ff
* = $c000
.include "cart-demo-data.inc"



color_page_delta: .byte $d4
top_entry: .byte 0
rows_remaining: .byte 0

; Loaded main code is at C800 and remains executable while bank 2 is mapped.
; This loader must be in the main image, so it is defined below at a reserved
; address inside the main-image padding.
menu_redraw:
    lda selected_entry
    sta CONTROL_CURRENT
    jsr draw_menu_window
    jmp menu_wait_key

draw_menu_window:
    lda selected_entry
    cmp top_entry
    bcs menu_check_bottom
    sta top_entry
menu_check_bottom:
    sec
    sbc top_entry
    cmp #MENU_VISIBLE_ROWS
    bcc menu_top_ready
    lda selected_entry
    sec
    sbc #MENU_VISIBLE_ROWS-1
    sta top_entry
menu_top_ready:
    ; Build all ten rows offscreen; no clearing of the displayed screen.
    ldx #0
menu_clear_shadow:
    lda #$20
    sta $0800,x
    sta $0890,x
    lda #$01
    sta $0c00,x
    sta $0c90,x
    inx
    bne menu_clear_shadow
    lda #$04
    sta color_page_delta
    lda #<($0800+MENU_LIST_COL)
    sta ZP_SCREEN_LO
    lda #>($0800+MENU_LIST_COL)
    sta ZP_SCREEN_HI
    ldx top_entry
    lda #MENU_VISIBLE_ROWS
    sta rows_remaining
menu_entry_loop:
    stx ZP_TMP
    txa
    cmp selected_entry
    bne not_selected
    lda #$07                    ; yellow selected row
    sta text_color
    lda #$3e                    ; '>' marker
    bne marker_ready
not_selected:
.if MENU_STYLE == MENU_STYLE_DEFAULT
    lda #$01                    ; white
.else
    lda #$0e                    ; light blue
.endif
    sta text_color
    lda #$20
marker_ready:
    ldy #0
    sta (ZP_SCREEN_LO),y

    ; Colour the marker cell as well as the text printed below.
    lda ZP_SCREEN_LO
    sta ZP_SRC_LO
    lda ZP_SCREEN_HI
    clc
    adc color_page_delta
    sta ZP_SRC_HI
    lda text_color
    sta (ZP_SRC_LO),y

    iny
    lda #$20
    sta (ZP_SCREEN_LO),y
    lda text_color
    sta (ZP_SRC_LO),y

    ldx ZP_TMP
    lda demo_name_lo,x
    sta ZP_STR_LO
    lda demo_name_hi,x
    sta ZP_STR_HI

    ; Temporarily advance screen pointer by two columns for the name.
    clc
    lda ZP_SCREEN_LO
    adc #2
    sta ZP_SCREEN_LO
    bcc entry_name_ptr_ok
    inc ZP_SCREEN_HI
entry_name_ptr_ok:
    jsr print_z_line

    ; We are at row_base+2; add 38 to reach the next 40-column row base.
    clc
    lda ZP_SCREEN_LO
    adc #38
    sta ZP_SCREEN_LO
    bcc entry_next_row_ok
    inc ZP_SCREEN_HI
entry_next_row_ok:
    ldx ZP_TMP
    inx
    cpx #DEMO_ENTRY_COUNT
    beq menu_entries_done
    dec rows_remaining
    bne menu_entry_loop
menu_entries_done:


    lda #$d4
    sta color_page_delta
    ; Wait for the beam to pass the list. Do not blank DEN or change VIC bank.
menu_wait_copy_frame:
    lda $d011
    bmi menu_wait_copy_frame
menu_wait_copy_line:
    lda $d012
    cmp #MENU_COPY_RASTER
    bne menu_wait_copy_line
    ldx #0
menu_commit_viewport:
    lda $0800,x
    sta $0400+MENU_LIST_ROW*40,x
    lda $0c00,x
    sta $d800+(MENU_LIST_ROW+0)*40,x
    lda $0828,x
    sta $0428+MENU_LIST_ROW*40,x
    lda $0c28,x
    sta $d800+(MENU_LIST_ROW+1)*40,x
    lda $0850,x
    sta $0450+MENU_LIST_ROW*40,x
    lda $0c50,x
    sta $d800+(MENU_LIST_ROW+2)*40,x
    lda $0878,x
    sta $0478+MENU_LIST_ROW*40,x
    lda $0c78,x
    sta $d800+(MENU_LIST_ROW+3)*40,x
    lda $08a0,x
    sta $04a0+MENU_LIST_ROW*40,x
    lda $0ca0,x
    sta $d800+(MENU_LIST_ROW+4)*40,x
    lda $08c8,x
    sta $04c8+MENU_LIST_ROW*40,x
    lda $0cc8,x
    sta $d800+(MENU_LIST_ROW+5)*40,x
    lda $08f0,x
    sta $04f0+MENU_LIST_ROW*40,x
    lda $0cf0,x
    sta $d800+(MENU_LIST_ROW+6)*40,x
    lda $0918,x
    sta $0518+MENU_LIST_ROW*40,x
    lda $0d18,x
    sta $d800+(MENU_LIST_ROW+7)*40,x
    lda $0940,x
    sta $0540+MENU_LIST_ROW*40,x
    lda $0d40,x
    sta $d800+(MENU_LIST_ROW+8)*40,x
    lda $0968,x
    sta $0568+MENU_LIST_ROW*40,x
    lda $0d68,x
    sta $d800+(MENU_LIST_ROW+9)*40,x
    inx
    cpx #40
    beq menu_commit_done
    jmp menu_commit_viewport
menu_commit_done:
    lda #$3d
    ldx top_entry
    beq menu_no_above
    lda #$2b                    ; '+' means more entries beyond this border
menu_no_above:
    sta $0400+(MENU_LIST_ROW-1)*40+38
    lda top_entry
    clc
    adc #MENU_VISIBLE_ROWS
    cmp #DEMO_ENTRY_COUNT
    lda #$3d
    bcs menu_no_below
    lda #$2b
menu_no_below:
    sta $0400+(MENU_LIST_ROW+MENU_VISIBLE_ROWS)*40+38
    rts

draw_list_borders:
    lda #$0e
    sta text_color
    lda #<frame_line
    sta ZP_STR_LO
    lda #>frame_line
    sta ZP_STR_HI
    lda #<($0400+(MENU_LIST_ROW-1)*40)
    sta ZP_SCREEN_LO
    lda #>($0400+(MENU_LIST_ROW-1)*40)
    sta ZP_SCREEN_HI
    jsr print_z_line
    lda #<($0400+(MENU_LIST_ROW+MENU_VISIBLE_ROWS)*40)
    sta ZP_SCREEN_LO
    lda #>($0400+(MENU_LIST_ROW+MENU_VISIBLE_ROWS)*40)
    sta ZP_SCREEN_HI
    jmp print_z_line

.if * > $c800
.error "menu directory/scroll helpers exceed $c000-$c7ff"
.endif
.fill $c800-*, $ff
