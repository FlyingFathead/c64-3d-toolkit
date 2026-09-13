"""Event-only selection of the original light stars or the fuller starfield.

Both kernels and both trajectory sets are resident in RAM. The IRQ call target
is patched with interrupts masked; there is no per-refresh mode dispatch.
"""
import re
from .demo_colors import once
from .emit import bytes_lines
from .hors_v3_effects import trajectories


def configure(source, *, default_profile="full"):
    if default_profile not in ("full", "light"):
        raise ValueError("Unknown starfield profile")
    source = once(source, '        jsr fx_irq\n', 'sl_dispatch:\n        jsr fx_irq\n')
    # Screen buffer 1 is unused during boot. Copy before video clears it.
    copies = ''.join(f'        lda ${0x4400+p*256:04x},x\n        sta ${0x8000+p*256:04x},x\n' for p in range(4))
    source = once(source, 'sp_boot_copy_loop:\n', 'sp_boot_copy_loop:\n'+copies)
    if '        bne sp_boot_copy_loop\n' in source:
        source = once(source, '        bne sp_boot_copy_loop\n',
                      '        beq sp_boot_copy_done\n        jmp sp_boot_copy_loop\nsp_boot_copy_done:\n')

    # 4 shares the already-read row with 3. No new CIA row access.
    source = once(source, 'sd_row1_read:\n        and #1\n        beq sd_less\n',
                  'sd_row1_read:\n        sta sd_row\n        and #1\n        beq sd_less\n        lda sd_row\n        and #8\n        bne sl_no_key\n        jmp sl_toggle\nsl_no_key:\n')
    source = once(source, '        lda sd_level\n        cmp #5\n',
                  '        lda sd_level\n        ldy sl_mode\n        cmp sl_limits,y\n')
    source = once(source, 'sd_reset:\n        lda sp_held\n        bne sd_key_done\n        lda #3\n',
                  'sd_reset:\n        lda sp_held\n        bne sd_key_done\n        ldy sl_mode\n        lda sl_defaults,y\n')
    source = once(source, 'sd_default:\n        lda #3\n',
                  'sd_default:\n        jmp sl_reset_all\nsl_default_full:\n        lda #3\n')
    source = once(source, 'sd_apply:\n', '''sd_apply:
        lda sl_mode
        beq sl_apply_full
        jmp sl_apply_light
sl_apply_full:
        lda #<fx_irq
        sta sl_dispatch+1
        lda #>fx_irq
        sta sl_dispatch+2
''')

    # Recover the original single-point loop, including current opaque-paint
    # protection, from the shared effects source before the density extension.
    first, last = source.index('fx_irq:\n'), source.index('fx_irq_return:\n')+len('fx_irq_return:\n        rts\n')
    kernel = source[first:last]
    phase_start = kernel.index('        cmp sd_periods,x\n')
    phase_end = kernel.index('        lda fx_xlo,x\n', phase_start)
    kernel = kernel[:phase_start]+'''        and #63
        sta fx_phase,x
        tay
'''+kernel[phase_end:]
    kernel = once(kernel, '        jsr sd_visible\n        bcs fx_hidden\n        lda fx_y\n', '')
    kernel = once(kernel, 'sd_sprite_count:\n', '''        ldx #7
        lda #$fe
sl_pointer_loop:
sl_pointer_store:
        sta $07f8,x
        dex
        bpl sl_pointer_loop
sl_sprite_count:
''')
    kernel = kernel.replace('sta fx_pointer_store+2', 'sta sl_pointer_store+2')
    for name in ('fx_xlo','fx_xhi','fx_ylo','fx_yhi'):
        kernel = re.sub(r'\b'+name+r'\b', name.replace('fx_', 'sl_'), kernel)
    local_labels = re.findall(r'^(fx_\w+):', kernel, re.M)
    for label in sorted(local_labels, key=len, reverse=True):
        kernel = re.sub(r'\b'+label+r'\b', label.replace('fx_', 'sl_'), kernel)

    code = '''
sl_toggle:
        lda sp_held
        beq sl_toggle_ready
        jmp sd_key_done
sl_toggle_ready:
        php
        sei
        lda #0
        sta $d015
        sta fx_visible
        ldy sl_mode
        lda sd_level
        sta sl_levels,y
        tya
        eor #1
        sta sl_mode
        tay
        lda sl_levels,y
        sta sd_level
        jsr sl_restart_phases
        jsr sd_apply
        plp
        jmp sd_key_done
sl_reset_all:
        php
        sei
        lda #SL_DEFAULT_MODE
        sta sl_mode
        lda #3
        sta sl_levels
        lda #2
        sta sl_levels+1
        lda #SL_DEFAULT_LEVEL
        sta sd_level
        jsr sd_apply
        plp
        rts
sl_restart_phases:
        ldx #7
sl_phase_loop:
        lda sl_initial_phases,x
        sta fx_phase,x
        dex
        bpl sl_phase_loop
        rts
sl_apply_light:
        lda #<sl_irq
        sta sl_dispatch+1
        lda #>sl_irq
        sta sl_dispatch+2
        ldy sd_level
        lda sd_sprites,y
        sta sl_sprite_count+1
        lda #1
        sta sd_dot_count
        lda #0
        sta sd_wide
        ldy #62
sl_clear_pattern:
        sta $3f80,y
        sta $7f80,y
        sta $ff80,y
        dey
        bpl sl_clear_pattern
        lda #$80
        sta $3f80
        sta $7f80
        sta $ff80
        rts
sl_mode: .byte 0
sl_levels: .byte 3,2
sl_defaults: .byte 3,2
sl_limits: .byte 5,2
sl_initial_phases: .byte 0,9,18,27,36,45,54,63
'''.replace('SL_DEFAULT_MODE', str(int(default_profile=='light'))).replace('SL_DEFAULT_LEVEL', '2' if default_profile=='light' else '3')+kernel
    for axis in ('x','y'):
        for part,op in (('lo','<'),('hi','>')):
            code += f'sl_{axis}{part}: .byte '+','.join(f'{op}sl_{axis}{i}' for i in range(8))+'\n'
    code += 'sl_end:\n'
    source = once(source, 'sd_end:\n', code+'sd_end:\n')
    source += '\n* = $4400\n.logical $8000\nsl_paths:\n'
    for i,points in enumerate(trajectories()):
        for axis,coord in (('x',0),('y',1)):
            source += f'sl_{axis}{i}:\n'+'\n'.join(bytes_lines([p[coord] for p in points]))+'\n'
    source += '''sl_paths_end:
.if * != $8400
.error "Light star paths overlap help screen RAM"
.endif
.here
'''
    return source


def describe(manifest, *, default_profile="full"):
    manifest['background_effect']['profiles'] = dict(
        default=default_profile, toggle_key='4',
        light=dict(default_points=8, levels=[2,4,8], width=1, path_samples=64,
                   trajectories='original eight-point perspective field'),
        full=dict(default_points=16, levels=[2,4,8,16,24,32], near_width=2),
        independent_density=True, extra_path_RAM=[0x8000,0x8400],
        boot_staging=[0x4400,0x4800], additional_RAM_bytes=1024,
        switch='IRQ call operand and sprite patterns changed only on key events; both kernels already in RAM',
        extra_per_refresh_dispatch_cycles=0)
    manifest['background_effect']['density']['default'] = 8 if default_profile=='light' else 16
    manifest['interactive_cart']['keys'].update({
        '1':'reset density for current starfield (light 8 / full 16)',
        '4':'switch light / full starfield; preserve each density and on/off state'})
