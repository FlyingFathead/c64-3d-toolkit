# v0.7.9: The Golden Dragon & SAKU 2026 — release_final_v2

This correction keeps the v0.7.8 introduction layout and indefinite SPACE wait.
The separate `press SHIFT+H for help` row remains directly above `SPACE to start`.
All eight SAKU presentations remain on one EasyFlash cartridge.

| Key | Action |
| --- | --- |
| `1` | Reset star density to 16 |
| `2` | More stars, up to 32 |
| `3` | Fewer stars, down to 2 |
| Shift+S | Toggle stars |
| `+` / `-` / `0` | Rotation speed up / down / reset |
| Shift+U | Hide all HUD text; press again to restore all, including INTERACTIVE |
| Shift+I | Toggle only the lower-left name and V:/E: counts |
| Shift+F | Toggle only FPS and speed messages |
| Shift+H | Open/close help; Space also closes help |
| Shift+B | Padded, rounded white card; preserve rotation/crawl selection |

The number keys replace the shifted density shortcuts. VICE's supplied GTK
symbolic keymap marks `plus` with its "deshift" flag, which can defeat a
Shift-plus binding. Number keys need no modifier. The verification now sends
host keysyms through VICE's keyboard event API and both its symbolic and
positional keymaps, then reads the resulting cartridge state. It does not
inject CPU register values for those checks. Operating-system GUI event
handling and physical C64 hardware are not claimed as tested.

The help header has full-width light-blue and cyan stripes with black text.
Reverse ROM characters include the spaces, so each stripe spans all 40 columns.
This adds work only when help opens. HUD hiding patches draw entry points to
RTS and clears all three buffers once; no new per-frame visibility branch.
The `--hide-hud` initial state now also hides INTERACTIVE.

The card adds 8-point horizontal and 6-point vertical padding, with 5-point
corner radii. `examples/saku_2026/saku_2026-rounded-card.svg` is the presentation
source; the original rectangular reference and transparent variants remain.

## Starfield and performance

Interactive stars now have irregularly spaced directions, unequal 43–64-refresh
lifetimes, and two-pixel-wide near stars. Their lookup tables are still built on
the host; there is no runtime division or 3D projection. Higher densities remain
small groups sharing eight sprite trajectories. Both pixels of wider stars are
protected by the colour-cell and opaque-logo checks. The additional near-star
pattern needs 64 bytes per VIC bank: 192 bytes total, after bitmap data and away
from the CPU vectors.

Same SAKU cart, default speed, HUD visible, 750 PAL refreshes after warmup:

| Stars | Displayed FPS | Average visible stars |
| --- | ---: | ---: |
| off | **18.18** | 0.00 |
| 2 | 17.38 | 1.10 |
| 8 | 14.97 | 5.74 |
| 16 (default) | 13.70 | 10.97 |
| 32 | 12.16 | 17.40 |

The previous final_v1 default measured 14.77 FPS with 6.94 visible stars.
This version makes the field fuller, with a 7.2% throughput cost at the default.
With all HUD text hidden, the new default measures 14.03 FPS; without stars,
18.71 FPS. Rounded-card spin measures 11.36 FPS and card crawl 14.17 FPS.
These are elapsed PAL VICE measurements, including VIC-II DMA.

The number-key scan adds 46 CPU cycles per idle input poll (not per raster
refresh). The disabled-star IRQ path remains 32 elapsed cycles including
call/return. `--no-starfield` still excludes star and density code entirely;
help, speed controls, and HUD toggles remain available.

The SAKU cart uses **440 KiB** of allocated ROM slots; **584 KiB** remains
(80 KiB ROML and 504 KiB ROMH). Its padded card costs one additional 8 KiB slot
relative to final_v1. These figures describe cartridge ROM allocation, not the
CRT container's header overhead.

## Validation

- 262 unit tests, with 3 expected skips.
- Cold-boot introduction/SPACE checks on all 18 V3 carts.
- Full SAKU picture, colour, help, HUD, speed, density, occlusion, and GIF checks.
- Host-key translation in both supplied GTK VICE keymaps; held keys and limits.
- Rebuilt and verified the two shared interactive Pretzel carts.
- Rechecked star exclusion/defaults, fixed/toggle HUD states, and the Dragon examples.
- Updated `PERFORMANCE_COMPARISON.md` from the complete renderer comparison.

Only three supplied CRTs change: SAKU interactive and the two HORS-V3 interactive
Pretzel variants. The other 63 CRTs are byte-identical to final_v1. Earlier
release records remain under `docs/benchmarks/`; current results are linked from
`docs/benchmarks/release-final-v2/validation.json`.

No remote commit, tag, push or release is performed by these correction archives.
