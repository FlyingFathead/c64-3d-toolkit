# yunroll-cart-v3: measured vector-rendering improvements

> Historical mixed-method menu carts mentioned below now live in `examples/old/cart_demos/`. For uniform comparisons and scrolling menus, see [the V4 guide](CARTRIDGE_STREAM_V4.md).

V3 is an opt-in derivative of V2, introduced in toolkit 0.6.4; the renderer
suffix identifies the experiment. The current toolkit release is 0.6.5,
with V4 as its default cart renderer. Existing V2 sources, assets, cartridges and
normal PRG renderers are retained. `cart-stream` still defaults to V2.

## Results

Measured in bundled VICE 3.10, PAL, with 64tass 1.59.3120. These are emulated
completed-frame rates, excluding startup, not host rendering or GIF playback.

| Standalone demo, 192 orientations | V2 FPS | V3 FPS | FPS increase |
|---|---:|---:|---:|
| Horse head HiFi | 7.20 | 8.03 | 11.6% |
| Sunflower torus HiFi | 4.91 | 5.55 | 13.0% |

The separate twelve-entry V3 menu cartridge uses 128 orientations per HiFi
entry and measures 8.00 FPS for the horse and 5.52 FPS for the sunflower.
The first ten demos remain their existing PRG payloads, with the normal menu
IRQ shim. They do not receive these V3 rasteriser optimisations.

Each standalone V3 stream passed 387 consecutive exact bitmap/colour checks;
each menu stream passed 259. All three bitmap slots and rotation wraparound
are covered. Both standalone V3 animations have **identical frame blocks,
SHA-256 checksums and frame-bank placement** to their V2 counterparts. The
meshes, camera sampling, colours and hidden-line culling are unchanged.
This is still live C64 vector rasterisation, not bitmap-frame playback.

Detailed reports are in `examples/hifi_showcase/*-v3-validation.json`,
`v3-performance.json` and `examples/old/cart_demos/*v3*validation.json`.
No physical C64 or NTSC timing claim is made.

## Run or build

From the repository root:

```bash
x64sc -cartcrt examples/old/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v3.crt
x64sc -cartcrt examples/hifi_showcase/horse_head_hifi-yunroll-cart-v3.crt
x64sc -cartcrt examples/hifi_showcase/sunflower_torus_hifi-yunroll-cart-v3.crt

python c643d.py cart-stream --renderer yunroll-cart-v3 \
  --object horse_head_hifi --frames 192 --output-dir examples/hifi_showcase
python c643d.py cart-stream --renderer yunroll-cart-v3 \
  --object sunflower_torus_hifi --frames 192 --output-dir examples/hifi_showcase
python c643d.py cart-demos --stream-renderer yunroll-cart-v3
```

The V3 menu command defaults to its own versioned filename; it does not replace
`c643d-demo.crt` or `c643d-demo-v0.6.4.crt`. An explicit `--output` overrides the
name as usual. Standard `--tass`, `--cartconv`, `--vice` and `--run` flags apply.
F1 cycles menu styles; cursors select; RETURN plays; in demos F1/RUNSTOP returns
to the menu and SPACE advances. The existing twelve-entry menu layout is kept.

## Changes

- A 256-entry low/high jump table replaces repeated axis/direction dispatch.
- Line headers read their first step mask in the same pass, advancing the
  stream pointer once instead of twice.
- The 16-bit run count is processed as an initial partial batch followed by
  256-run batches, making the common loop termination check cheaper.
- Vertical scanline phases fall through to the next phase, removing redundant
  jumps between adjacent instructions.
- Frequently used counters and temporaries use 16 additional zero-page bytes.
- ROM-to-RAM and metadata copying use patched absolute-indexed load/store
  operands, with four-byte unrolled full pages and exact partial-page tails.
- Skipping clear-span metadata uses a 16-bit `3*count+1` calculation instead of
  a loop proportional to the number of spans.

The sunflower stage profile fell from about 139,705 to 122,645 cycles in line
drawing, and from 30,522 to 27,137 cycles in cartridge fetching. These are
elapsed emulated cycles including VIC stalls and IRQ work. Drawing remains the
largest cost, so substantial further gains still require work there.

## RAM and compatibility

| V3 addition or allocation | Location / size |
|---|---|
| Extra hot scratch | `$e0-$ef`, 16 bytes; existing pointers remain `$f0-$f7` |
| Dispatch high-byte table | `$4300-$43ff`, 256 bytes |
| Dispatch low-byte table | `$4f00-$4fff`, 256 bytes |
| Frame staging, same as V2 | `$a000-$bfff`, 8 KiB |
| Three metadata caches, same as V2 | `$5000-$5bff`, 3 KiB |
| Directory, same as V2 | `$4800`, 7 bytes per frame, maximum 255 frames |

The lookup tables occupy previously unused gaps. Copy helpers are asserted to
end before `$4300`, and the maximum directory ends before `$4f00`. The renderer
and HUD still must fit below `$1700`. The original bootstrap already copies
through `$4fff`, so standalone frame-ROM capacity stays unchanged. Menu PRG
bootstraps contain additional padding/table bytes, but all twelve entries still
fit the existing 64-bank layout.

Self-modifying routines execute from RAM. Cartridge-copy bursts remain bounded
at 256 bytes; the cart is hidden and `$01=$35` restored before IRQs resume.
The third bitmap under KERNAL therefore remains accessible during drawing.
The menu control handoff uses its existing separate scratch locations.

The frame format is still `c643d-easyflash-stream-v2`; `renderer` in the manifest
identifies V3. Limits remain 1..255 frames, 8 KiB per staged frame, 1 KiB metadata
per slot and 255 clear/colour spans each. Visible-run counts remain 16-bit,
subject to the frame-byte limit. Blender scene streaming and nonstandard HUD
variants retain V2's restrictions.

## Reproduce verification and profiling

Build the matching CRT first; intermediate labels/oracles are required.

```bash
python tools/verify_cart_stream.py \
  examples/hifi_showcase/sunflower_torus_hifi-yunroll-cart-v3.crt
python tools/verify_cart_stream.py \
  examples/old/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v3.crt --menu-entry 11
python tools/profile_cart_stream.py \
  examples/hifi_showcase/sunflower_torus_hifi-yunroll-cart-v3.crt
python tools/verify_cart_stream_edges.py
python -m unittest discover -s tests -v
```

The emulator tools accept `--vice` and `--vice-data`; boundary checks also accept
`--tass` and `--cartconv`. Use your tool package's library search path if its VICE
binary requires one. `--report FILE` writes JSON. Boundary checks include blank
frames, 255/256/257/512 visible runs, 255 clear spans, exact 1,024-byte metadata,
monochrome output, and 255 directory entries. The frame verifier stops before
the publication wait, so very cheap frames cannot trigger duplicate samples.

## Colour shorthand investigation

Current colour spans already contain a numeric colour byte, not a material
name or RGB string. A one-byte repeat marker replacing a one-byte colour alone
would not save space. Grouping spans under a shared colour header could.

For the existing 192-frame data, a format with one group-count byte, two header
bytes per colour group, and three bytes per span would save approximately
6,590 bytes for the horse (2.98% of frame ROM) and 9,091 bytes for the sunflower
(2.45%). This is a storage estimate, not an implemented or benchmarked decoder.
V3 deliberately keeps the existing frame format; a grouped-colour experiment
would need both decoding and per-slot clearing metadata to be measured together.
