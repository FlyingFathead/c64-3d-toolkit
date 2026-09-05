# Long Blender scenes on EasyFlash: V4 scene extension

Toolkit v0.6.6 includes **Don't Lose Your Marbles, early beta**, as a standalone
cartridge example. It is silent; music and digi playback are future work.

`yunroll-cart-v4-scene` is an opt-in derivative of V4 for authored Blender
animation. It adds a paged directory, 16-bit sample index, ROML/ROMH packing,
PAL pacing, custom HUD, and optional native intro/finite ending. The original
V4 drawing kernels, builders and twelve-demo menu cartridge are preserved.

## Build the example

The [Blender example](../examples/blender_marbles/README.md) provides a live
rigid-body authoring file, baked file and deterministic generator. Its 40-second
source contains six alternating pours (45 objects), an orbiting camera and a
32-piece tabletop fracture that drifts into a constellation. Queued emitters
have isolated collision collections; releases aim at the tabletop and pile.
The finale is authored after the physical pours, with fixed mesh topology.

```bash
blender --background --python examples/blender_marbles/dont_lose_your_marbles.py
python3 c643d.py cart-stream \
  --renderer yunroll-cart-v4-scene \
  --blend examples/blender_marbles/dont_lose_your_marbles.blend \
  --sample-step 5 --frame-ticks 7 --intro --ending \
  --hud-text "DON'T LOSE YOUR MARBLES" \
  --output dont_lose_your_marbles-yunroll-cart-v4-scene \
  --output-dir examples/cart_marbles
```

Use the usual `--tass`, `--cartconv`, `--blender`, `--vice`, `--run` and overwrite
options or existing toolchain configuration. For a clean presentation, add
`--no-text-overlay` and give the output a `-clean` suffix. This variant retains
the 192-line geometry viewport with a blank bottom row.

`--intro` plays the native bitmap title sequence. `--ending` requires `--intro`
and stops after the last sample has actually been displayed. It runs the
backspacing greetings joke, thank-you credits and staged BASIC/ghost epilogue.
The final cursor blinks without restarting the demo. It is a visual boot-screen
illusion, not interactive BASIC. Without `--ending`, the general scene streamer
still loops; without both flags, it starts immediately. Neutral `.c643dscene`
exports can be compiled with `--scene` instead of `--blend`.

## Measured example and limitations

PAL VICE: 200 exported samples, 405,972 vector bytes, approximately 5.5 scene FPS.
The HUD build takes 36.370 seconds for the vector scene and 58.151 seconds from
reset through the final typed message, including the intro, constellation hold,
greetings and credits. The clean build has almost identical timing; its exact
result is in `examples/cart_marbles/ending-clean-validation.json`.

The 7-raster-tick setting targets 7.14 FPS. Busy collisions and the fracture miss
that deadline, extending playback. There is no runtime sample dropping; changing
sampling and pacing together is how this demo was shortened. The authored
25-FPS Blender timeline is not a promise of C64 playback speed. Physics,
projection and visibility run on the host; the C64 draws every streamed vector.

Both carts pass all 200 frame comparisons in PAL VICE: bitmap pixels, colours,
three buffers and title/blank HUD. The finite ending and typing are separately
verified. The suite passes 105 tests, including 16-bit directory boundaries up
to 2,048 frames and dual-chip packing. The previous long beta exercised two
750-frame loops; the delivered finite demo does not cross frame 255.

A ray-visibility/bitmap audit found no empty regions in 514 unobscured tabletop
marble samples. No released object has a lifetime removal. Ordinary geometry
occlusion and viewport clipping remain intentional. The earlier disappearance
report was not tied to an exact frame and is not claimed as conclusively diagnosed.

Physical EasyFlash and NTSC remain untested. PAL VICE has about 50.125 raster
frames per second, so nominal 50-Hz durations differ slightly. Audio scheduling
and digi feasibility have not been measured; spare ROM alone is not an audio
performance guarantee.

