# EasyFlash frame streaming: yunroll-cart-v2

> Historical mixed-method menu carts mentioned below now live in `examples/old/cart_demos/`. For uniform comparisons and scrolling menus, see [the V4 guide](CARTRIDGE_STREAM_V4.md).

V2 is an independent experimental renderer and cartridge builder. It stores
vector records in ROM, stages one frame in RAM, and draws the vectors with the
yunroll rasterisation routines. It does not play back bitmap frames. The
original PRG path and `yunroll-cart` scaffold are retained. The menu packer now
includes the two streamed HiFi entries alongside the ten original demos.

## Build and run

```bash
./build.sh cart-stream --object horse_head_hifi --frames 192 --run
./build.sh cart-stream --object sunflower_torus_hifi --frames 192 --run
# Equivalent explicit renderer selection:
./build.sh --object horse_head_hifi --renderer yunroll-cart-v2 --frames 192
```

`--tass`, `--cartconv`, `--vice`, and toolchain config work as before. Outputs are
`.crt`, `.lbl`, and `-manifest.json`. Generated assembly, raw cartridge bytes and
the verification oracle stay under `build/<output>-stream-v2/`.

V2 accepts OBJ, named objects, SVG, procedural geometry, colour, camera, culling,
and generated spin/recede/crawl settings. It explicitly rejects `.blend` and
`.c643dscene`, no-overlay, raster-profiler and non-192-line viewport requests.
The default is 192 frames. V2 never silently reduces the requested frame count.
Each standalone CRT starts one animation directly. `cart-demos` also includes
both HiFi streams at 128 orientations in its twelve-entry menu, with the usual
F1/RUNSTOP return and SPACE-next controls. Menu streams use ROMH banks 2+ in
16K mode, staging from the A000 ROM window into underlying A000 RAM; the
standalone stream builder uses ROML in 8K mode. Both restore RAM before drawing.

## RAM working set

Unlike `cart-demos`, which loads whole PRGs and their complete frame tables,
V2 retains only the current frame and old per-bitmap clearing metadata.

| Data | Address | Allocation |
|---|---|---|
| Renderer and HUD | `$0801` to below `$1700` | Bounded by assembler assertion |
| X-chunk LUT | `$1700-$1fff` | 2,304 bytes |
| Colour/reset/copy helpers | `$4000-$43ff` | Below screen RAM |
| Frame directory | `$4800-$4eff` at maximum | 7 bytes/frame; 1,344 for 192 frames |
| Slot 0 metadata | `$5000-$53ff` | 1 KiB |
| Slot 1 metadata | `$5400-$57ff` | 1 KiB |
| Slot 2 metadata | `$5800-$5bff` | 1 KiB |
| Current complete frame | `$a000-$bfff` | 8 KiB, reused each frame |

The original screens (`$0400`, `$4400`, `$c800`) and bitmaps (`$2000`, `$6000`,
`$e000`) retain the three-buffer producer/consumer design. Metadata follows its
physical bitmap slot, so clearing remains correct while another slot is queued
or displayed. The fixed frame/cache allocation is 11,264 bytes plus directory;
this is **not total program RAM**. Code, LUTs, screens and bitmaps also use RAM.

## ROM format and safe copying

- Bank 0 ROMH: native Ultimax reset code.
- ROML banks 0..2: padded boot-time RAM image, copied to `$0800-$4fff` through
  a trampoline in the always-visible `$df00` EasyFlash RAM.
- ROML banks 3..63: complete frame blocks, each contained within one 8 KiB bank.
- Directory arrays: bank, source address low/high, byte length low/high,
  metadata length low/high.
- Frame block: clear count + three-byte spans; optional colour count +
  four-byte spans; **little-endian 16-bit run count**; existing variable-length
  vector records. Legacy PRG records retain their original one-byte run count.

Each ROM copy burst is at most 256 bytes: disable IRQs, select `$01=$37` and
EasyFlash 8K mode (`$de02=$06`), and write through BASIC ROM into underlying RAM
at `$a000`. Before allowing IRQs, hide the cart (`$de02=$04`) and restore
`$01=$35`, exposing the RAM IRQ vector and third bitmap. Full pages use a
four-byte unrolled copy; the final partial page has an exact byte count.
The IRQ preserves the copy registers and never changes mapping or pointers.
All actual drawing occurs with the cart hidden and RAM under KERNAL visible.

## Current limits

- 1..255 orientations per CRT; actual frame indices 0..254, `$ff` marks an
  uninitialised bitmap slot.
- 8,192 bytes per complete frame; 1,024 metadata bytes per cached slot.
- 255 clear spans and 255 colour spans per frame. Visible runs use a 16-bit
  counter; practical geometry is bounded by the 8 KiB frame block.
- 61 ROML data banks: 499,712 bytes before bank-packing gaps. This limit applies to standalone CRTs. The combined
  menu cartridge additionally uses ROMH for the two HiFi streams.
- Standard 256x192 viewport with HUD. PAL VICE is the measured configuration;
  physical EasyFlash hardware and NTSC are not validated here.

Overflow is rejected. Extra flash capacity does not make complex frames cheap
to rasterise. The host compiler's default 255-run guard stays unchanged for
ordinary PRGs; V2 explicitly opts into the wider counter.

## Verification

Build first, then run:

```bash
python3 tools/verify_cart_stream.py \
  build/horse_head_hifi-yunroll-cart-v2.crt \
  --vice x64sc --report build/horse-validation.json
python3 -m unittest discover -s tests -v
```

For relocated VICE, add `--vice-data /path/to/vice-data`.
`--capture build/captures` creates PNG/GIF framebuffer captures (requires Pillow).
The oracle is generated locally by the build. The verifier checks two full
rotations plus wraparound: all 7,680 bitmap bytes and 960 hires screen bytes per
frame, across all three slots, including blank padding outside the drawing area.
Timing uses emulated CPU cycles, excludes startup, and reports completed render
throughput, not the 50 Hz raster IRQ. GIF timing follows measured cycles rounded
to GIF precision. Captures use toolkit palette RGB values rather than analogue
VIC-II filter output. See the shipped JSON reports for measured builds.

## Next useful improvements

1. Stream the directory or widen indices to exceed 255 frames.
2. Generalise combined ROML/ROMH allocation for arbitrary standalone streams.
3. Add scene-stream support and generalise menu stream selection.
4. Measure merging short collinear runs: fewer records reduce both table bytes
   and per-line setup costs on the 6510.
5. Compare larger segment caching or direct-ROM/hybrid reads with this verified
   baseline. Direct reads must handle CPU mapping and the third bitmap safely.

Compression should earn its place through measurement: saved ROM/transfer work
must outweigh 6510 decompression cost.
