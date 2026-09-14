"""Observe actual displayed buffers and PAL holds, separately from preparation."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from .gmod3_probe import labels, vice_command

CLOCK = 985248
PAL_CYCLES = 19656


def display_capture(crt, oracle, *, vice, vice_data, out, refreshes=1600):
    from verify_cart_stream import expected_frame, apply_interactive_overlay, render_ram, startup_monitor
    from PIL import Image
    crt, out = Path(crt).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    sym = labels(crt.with_suffix('.lbl'))
    frames = json.loads(Path(oracle).read_text())
    expected = []
    for f in frames:
        bm, sc = expected_frame(f, manifest['screen_color'])
        expected.append(bytes(apply_interactive_overlay(bm, manifest))+sc)
    digest = hashlib.sha256(crt.read_bytes()).hexdigest()
    transitions, ticks = [], []
    with tempfile.TemporaryDirectory(prefix='gmod3-display-') as td:
        tmp = Path(td)
        startup, go = startup_monitor(manifest, sym)
        commands = ['delete', *startup, f'break ${sym["profile_published"]:04x}', go,
                    *(['g']*(len(frames)+5)), 'delete', f'break ${sym["irq_no_flip"]:04x}']
        for i in range(refreshes+1):
            commands += ['g', 'stopwatch', 'bank ram',
                f'bsave "{tmp/f"{i}.ram"}" 0 $0000 $ffff', 'bank cpu',
                f'bsave "{tmp/f"{i}.io"}" 0 $d000 $dd03']
        commands += ['quit']
        (tmp/'run.mon').write_text('\n'.join(commands)+'\n')
        with (tmp/'vice.log').open('w') as output:
            proc = subprocess.run(vice_command(vice, crt, vice_data)+[
                '-initbreak', 'reset', '-moncommands', str(tmp/'run.mon'), '-monlogname', str(tmp/'monitor.log'), '-monlog', '-limitcycles', str(refreshes*19656+100000000)],
                stdout=output, stderr=subprocess.STDOUT, timeout=120)
        trace = (tmp/'monitor.log').read_text() if (tmp/'monitor.log').exists() else ''
        ticks = [int(t) for t in re.findall(r'Stopwatch:\s*(\d+)', trace)]
        if proc.returncode or len(ticks) != refreshes+1:
            raise RuntimeError('Display observation failed: '+(tmp/'vice.log').read_text()[-1800:])
        slots, orientations, previous = set(), set(), None
        for i in range(refreshes+1):
            ram, io = (tmp/f'{i}.ram').read_bytes(), (tmp/f'{i}.io').read_bytes()
            slot = ram[sym['display_slot']]
            if slot not in (0,1,2):
                raise AssertionError('Invalid displayed slot')
            fi = ram[sym['slot_frame']+slot]
            baddr, saddr = (0x2000,0x6000,0xe000)[slot], (0x400,0x4400,0xc800)[slot]
            if fi >= len(frames) or ram[baddr:baddr+7680]+ram[saddr:saddr+960] != expected[fi]:
                raise AssertionError(f'Displayed picture mismatch at refresh {i}, frame {fi}, slot {slot}')
            if io[0xd00]&3 != (3,2,0)[slot] or io[0x18]&0xfe != (0x18,0x18,0x28)[slot]:
                raise AssertionError('VIC bank and displayed slot disagree')
            slots.add(slot); orientations.add(fi)
            if slot != previous:
                if transitions and fi != (transitions[-1][1]+1) % len(frames):
                    raise AssertionError('Default display skipped/reordered an orientation')
                transitions.append((i, fi, render_ram(ram, slot)))
            previous = slot
    if slots != {0,1,2} or orientations != set(range(len(frames))):
        raise AssertionError('Display observation did not cover all frames and slots')
    if hashlib.sha256(crt.read_bytes()).hexdigest() != digest:
        raise AssertionError('Display test changed the cartridge')
    zeros = [i for i, item in enumerate(transitions) if item[1] == 0]
    if len(zeros) < 2:
        raise ValueError('Increase refreshes to capture a complete steady-state loop')
    start, end = zeros[:2]
    holds = [transitions[i+1][0]-transitions[i][0] for i in range(start,end)]
    elapsed = 0
    boundaries = [0]
    for hold in holds:
        elapsed += hold
        boundaries.append(round(elapsed*PAL_CYCLES/CLOCK*100))
    durations = [(b-a)*10 for a,b in zip(boundaries,boundaries[1:])]
    pictures = [t[2].resize((640,400),Image.Resampling.NEAREST) for t in transitions[start:end]]
    if len(pictures) != len(frames) or min(durations) < 20:
        raise AssertionError('Invalid GIF loop or browser-clamped timing')
    pictures[0].save(out/f'{crt.stem}.png')
    pictures[0].save(out/f'{crt.stem}.gif',save_all=True,append_images=pictures[1:],duration=durations,loop=0)
    report = dict(passed=True, cartridge=crt.name, crt_sha256=digest, observed_refreshes=refreshes,
        clock_hz=CLOCK, pal_cycles=PAL_CYCLES, elapsed_monitor_cycles=ticks[-1]-ticks[0],
        displayed_frames=len(transitions)-1,
        displayed_fps=(len(transitions)-1)/(refreshes*PAL_CYCLES/CLOCK),
        all_orientations=True, all_three_slots=True, bitmap_and_color_match=True,
        default_forward_sequence=True, loop_holds_pal_ticks=holds,
        gif_duration_ms=sum(durations), actual_loop_seconds=sum(holds)*PAL_CYCLES/CLOCK,
        scope='Actual VIC display slots sampled after each raster publication; one full warmup turn; native frame holds')
    (out/f'{crt.stem}-display.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
