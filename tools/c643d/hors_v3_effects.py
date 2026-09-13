"""Optional RAM-resident presentation controls and forward starfield for V3.

These builds use only literal frames. The unused $1700..$1fff vector lookup
tables are reclaimed after that property is checked by the directory writer.
No previous renderer source or ordinary V3 cartridge is modified.
"""
import math
from .demo_colors import once
from .emit import bytes_lines
from .colors import C64_PALETTE, c64_color_name
from .surface_palettes import shade_codes


STAR_PERIODS = (64, 59, 53, 47, 61, 57, 51, 43)


def trajectories(interactive=False):
    result = []
    for i in range(8):
        angle = math.radians((11, 57, 108, 148, 194, 239, 283, 328)[i]) if interactive else (i+.31) * math.tau / 8
        dx, dy = math.cos(angle), math.sin(angle)
        extent = min(123/max(abs(dx), .001), 90/max(abs(dy), .001))
        points = []
        for step in range(64):
            # Perspective acceleration towards the viewport edges.
            period = STAR_PERIODS[i] if interactive else 64
            depth = .12 if interactive else .045
            radius = extent * (depth / (1+depth-(step % period)/(period-1)))
            points.append((round(128+dx*radius), round(96+dy*radius)))
        result.append(points)
    return result


def reclaim_tables(path, directory, writer, **kwargs):
    if any(row.get('encoding') != 'byte-spans' for row in directory):
        raise ValueError('Background effects require every frame to use literal bitmap spans')
    writer(path, directory, **kwargs)
    text = path.read_text()
    start, end = text.index('* = $1700'), text.index('* = $4800')
    aliases = ['xchunk_levels = $1700'] + [f'xchunk_mask{i} = ${0x1800+i*256:04x}' for i in range(8)]
    path.write_text(text[:start] + '\n'.join(aliases) + '\n' + text[end:])


