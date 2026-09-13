"""Boot-only V3 title: v0.7.8 layout, explicit SPACE start, optional help row."""
from .buildscreen import build_screen_lines
from .demo_colors import once


def configure(source, boot, *, version, interactive):
    # Borrow the first bitmap's RAM only until video initialization clears it.
    # Nothing is added to drawing, input polling or the playback IRQ.
    lines = ['* = $2000', 'v3_intro_start:']
    if interactive:
        # Copy help/speed/HUD before the intro can open help. Retain the same
        # three-byte startup call site and all renderer entry point addresses.
        source = once(source, '        jsr sp_boot_copy\n',
                      '        jsr v3_intro_start\n')
        lines += ['        jsr sp_boot_copy']
    else:
        boot = once(boot, '        jmp $080d\n',
                    '        jsr $2000\n        jmp $080d\n')
    lines += build_screen_lines(version, 'hors-renderer-v3',
                                help_handler='v3_intro_help' if interactive else None)
    i = lines.index('        and #$10', lines.index('build_screen_leave:'))
    lines.insert(i, 'build_screen_space_read:')
    # Do not carry a held SPACE through to playback. This also lets help close
    # with SPACE without accidentally starting the demo underneath it.
    i = lines.index('build_screen_done:') + 1
    lines[i:i] = ['build_screen_space_release:', '        lda $dc01',
                  '        and #$10', '        beq build_screen_space_release']
    i = lines.index('        rts', lines.index('build_screen_done:'))
    lines.insert(i, 'build_screen_return:')
    if interactive:
        lines += ['v3_intro_help:', '        jsr hp_stop_poll', '        jsr v3_shift',
                  '        beq v3_intro_help_return',
                  '        lda #$f7', '        sta $dc00', '        lda $dc01',
                  'v3_intro_h_read:', '        and #$20',
                  '        bne v3_intro_help_return', '        jmp hp_open',
                  'v3_intro_help_return:', '        rts']
    lines += ['.if * > $2200', '.error "Startup screen overlaps bootstrap staging"', '.endif']
    return source + '\n' + '\n'.join(lines) + '\n', boot


def describe(manifest, version, *, interactive):
    manifest['build_screen'] = dict(version=version, renderer='hors-renderer-v3',
        wait_for_space=True, layout='v0.7.8', screen_ram=[0x400, 0x800],
        help_hint='press SHIFT+H for help' if interactive else None,
        help_row=19 if interactive else None, start_row=20,
        startup_only_ram=[0x2000, 0x2400], extra_playback_RAM_bytes=0,
        playback_cycle_cost=0)
