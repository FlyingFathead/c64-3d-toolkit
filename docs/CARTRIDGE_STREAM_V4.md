# Uniform comparison cartridges and yunroll-cart-v4

Toolkit version remains **0.6.4**; the renderer suffix identifies the algorithm.
`cart-demos` defaults to **V4 for every entry**. Select V3 explicitly to produce
the matched baseline. Each filename and menu title identifies its renderer.

```bash
./build.sh cart-demos --stream-renderer yunroll-cart-v3
./build.sh cart-demos --stream-renderer yunroll-cart-v4
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v4-all.crt
```

## What changed

V4 inlines line dispatch into the drawing loop and returns from each drawing
kernel directly to the loop continuation. This removes a per-line JSR/RTS pair
in favour of a JMP, saving nine cycles per visible run before alignment/IRQ
interactions. Its format, culling and RAM capacities match V3. It is a modest
increment on V3, not a new compression format or a large FPS jump.

The uniform builder reads the ten canonical PRGs' original vector tables,
including the Blender falling-cubes and SVG examples. It validates their known
pointer layout, metadata coverage, run coordinates and HUD signatures. This is
a restricted importer for these toolkit PRGs, not a general-purpose PRG decoder.
The original PRG files are unchanged. Original camera framing, colours,
visibility and sample counts are retained. Both HiFi meshes are compiled with
128 orientations and their established surface-based hidden-line culling.

All twelve entries run the selected stream renderer. There is no silent fallback
to another method and no automatic reduction of samples to make the cart fit.
The V3 and V4 manifests have identical frame bytes, hashes and ROM locations.
Standalone `cart-stream --renderer yunroll-cart-v4` is also supported; the
standalone command retains its existing V2 default.

## Matched PAL VICE measurements

Each entry was checked over two complete cycles plus three frames, against the
host bitmap and colour oracle in all three screen buffers. FPS uses emulator
cycle counts at 985,248 cycles/second, including runtime and cartridge control
IRQ work; emulator warp changes host execution speed, not these cycle counts.
These figures are rendering throughput, not a promise of perfectly even frame
presentation. Physical hardware has not been tested here.

| Demo | Samples | V3 FPS | V4 FPS | Gain |
|---|---:|---:|---:|---:|
| TORUS | 32 | 12.019 | 12.077 | 0.49% |
| TORUS DENSE | 32 | 10.621 | 10.686 | 0.61% |
| CUBE | 36 | 24.939 | 24.957 | 0.07% |
| SPHERE | 24 | 13.239 | 13.274 | 0.26% |
| HORSE HEAD | 32 | 11.685 | 11.793 | 0.93% |
| SUNFLOWER TORUS | 28 | 10.362 | 10.460 | 0.94% |
| SUNFLOWER COLOR | 20 | 8.893 | 8.965 | 0.81% |
| SPACE HORSE SPIN | 24 | 9.401 | 9.492 | 0.97% |
| SPACE HORSE CRAWL | 32 | 14.205 | 14.432 | 1.60% |
| FALLING CUBES | 18 | 12.875 | 12.965 | 0.70% |
| HORSE HEAD HIFI | 128 | 7.998 | 8.078 | 1.00% |
| SUNFLOWER TORUS HIFI | 128 | 5.525 | 5.599 | 1.34% |

Reports: `examples/cart_demos/uniform-v3-validation.json` and
`uniform-v4-validation.json`. The older V3 standalone measurements used 192
orientations and a different cartridge control path; use the table above for
this matched comparison.

## ROM and RAM

Frame blocks occupy **580,017 bytes**. Each block remains within one 8 KiB ROM
chip window. Each entry has a three-bank RAM bootstrap; ROMH and spare ROML
chips provide a shared frame pool. The loader selects 16K or 8K cartridge mode
from the source chip before copying into the fixed staging buffer.

| Allocation | Location |
|---|---|
| Boot, control shim, menu font | Bank 0 |
| Three 2 KiB main menu style images | ROMH bank 1 |
| Three 2 KiB shared menu helpers/directories | ROMH bank 2 |
| Twelve three-bank runtime bootstraps | ROML banks 1–36 |
| Frame pool, allocated in this order | ROMH 3–63, then ROML 37–63 |
| Main renderer, HUD and hot code | RAM below $1700 |
| Drawing lookup tables | $1700–$1FFF, $4300–$43FF, $4F00–$4FFF |
| Cold reset and stream helper | $4000–$42FF |
| Frame directory, at most 255 entries | $4800–$4EF8 |
| Three 1 KiB metadata caches | $5000–$5BFF |
| Fixed frame staging | $A000–$BFFF |
| Menu shared helpers/main code while browsing | $C000–$CFFF |
| Menu character/colour shadows while browsing | $0800–$098F, $0C00–$0D8F |

Three bitmap/screen pairs retain the V3 allocation. The menu memory is reused
between demo launches; shared menu code is reloaded when returning. No animation
length-dependent allocation is added to RAM. The directory still limits one
animation to 255 frames, and metadata to 1,024 bytes per frame.

## Scrolling menu

All three styles show ten entries between fixed horizontal borders. Scrolling
keeps the selected item visible; navigation wraps at either end. A `+` at a
border indicates more entries beyond it. Header, help and footer remain fixed.

Navigation builds the character and colour rows in shadow buffers, waits until
the raster has passed the visible list, and copies them to the screen. It does
not clear the screen, change VIC banks or blank the display on each keypress.
A full redraw is still appropriate when entering the menu or switching styles.

The shipped checks exercised 75 menu states across all three styles, including
both directions, scrolling, wrapping, marker colours and fixed surrounding
rows. Separate VICE checks cover all twelve loader checksums, F1 style reloads,
return from a streamed demo, SPACE next and last-to-first wrapping. Those control
checks enter the real handler paths from the monitor; keyboard scanning itself
is unchanged.

## Reproducing checks

Build the matching cart first so its labels and oracle files exist under
`build/`. Supply explicit tool paths if they are not on PATH. Menu screenshots
require Pillow and `--vice-data` pointing to the VICE ROM directory.

```bash
python -m unittest discover -s tests -v
python tools/verify_uniform_cart.py examples/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v3-all.crt --report build/verify-v3.json
python tools/verify_uniform_cart.py examples/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v4-all.crt --report build/verify-v4.json
python tools/verify_cart_menu.py examples/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v4-all.crt --vice-data /path/to/vice-data
python tools/verify_cart_stream_edges.py --renderer yunroll-cart-v4 --report build/verify-v4-boundaries.json
```

The V4 boundary check covers empty frames; 1, 255, 256, 257 and 512 runs;
255 clear spans; the 1,024-byte metadata boundary; and a 255-frame directory,
with slot reuse and wrapping. Both colour and monochrome paths are checked.

## Updating an existing checkout

The changed-files ZIP contains new/modified files and archived copies. Because
unzip cannot remove obsolete paths, run the cleanup command afterwards:

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
unzip -o ../c64-3d-toolkit-v0.6.4-cart-v4-changed-files.zip
python tools/archive_old_carts.py
```

This archives only the explicit superseded bundled cart names and their reports
under `examples/old/cart_demos/`. It preserves differing local copies using a
content-hash suffix, skips already archived files, and leaves custom filenames
alone. Use `--dry-run` to inspect the moves. Git can recognize the unchanged
archived files as renames. The full-repo ZIP already uses the cleaned layout.