def configure(source, *, starfield=False, interactive=False, mode_frames=0, include_starfield=True, variants=()):
    source = once(source, '        cli\n\nmain_loop:', '        jsr fx_init\n        cli\n\nmain_loop:')
    source = once(source, 'irq_no_flip:\n', 'irq_no_flip:\n        jsr fx_irq\n')
    if interactive:
        source = once(source, '        jsr v3_poll\n', '        jsr v3_poll\n        jsr fx_poll\n')
        if not mode_frames:
            source=once(source,'v3_reset:\n',f'v3_reset:\n        lda #{int(starfield)}\n        sta fx_enabled\n')
    if mode_frames:
        if not interactive or not 1 <= mode_frames <= 255//(4+2*len(variants)):
            raise ValueError('Interactive presentation modes exceed the frame index capacity')
        source = once(source, '        jsr v3_advance\n', '        jsr fx_advance\n')
        # F3 keeps its usual foreground slot; zero means the source palette.
        source = once(source, '''        lda v3_shifted+1
        beq v3_key_done
        jmp v3_next_background
''', '''        lda v3_shifted+1
        bne fx_key_background
        jmp fx_next_foreground
fx_key_background:
        jmp v3_next_background
''')
        source = once(source, 'v3_reset:\n', 'v3_reset:\n        jsr fx_reset\n')
        first, last = source.index('v3_prepare_background:\n'), source.index('v3_prepare_slot:\n')
        source = source[:first] + '''v3_prepare_background:
        jsr fx_prepare_lut
        jmp v3_prepare_slot
''' + source[last:]
        source = source.replace('        lda v3_background\n        beq v3_color_copy\n',
                                '        lda fx_mapping_active\n        beq v3_color_copy\n')
    background = '        lda v3_slot_background,x\n' if interactive else '        lda #SCREEN_COLOR & 15\n'
    code = '''
* = $1700
fx_init:
        lda #0
        ldx #62
fx_clear_sprite:
        sta $3f80,x
        sta $7f80,x
        sta $ff80,x
        dex
        bpl fx_clear_sprite
        lda #$80
        sta $3f80
        sta $7f80
        sta $ff80
        lda #$ff
        sta $d01b
        lda #0
        sta $d01c
        sta $d017
        sta $d01d
'''
    if mode_frames:
        code += '        jsr fx_set_frame\n'
    code += '''        rts
fx_irq:
        lda #0
        sta $d015
        sta fx_xhigh
        sta fx_visible
        lda fx_enabled
        bne fx_irq_active
fx_irq_disabled_return:
        rts
fx_irq_active:
        ldx display_slot
''' + background + '''        sta fx_background
        lda fx_screen_hi,x
        sta fx_screen_base
        lda fx_pointer_hi,x
        sta fx_pointer_store+2
        ldx #7
        lda #$fe
fx_pointer_loop:
fx_pointer_store:
        sta $07f8,x
        dex
        bpl fx_pointer_loop
        ldx #7
fx_star_loop:
        inc fx_phase,x
        lda fx_phase,x
        and #63
        sta fx_phase,x
        tay
        lda fx_xlo,x
        sta fx_read_x+1
        lda fx_xhi,x
        sta fx_read_x+2
        lda fx_ylo,x
        sta fx_read_y+1
        lda fx_yhi,x
        sta fx_read_y+2
fx_read_x:
        lda $ffff,y
        sta fx_x
fx_read_y:
        lda $ffff,y
        sta fx_y
        lsr a
        lsr a
        lsr a
        tay
        lda fx_row_lo,y
        sta $f8
        lda fx_row_hi,y
        clc
        adc fx_screen_base
        sta $f9
        lda fx_x
        lsr a
        lsr a
        lsr a
        tay
        lda ($f8),y
        and #15
        cmp fx_background
        bne fx_hidden
        ; VIC sprite priority hides bitmap-set pixels. A non-background low
        ; nibble means the whole cell is filled, so suppress this star too.
        lda fx_visible
        ora fx_bits,x
        sta fx_visible
fx_hidden:
        txa
        asl a
        tay
        lda fx_x
        clc
        adc #24
        sta $d000,y
        bcc fx_x_low
        lda fx_xhigh
        ora fx_bits,x
        sta fx_xhigh
fx_x_low:
        lda fx_y
        clc
        adc #50
        sta $d001,y
        lda fx_phase,x
        lsr a
        lsr a
        lsr a
        lsr a
        tay
        lda fx_star_colors,y
        sta $d027,x
        dex
        bmi fx_publish
        jmp fx_star_loop
fx_publish:
        lda fx_xhigh
        sta $d010
        lda fx_visible
        sta $d015
fx_irq_return:
        rts
'''
    if interactive:
        code += '''fx_poll:
        jsr v3_shift
        beq fx_keys_released
        lda #$fd
        sta $dc00
        lda $dc01
fx_row1_read:
        and #$20
        beq fx_key_s
'''
        if mode_frames:
            code = code.replace('fx_row1_read:\n        and #$20', 'fx_row1_read:\n        sta fx_row\n        and #$20')
            code += '''        lda fx_row
        and #2
        beq fx_key_t
        lda #$fb
        sta $dc00
        lda $dc01
fx_row2_read:
        sta fx_row
        and #$40
        beq fx_key_t
        lda fx_row
        and #2
        beq fx_key_r
        lda #$f7
        sta $dc00
        lda $dc01
fx_row3_read:
        and #4
        beq fx_key_g
'''
        code += '''fx_keys_released:
        lda #0
        sta fx_key_held
        beq fx_keys_done
fx_key_s:
        lda fx_key_held
        bne fx_keys_done
        inc fx_key_held
        lda fx_enabled
        eor #1
        sta fx_enabled
        bne fx_keys_done
        lda #0
        sta $d015
        sta fx_visible
fx_keys_done:
        lda #$ff
        sta $dc00
        sta $dc02
fx_poll_return:
        rts
'''
    if mode_frames:
        code += f'''fx_key_t:
        lda fx_key_held
        bne fx_keys_done
        inc fx_key_held
        lda #0
        sta fx_mode
        sta fx_position
        sta fx_enabled
        sta $d015
        sta fx_visible
        sta fx_foreground
        sta v3_cycle_enabled
        lda #1
        sta v3_background
        sta v3_border_mode
        jsr fx_set_frame
        jmp fx_keys_done
fx_key_g:
        lda fx_key_held
        bne fx_keys_done
        inc fx_key_held
        lda fx_mode
        ora #1
        sta fx_mode
        lda #{int(include_starfield)}
        sta fx_enabled
        lda #0
        sta fx_foreground
        sta v3_background
        sta v3_cycle_enabled
        jsr fx_set_frame
        jmp fx_keys_done
fx_key_r:
        lda fx_key_held
        bne fx_keys_done
        inc fx_key_held
        lda fx_mode
        eor #2
        sta fx_mode
        lda #0
        sta fx_position
        jsr fx_set_frame
        jmp fx_keys_done
fx_reset:
        lda #1
        sta fx_mode
        lda #{int(starfield)}
        sta fx_enabled
        lda #0
        sta fx_foreground
        sta fx_position
        jmp fx_set_frame
fx_advance:
        lda v3_step
        bmi fx_reverse
        inc fx_position
        lda fx_position
        cmp #{mode_frames}
        bcc fx_set_frame
        lda #0
        sta fx_position
        beq fx_set_frame
fx_reverse:
        lda fx_position
        bne fx_decrement
        lda #{mode_frames}
        sta fx_position
fx_decrement:
        dec fx_position
fx_set_frame:
        ldx fx_mode
        lda fx_mode_base,x
        clc
        adc fx_position
        sta frame_index
        rts
fx_next_foreground:
        inc fx_foreground
        lda fx_foreground
        cmp #17
        bcc fx_foreground_done
        lda #0
        sta fx_foreground
fx_foreground_done:
        rts
fx_prepare_lut:
        lda v3_background
        cmp fx_last_background
        bne fx_build_lut
        lda fx_mode
        cmp fx_last_mode
        bne fx_build_lut
        lda fx_foreground
        cmp fx_last_foreground
        beq fx_lut_done
fx_build_lut:
        lda v3_background
        sta fx_last_background
        lda fx_mode
        sta fx_last_mode
        and #1
        eor #1
        sta fx_source_background
        lda fx_foreground
        sta fx_last_foreground
        bne fx_mapping_needed
        lda v3_background
        eor fx_source_background
        beq fx_mapping_chosen
fx_mapping_needed:
        lda #1
fx_mapping_chosen:
        sta fx_mapping_active
        ldy #0
fx_lut_loop:
        tya
        lsr a
        lsr a
        lsr a
        lsr a
        jsr fx_map_nibble
        asl a
        asl a
        asl a
        asl a
        sta fx_high_nibble
        tya
        and #15
        jsr fx_map_nibble
        ora fx_high_nibble
        sta v3_color_lut,y
        iny
        bne fx_lut_loop
fx_lut_done:
        rts
fx_map_nibble:
        cmp fx_source_background
        beq fx_map_background
        sta fx_source_nibble
        ldx fx_foreground
        beq fx_map_done
        dex
        txa
        asl a
        asl a
        asl a
        asl a
        ora fx_source_nibble
        tax
        lda fx_foreground_maps,x
fx_map_done:
        rts
fx_map_background:
        lda v3_background
        rts
fx_mode_base: .byte 0,{mode_frames},{mode_frames*2},{mode_frames*3}
fx_mode: .byte 1
fx_position: .byte 0
fx_foreground: .byte 0
fx_row: .byte 0
fx_last_background: .byte $ff
fx_last_mode: .byte $ff
fx_last_foreground: .byte $ff
fx_source_background: .byte 0
fx_high_nibble: .byte 0
fx_source_nibble: .byte 0
fx_mapping_active: .byte 0
fx_foreground_maps:
'''
        rgb = {i:v for i,v in C64_PALETTE.values()}
        indices = [min(3, round(sum(rgb[i])/3/255*3)) for i in range(16)]
        maps = [shade_codes(c64_color_name(target))[1+indices[i]] for target in range(16) for i in range(16)]
        code += '\n'.join(bytes_lines(maps)) + '\n'
    code += f'''fx_enabled: .byte {int(starfield)}
fx_phase: .byte 0,9,18,27,36,45,54,63
fx_key_held: .byte 0
fx_x: .byte 0
fx_y: .byte 0
fx_xhigh: .byte 0
fx_visible: .byte 0
fx_background: .byte 0
fx_screen_base: .byte 0
fx_bits: .byte 1,2,4,8,16,32,64,128
fx_screen_hi: .byte $04,$44,$c8
fx_pointer_hi: .byte $07,$47,$cb
fx_star_colors: .byte 11,12,15,1
fx_row_lo:
'''
    code += '\n'.join(bytes_lines([y*40&255 for y in range(24)])) + '\nfx_row_hi:\n'
    code += '\n'.join(bytes_lines([y*40>>8 for y in range(24)])) + '\n'
    for axis in ('x', 'y'):
        for part, op in [('lo','<'), ('hi','>')]:
            code += f'fx_{axis}{part}: .byte ' + ','.join(f'{op}fx_{axis}{i}' for i in range(8)) + '\n'
    for i, points in enumerate(trajectories(interactive=interactive)):
        for axis, coord in [('x',0),('y',1)]:
            code += f'fx_{axis}{i}:\n' + '\n'.join(bytes_lines([p[coord] for p in points])) + '\n'
    code += '''fx_end:
.if * > $2000
.error "V3 effects exceed the reclaimed vector lookup RAM"
.endif
'''
    if variants:
        # Additional style pairs use adjacent spin/crawl indices after the
        # original four modes. Colours always retain black space as their base.
        code=once(code,f'fx_mode_base: .byte 0,{mode_frames},{mode_frames*2},{mode_frames*3}',
            'fx_mode_base: .byte '+','.join(str(i*mode_frames) for i in range(4+2*len(variants))))
        code=once(code,'        sta fx_last_mode\n        and #1\n        eor #1\n        sta fx_source_background\n',
            '        sta fx_last_mode\n        tax\n        lda fx_source_backgrounds,x\n        sta fx_source_background\n')
        code=once(code,'fx_foreground_maps:\n','fx_source_backgrounds: .byte '+','.join(map(str,[1,0,1,0]+[0]*(2*len(variants))))+'\nfx_foreground_maps:\n')
        code=once(code,'        lda fx_mode\n        ora #1\n',
            '        lda fx_mode\n        jsr fx_standard_motion\n        ora #1\n')
        code=once(code,'        lda fx_mode\n        eor #2\n',
            '        lda fx_mode\n        cmp #4\n        bcc fx_toggle_standard\n        eor #1\n        jmp fx_motion_selected\nfx_toggle_standard:\n        eor #2\nfx_motion_selected:\n')
        code=once(code,'fx_row3_read:\n        and #4\n','fx_row3_read:\n        sta fx_row\n        and #4\n')
        extra=''
        for index,kind in enumerate(variants):
            key='b' if kind=='card' else 'o';start=4+index*2
            if key=='b':extra+='        lda fx_row\n        and #$10\n        beq fx_key_b\n'
            else:extra+='        lda #$ef\n        sta $dc00\n        lda $dc01\nfx_row4_read:\n        and #$40\n        beq fx_key_o\n'
            handler=f'''fx_key_{key}:
        lda fx_key_held
        bne fx_extra_done_{key}
        inc fx_key_held
        lda fx_mode
        cmp #{start}
        bcc fx_select_{key}
        cmp #{start+2}
        bcs fx_select_{key}
        jsr fx_standard_motion
        ora #1
        jmp fx_extra_set_{key}
fx_select_{key}:
        jsr fx_standard_motion
        and #2
        lsr a
        ora #{start}
fx_extra_set_{key}:
        sta fx_mode
        lda #0
        sta fx_position
        sta v3_background
        sta v3_cycle_enabled
        sta fx_foreground
        ; Style switches preserve whether the user enabled stars.
        jsr fx_set_frame
fx_extra_done_{key}:
        jmp fx_keys_done
'''
            code=once(code,'fx_enabled: .byte',handler+'fx_enabled: .byte')
        code=once(code,'        beq fx_key_g\n','        beq fx_key_g\n'+extra)
        release='fx_keys_released:\n        lda #0\n        sta fx_key_held\n        beq fx_keys_done\n'
        code=once(code,release,'        jmp fx_keys_released\n')
        code=once(code,'fx_poll:\n',release.replace('        beq fx_keys_done','        jmp fx_keys_done')+'fx_poll:\n')
        code=once(code,'fx_enabled: .byte','''fx_standard_motion:
        cmp #4
        bcc fx_standard_done
        and #1
        asl a
fx_standard_done:
        rts
fx_enabled: .byte''')
        # Style handlers live beyond the branch range once all variants exist.
        for key in ('t','r','g','b','o'):
            marker=f'        beq fx_key_{key}\n';serial=0
            while marker in code:
                code=code.replace(marker,f'        bne fx_not_{key}_{serial}\n        jmp fx_key_{key}\nfx_not_{key}_{serial}:\n',1);serial+=1
    if not include_starfield:
        # Presentation controls can remain without any star drawing routine,
        # IRQ call, sprite setup, trajectory data or star keyboard binding.
        source=once(source,'        jsr fx_irq\n','')
        code=code.replace('        sta $d015\n        sta fx_visible\n','')
        first,last=code.index('fx_init:\n'),code.index('fx_keys_released:\n' if variants else 'fx_poll:\n')
        code=code[:first]+'fx_init:\n        jsr fx_set_frame\n        rts\n'+code[last:]
        code=once(code,'        and #$20\n        beq fx_key_s\n','')
        first,last=code.index('fx_key_s:\n'),code.index('fx_keys_done:\n')
        code=code[:first]+code[last:]
        first,last=code.index('fx_phase:'),code.index('fx_end:\n')
        code=code[:first]+'fx_key_held: .byte 0\n'+code[last:]
    return source + code


