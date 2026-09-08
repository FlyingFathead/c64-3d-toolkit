# yunroll-cart-v7: join runs, clear fewer bytes, choose FPS or RAM

Toolkit **0.6.7** ships `yunroll-cart-v7` and `yunroll-cart-v7-scene`, with
PLAY ALL and a ten-second closing screen between rounds. The renderer and
the matched rc4 measurements below are unchanged by finalization.
**`--prefer fps` is the default.** V4/V5/V6 renderer assembly remains in the
project; older menu cartridges are preserved in the external oldies ZIP. The default renderer for the general
`cart-demos` command remains V4; select V7 explicitly or use its example builder.

## The three experiments retained

1. **Lossless run joining.** After V5 redundant-record removal, the host joins
   compatible connected paths under one existing line-record header. Both paths
   must share a major axis and a monotonic minor direction, touch at an endpoint
   or the next adjacent pixel, and fit the 127-pixel record limit. The existing
   packed step bits preserve the exact path, including changes in slope. The
   compiler tries input order and position order, then selects fewer records,
   breaking ties by byte count and raw pixels. It never fits a replacement line.
   It decodes every joined path and compares the whole bitmap and resolved cell
   colours with the original. Clear/colour metadata remains attached to the
   original picture. This is the main measured FPS and cartridge-size gain.
2. **Selective byte clearing.** Each old cell span can become a trimmed byte
   range when a host cost estimate favours it. The three-byte span size and
   number of metadata records remain unchanged. Dense areas keep cell clearing.
   The selector estimates 69 cycles per cell versus 11 per byte, with an
   eight-cycle margin; these are selection costs, not fresh emulator timings.
   The selective-clearing-only experiment measured roughly -0.02% to +0.72%
   across the twelve demos, so its benefit is small next to run joining.
3. **Optional smaller Y kernels.** `--prefer ram` replaces the Y phase bodies
   and full Y blocks with two compact loops. The X byte kernels remain intact.
   Every pixel, colour and logical animation sample is preserved. This reduces
   resident code, with a measured FPS cost; it is useful to demos as well as games.

V5's picture dictionary, resident reuse and hold timing are inherited. Joining
records does not drop animation samples. The menu retains every original sample,
including 128 orientations in each HiFi entry; Marbles retains all 200 samples.
Region deltas against a recycled bitmap and broader compact/game integration
profiles remain future work. V7 does not implement every idea in the roadmap.

## Stream format and RAM

A clear span is still `(offset_low, offset_high, count)`. Bit 7 of its high byte
now means a byte range instead of a cell range; strip it before forming the
bitmap address. Geometry offsets are below 7680. The production selector emits
byte counts 1..255; the byte loop also supports 0 meaning 256, tested explicitly.
Untagged records retain their original cell-count meaning. Colour spans, frame
directories and packed line headers/step bits retain their existing layout.
**V7 clear metadata requires the V7 renderer.** Do not feed its stream to V6.

The runtime still clears the old recycled slot before loading new metadata
straight into that slot's cache. Cartridge copies remain bounded to 256 bytes,
with cartridge-off / `$01=$35` restored between bursts. No extra bitmap or
lookup table is allocated.

Matched regular horse code sizes (includes its unchanged HUD):

| Resident region | V6 | V7 FPS | V7 RAM |
| --- | ---: | ---: | ---: |
| Main runtime/HUD, from `$0801` | 3,570 | 3,608 | 2,828 |
| Cold negative-Y block, at `$5c00` | 272 | 272 | 0 |

FPS mode adds **38 renderer bytes** versus V6. RAM mode saves **1,052 code
bytes** versus V7 FPS, in two regions: 780 bytes below `$1700`, and 272 bytes
at `$5c00`. Fixed tables/buffers are not relocated or reclaimed automatically.
The allocations remain three 8 KiB bitmaps, three 1 KiB screen areas, 8 KiB of
line staging and three 1 KiB metadata caches. This is a kernel-size preference,
not a complete memory-budgeted game renderer.

The menu's PLAY ALL timer occupies 41 bytes at `$c700`, within its existing
`$c000-$c7ff` shared area. The V7 control shim grows six bytes, still fits its
existing `$0200-$02f7` region, and uses the three previously spare state bytes
`$02fd-$02ff`. Standalone Marbles does not install this menu/timer.

## Matched PAL VICE results

VICE 3.10 `x64sc`, PAL, 64tass 1.59.3120. Menu measurements use two complete
loops plus three frames per entry, excluding startup. Every completed bitmap
and all 960 geometry colour cells are compared with the frozen V6 build's
original pre-optimization oracle, across all three slots. Sampling, colours,
meshes and hires resolution are unchanged. Final numbers include the menu
control shim with PLAY ALL inactive, as for a manually launched demo.

These are completed-frame throughput measurements. Longest intervals include
queueing and IRQ work, not just line drawing. Host display smoothness and
physical C64/NTSC behaviour were not measured.