## What changed in the assembly files?

These are separate scene-extension files, first added in the early beta. ZIP
updates replace these files when improving the scene extension. They do not
replace the baseline `yunroll-cart-v4` files.

| Scene file | Purpose |
| --- | --- |
| `c64/renderer-yunroll-cart-v4-scene.asm` | V4 drawing kernels with a 16-bit authored-frame index, directory loading, independent buffer-valid flags and paced presentation. The builder adds the optional final-frame handoff. |
| `c64/cart/easyflash-stream-v4-scene-helper.asm` | Selects ROML or ROMH while copying frame data and loads the seven-array directory page. It supports long scenes; this is not a replacement line-drawing optimisation. |
| `c64/cart/easyflash-stream-v4-scene-boot.asm` | Loads 88 pages into `$0800-$5fff`, plus 26 pages from unused ROMH bank-zero space into `$8000-$99ff` for native titles/credits. |

`tools/c643d/cartintro.py` generates native bitmap/text code and glyph data.
The finite outro code occupies `$5c80-$5f5d`; title/credit data end below `$9a00`.
`tools/c643d/cartscene.py` assembles, checks and packs the result. Ending code is
kept outside metadata caches and vector staging RAM; no line kernels changed.

## Memory and capacity

| Allocation | Address / capacity |
| --- | --- |
| V4 renderer, HUD and LUT | Original addresses below `$2000` |
| V4 copy and colour helpers | `$4000-$43ff` |
| Seven directory arrays | `$4800-$4eff`, fixed 1,792 bytes |
| V4 dispatch low-byte table | `$4f00-$4fff` |
| Three clear/colour metadata caches | `$5000-$5bff`, 3 × 1 KiB |
| Scene directory/index extension | `$5c00-$5c72` |
| Optional finite outro code | `$5c80` to below `$6000` |
| Native intro/credit code and glyph data | `$8000-$99ff`, retained through playback |
| One staged vector frame | `$a000-$bfff`, 8 KiB |
| ROM directory pages | ROMH banks 1/2; up to 2,048 samples |
| Vector data | ROML and ROMH banks 3..63; 999,424 bytes before gaps |

Each complete frame stays inside an 8-KiB ROM bank. Directory pages load at
startup, each 256-sample boundary and loop wrap. ROM copies disable interrupts
for each 256-byte burst and restore RAM/IRQ mapping between bursts. Metadata
validity is independent of the low frame index, so sample 255 cannot be confused
with an uninitialised buffer.

Build limits: 2,048 samples, 8 KiB per frame, 1 KiB metadata per bitmap slot and
255 clear/colour spans per frame. Visible-run counts are 16-bit. Requested
samples are preserved or the build fails. The exporter supports inclusive
`c643d_visible_start`/`c643d_visible_end` object properties for fixed-topology
scheduled appearance; these are used for waiting emitters and the table swap.

## Verification and capture

```bash
python3 -m unittest discover -s tests
python3 tools/verify_cart_stream.py \
  examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene.crt \
  --vice x64sc --report build/marbles-validation.json \
  --capture build/marbles-captures
python3 tools/verify_cart_ending.py \
  examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene.crt \
  --vice x64sc --vice-data /path/to/vice-data --output build/marbles-ending
python3 tools/capture_cart_story.py \
  examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt \
  --vice x64sc --vice-data /path/to/vice-data --output build/marbles-story
```

The matching build oracle is retained under `build/`. The general verifier
checks a finite cart once, or two loops plus wraparound for looping carts.
The ending verifier checks text RAM, text-mode registers, colours, timing and
idle stability. The story capture records native intro/outro raster ticks and
completed scene buffers using the real C64 character ROM; it is not a Blender
render. Use `tools/verify_blender_marbles.py` inside the supplied baked Blender
scene for the additional marble visibility audit.