def describe(manifest, *, starfield=False, mode_frames=0, include_starfield=True, variants=()):
    manifest['background_effect'] = dict(name='starfield-forward' if starfield else 'none',
        implementation='eight hardware sprites; precomputed perspective paths in RAM',
        star_count=8, path_samples=64, clock='PAL raster IRQ; independent of object rotation',
        bitmap_modified=False, sprites_behind_bitmap=True,
        occlusion='sprite priority plus suppress stars in cells whose low colour is not background',
        reclaimed_vector_lut_ram=[0x1700,0x2000], sprite_ram=[0x3f80,0x7f80,0xff80],
        sprite_bytes=192, private_zero_page=[0xf8,0xfa])
    manifest['background_effect']['included']=include_starfield
    if not include_starfield:
        manifest['background_effect']=dict(name='none',included=False,extra_reserved_RAM_bytes=0)
    if manifest.get('interactive_cart') and include_starfield:
        manifest['interactive_cart']['keys']['Shift+S'] = 'toggle forward starfield'
    if mode_frames:
        manifest['presentation_modes'] = dict(samples_per_mode=mode_frames, initial_mode=1,
            modes=['solid-spin','gradient-spin','solid-crawl','gradient-crawl']+[f'{kind}-{motion}' for kind in variants for motion in ('spin','crawl')],
            source_backgrounds=[1,0,1,0]+[0]*(2*len(variants)),variants=list(variants))
        manifest['interactive_cart']['keys'].update({'Shift+T':'solid source colours, white background, stars off, axis spin',
            'Shift+W':'same white-background axis presentation as Shift+T',
            'Shift+G':'source-colour gradients, black background, stars on',
            'Shift+R':'toggle spin / perspective crawl', 'F3':'next foreground hue overlay; cycle back to source colours'})
        if not include_starfield:
            manifest['interactive_cart']['keys']['Shift+G']='source-colour gradients, black background'
        for kind in variants:
            manifest['interactive_cart']['keys']['Shift+B' if kind=='card' else 'Shift+O']=f'toggle {kind} / gradient presentation, preserving spin/crawl and starfield on/off state'