| Demo | V6 FPS | V7 FPS (default) | Gain | V7 RAM FPS | V6 / V7 FPS longest interval, cycles |
| --- | ---: | ---: | ---: | ---: | ---: |
| TORUS | 12.771 | 13.505 | 5.75% | 12.898 | 90,183 / 84,472 |
| TORUS DENSE | 11.298 | 12.105 | 7.14% | 11.581 | 102,422 / 96,425 |
| CUBE | 27.092 | 27.136 | 0.16% | 24.847 | 40,908 / 40,546 |
| SPHERE | 14.423 | 14.787 | 2.52% | 13.542 | 75,046 / 70,687 |
| HORSE HEAD | 12.949 | 13.874 | 7.15% | 12.779 | 89,986 / 83,556 |
| SUNFLOWER TORUS | 11.144 | 12.122 | 8.78% | 11.138 | 99,380 / 92,282 |
| SUNFLOWER COLOR | 9.786 | 10.522 | 7.53% | 9.744 | 113,706 / 105,972 |
| SPACE HORSE SPIN | 10.573 | 10.669 | 0.91% | 10.031 | 106,362 / 106,088 |
| SPACE HORSE CRAWL | 15.534 | 16.623 | 7.01% | 16.295 | 84,502 / 80,743 |
| FALLING CUBES | 14.063 | 14.275 | 1.51% | 13.760 | 89,529 / 88,436 |
| HORSE HEAD HIFI | 8.742 | 10.018 | 14.61% | 9.268 | 127,186 / 110,350 |
| SUNFLOWER TORUS HIFI | 6.139 | 6.989 | 13.86% | 6.560 | 211,811 / 185,186 |

RAM mode costs about 2–8.6% of V7 FPS throughput across this set. Some RAM-mode
entries still beat V6 because the stream improvements save more work than the
compact kernels add. Use FPS mode for maximum measured speed.

| Cartridge | V6 CRT bytes | V7 CRT bytes | Saved |
| --- | ---: | ---: | ---: |
| Twelve-demo menu | 927,568 | 804,448 | 123,120 (13.27%) |
| Marbles, clean | 418,672 | 353,008 | 65,664 (15.68%) |
| Marbles, HUD | 418,672 | 353,008 | 65,664 (15.68%) |

FPS and RAM cartridges have the same stored CRT sizes because the code savings
fit within already allocated chips. Menu vector payload falls from **538,330
to 434,323 bytes**; Marbles falls from **323,159 to 274,770 bytes**. The compiler
joins 20,917 records across all menu samples and 9,698 in Marbles. The menu ROM
figure counts unique stored pictures; the joining totals count logical samples.
The EasyFlash target remains 1 MiB; CRT files omit unused chips.

## Marbles: faster rendering under the same cadence

The 200 samples retain seven PAL ticks each, with the original intro, credits
and finite ending. The table excludes the intro/credits and includes the final
scene hold. The render budget is 137,592 cycles; exceeding it measures work,
not an exact count of late displayed frames.

| Clean Marbles measurement | V6 | V7 FPS | V7 RAM |
| --- | ---: | ---: | ---: |
| Mean render cycles | 137,811.51 | 125,940.87 | 131,145.88 |
| Worst render cycles | 297,383 | 282,700 | 304,801 |
| Samples above render budget | 93 | 47 | 62 |
| Scene seconds | 31.42851 | 30.45095 | 30.86990 |
| Samples per second | 6.36365 | 6.56794 | 6.47880 |

FPS mode reduces mean render cost by **8.61%** and
raises scene throughput by **3.21%**. Frames that finish
before the presentation deadline still wait, so throughput gain is smaller.
Both clean and HUD builds pass all 200 original bitmap/colour comparisons.

## PLAY ALL and menu controls

V7 starts with **PLAY ALL** selected above the ten-row scrolling list. RETURN
starts it; every demo runs for **10 seconds by default**, then the next loads.
The last entry is followed by a ten-second THANK YOU FOR WATCHING screen,
then the first demo starts again. The timer waits for the first visible
rendered picture before starting; loading and initialization are excluded.
It counts 50 PAL raster ticks per configured second, approximately wall-clock
seconds on PAL. Duration is configurable at build time, from 1 to 255 seconds.

| Where | Key | Action |
| --- | --- | --- |
| Menu | Cursors | Select PLAY ALL or an individual demo |
| Menu | RETURN | Launch selection |
| Menu | F1 | Cycle default → decorative → demoscene/party → default |
| Animation | SPACE | Skip to next; PLAY ALL continues if active |
| Animation | RUN/STOP or F1 | Stop PLAY ALL and return to the current menu style |
| Closing screen | F1 | Return to the same menu style |

The closing screen is always white on black, including after the flashing
party menu. It shows the build version and repository URL. Its 500-tick pause
is independent of `--play-all-seconds`. Manual SPACE wrapping does not add this
pause. F1 release is consumed before returning so it does not also cycle styles.

