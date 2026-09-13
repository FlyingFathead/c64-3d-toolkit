# v0.7.9: The Golden Dragon & SAKU 2026 — release_final_v3

The SAKU cart now offers both the original light starfield and the fuller field.
Press **4** to switch them during playback. Both routines and both trajectory
sets are loaded into RAM at startup; switching updates the existing IRQ call
operand and sprite pattern on the key event. It does not reload the cartridge.
The fuller field remains the default.

| Key | Action |
| --- | --- |
| `4` | Switch light / full stars, remembering each density and on/off state |
| `1` | Reset the current field: light 8 points, full 16 |
| `2` | More stars: light up to 8, full up to 32 |
| `3` | Fewer stars, down to 2 |
| Shift+S | Toggle stars; disable hardware sprites immediately |
| Shift+H | Help, now including the `4` shortcut |
| Shift+U | Hide/show all HUD text, including INTERACTIVE |

The original intro still waits indefinitely for SPACE. The help shortcut
remains on its own row above the start prompt. All eight SAKU presentations,
rotation speed controls, colour controls, white outlines and rounded card remain.
Shared HORS-V3 interactive builds gain the same light/full choice. Stars start
disabled unless requested; `--no-starfield` excludes both fields and their keys.

## Measured cost

Same SAKU cart, normal speed, HUD shown, 750 PAL refreshes after warmup:

| Field | Displayed FPS | Average visible points |
| --- | ---: | ---: |
| Off | **18.18** | 0.00 |
| Original light, 8 points | 15.91 | 4.03 |
| Full, 16 points (default) | 13.70 | 10.98 |

Light improves throughput by **16.1%** over full on this animation. Compared
with stars off, light costs 12.5% of displayed throughput and full costs 24.6%.
The light IRQ averages 1,826.66 elapsed cycles versus 3,977.12 for full; both
off paths take 32. These measurements include VIC-II contention and call/return.
They are VICE results, not physical-hardware measurements.

The new key adds 13 CPU cycles per idle input poll and needs no additional CIA
row read. Switching adds zero per-refresh dispatch instructions. Light paths
use **1 KiB extra RAM** at `$8000..$83ff`; the light kernel fits the existing
`$9c00..$9fff` density reservation. The cartridge uses **440 KiB allocated ROM**
with **584 KiB free**, unchanged from final v2.

Matched ordinary interactive torus builds measure 9.60 FPS with stars excluded,
9.57 with stars included but disabled, and 7.47 with the full field enabled.
The included-disabled difference is one displayed frame in the roughly
30-second window (288 versus 287 flips, about 0.35%). It is small and near
the measurement resolution, but not claimed to be zero overhead.

[SAKU README](../examples/saku_2026/README.md),
[detailed performance](../examples/saku_2026/PERFORMANCE.md),
[raw comparison](../examples/saku_2026/evidence/starfield-comparison.json), and
[full renderer comparison](PERFORMANCE_COMPARISON.md) contain the results.
The SAKU directory includes fresh full and light GIFs captured from actual VIC output.

## Border dots

The border dots were reproduced with the sprite-enable register already zero.
A controlled test replaced repeated border/background colour stores with
same-duration reads; the dots disappeared. The shared display routine now
writes those registers only when their colours change. Its idle comparisons
add six CPU cycles per PAL refresh. The sprite-off handler also disables
hardware sprites immediately. Both VICE keymaps pass the sprite-register and
rendered-border checks after toggling stars, switching fields and closing help.

## Verification and contents

The release records include 262 unit tests (3 expected skips), all 18 V3
cold-boot/SPACE checks, full SAKU bitmap/colour/occlusion/control checks,
72 host-key state checks across VICE's symbolic and positional keymaps,
shared interactive Pretzel measurements, the star/HUD option matrix,
Dragon verification and the complete uncapped renderer comparison.

Three CRTs are rebuilt: SAKU interactive and both interactive Pretzel variants.
The other 63 CRTs are byte-identical to final v2. Unchanged Pretzel measurement
reuse is explicitly recorded and tied to verified cartridge/evidence hashes.
Historical results remain under `docs/benchmarks/`.

The full ZIP contains the complete project. The incremental ZIP is cumulative
against the supplied v0.7.8 baseline. No remote commit, tag or release is made.