VICE's Escape key can serve as RUN/STOP according to the selected host keymap;
there is no separate native C64 Escape key. Manually launched demos keep looping
until a control key is pressed. A held SPACE is latched across a handoff so it
does not skip multiple animations. PLAY ALL is a multi-demo menu feature;
Marbles remains a separate finite presentation.

## Run and rebuild

From the project root:

```bash
x64sc -cartcrt examples/cart_demos/history/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
x64sc -cartcrt examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v7-scene-clean.crt

# FPS is already the default; original samples, no Blender rebake:
python tools/build_v7_examples.py
# Choose a different PLAY ALL duration:
python tools/build_v7_examples.py --play-all-seconds 20
# Optional RAM comparison; output names gain -ram:
python tools/build_v7_examples.py --prefer ram

# Normal compiler entry points also support V7:
./build.sh cart-demos --stream-renderer yunroll-cart-v7 --play-all-seconds 10
python c643d.py cart-stream --renderer yunroll-cart-v7 --object horse_head --prefer fps
```

The example builder reads the original V4 vector samples from the checksum-verified
`assets/v4-menu-vector-reference.json.gz` before applying V5/V7 optimizations.
This compact host asset replaces the old menu CRT as the default build input.
It needs 64tass and VICE's `cartconv`, but no Blender installation. Six ready
cartridges are supplied: FPS/RAM menus and FPS/RAM clean/HUD Marbles. RAM
build screens identify `yunroll-v7 (ram)`; all show toolkit `0.6.7`, white
on black, for about three seconds or SPACE to skip.

## Verification

The full renderer matrix below was measured on rc4. Final v0.6.7 rebuilds
retain the same runtime, vector samples and menu logic with updated version
text. Fresh final-menu checks are in [reports/](../examples/cart_demos/reports/):
121 Python tests, 84 launches/252 rendered-picture comparisons across all
three menu styles, the timed PLAY ALL cycle, six closing-screen cases and
timeout/SPACE checks for all six final build screens passed.
Historical rc4/rc5 evidence remains in
[docs/benchmarks/cart_demos/](benchmarks/cart_demos/).

- 118 Python unit tests passed.
- Both preferences: all 12 menu demos against frozen V6 oracles, two loops plus
  three frames each, original sample order, all slots and wraparound.
- Both preferences: 1,744 synthetic X/Y and byte-clear cases, 3,491 completed
  frames each; phase, sign, length and byte/page boundaries, including 256-byte clears.
- Both preferences: a 270-sample reuse scene, 231 resident hits, consecutive
  holds, colour-only changes and the 16-bit directory crossing. The measured
  16.186-second hold duration remains within 0.1 second of the 16.160-second budget.
- Ordinary V7 stream edge cases: zero/one/255/256/257/512 runs, 255 clear
  spans, 1,024-byte metadata, and a 255-frame directory.
- All six build screens: white-on-black text, timeout, SPACE scanner and handoff.
- All four Marbles builds: 200 bitmap/colour/HUD comparisons; both clean
  builds also pass the complete ending, greeting correction and BASIC epilogue.
- 81 menu states: all three styles, scrolling/wrap, fixed PLAY ALL and footer.
- 72 menu launches plus 12 next-demo launches across two full style cycles:
  exact loaded payloads, 252 rendered pictures, no CPU JAM, animated menu IRQ
  running during idle and disabled before renderer handoff.
- PLAY ALL: all twelve entries plus wrap at the default ten seconds; a separate
  two-second build starts in the flashing party style and repeats the cycle.
  Both check SPACE skip, latch state, RUN/STOP return and subsequent manual play.
  Invalid zero/negative/256-second settings are rejected. Native handlers/CIA
  scanners are exercised through VICE's monitor, not the host Escape key mapping.

Reports: [V6/V7 menu comparison](benchmarks/cart_demos/v6-v7-validation.json),
[Marbles comparison](../examples/cart_marbles/history/v6-v7-validation.json),
[menu navigation](benchmarks/cart_demos/menu-v7-validation.json),
[menu launch regression](benchmarks/cart_demos/menu-launch-v7-validation.json),
[PLAY ALL](benchmarks/cart_demos/play-all-v7-validation.json).

```bash
python -m unittest discover -s tests
python tools/verify_v7_kernels.py --vice-data /path/to/vice-data
python tools/verify_v7_kernels.py --prefer ram --vice-data /path/to/vice-data
python tools/verify_cart_menu_launch.py examples/cart_demos/history/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt --vice-data /path/to/vice-data
python tools/verify_v7_play_all.py examples/cart_demos/history/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt --vice-data /path/to/vice-data
```

## Update an existing checkout

See [upgrading to v0.6.7](UPGRADING_0.6.7.md) for the flat changed-files overlay,
external oldies archive, cleanup command and local commit/tag/push instructions.
The scene cartridge remains separate from the twelve-demo menu.
