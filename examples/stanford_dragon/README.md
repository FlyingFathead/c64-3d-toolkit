# Stanford Dragon: HORS-V3

Five standalone EasyFlash demos in **v0.7.8: The Stanford Dragon Has Arrived!**: wireframe and the metallic (grey), red, green and blue shaded surfaces. All use Stanford's official res4 mesh: **5,205 vertices, 15,796 edges and 11,102 triangles**, with **128 orientations** and `--prefer fps`.

Model data: **Stanford University Computer Graphics Laboratory**. [Original source, usage terms and conversion provenance](SOURCE.md).

## Five-way showcase

One complete rotation each: **wireframe → metallic (grey) → red → green → blue**, with the measured PAL timing of each cartridge.

![Stanford Dragon: wireframe and four shaded surfaces](stanford_dragon-showcase.gif)

## Wireframe

[Download the wireframe cart](cartridges/stanford_dragon-wireframe-hors-v3.crt)

![Stanford Dragon wireframe running in PAL VICE](previews/stanford_dragon-wireframe-hors-v3.gif)

The complete res4 triangle mesh is retained. Its dense wire pattern is intentional; no edges are removed from the model. The host pipeline hides occluded line portions before encoding the frames.

## Metallic (grey)

[Download the metallic cart](cartridges/stanford_dragon-metallic-hors-v3.crt)

![Stanford Dragon metallic surface running in PAL VICE](previews/stanford_dragon-metallic-hors-v3.gif)

The metallic surface uses HORS-V3's generated grey lighting preset and direct colour bytes. The C64 hires limit of two colours per 8×8 cell produces visible colour blocks at some shade boundaries.

Each 640×400 GIF contains one complete turn captured from actual VICE display buffers. Frame delays follow PAL display holds, with cumulative centisecond rounding. The combined showcase preserves those delays. The longer performance window below includes several turns, so its average need not equal a single captured loop exactly.

## Red shading

[Download the red cart](cartridges/stanford_dragon-red-hors-v3.crt)

![Stanford Dragon with red surface shading](previews/stanford_dragon-red-hors-v3.gif)

## Green shading

[Download the green cart](cartridges/stanford_dragon-green-hors-v3.crt)

![Stanford Dragon with green surface shading](previews/stanford_dragon-green-hors-v3.gif)

## Blue shading

[Download the blue cart](cartridges/stanford_dragon-blue-hors-v3.crt)

![Stanford Dragon with blue surface shading](previews/stanford_dragon-blue-hors-v3.gif)

## Surface palette options

```bash
# Original metallic appearance; grey is an alias for metallic.
python c643d.py build --renderer hors-renderer-v3 \
  --obj examples/stanford_dragon/stanford_dragon.obj --frames 128 \
  --surface-fill grey

# Shaded surface in red; substitute green or blue.
python c643d.py build --renderer hors-renderer-v3 \
  --obj examples/stanford_dragon/stanford_dragon.obj --frames 128 \
  --surface-fill metallic --surface-palette red
```

| Palette | Darkest shade → brightest highlight |
| --- | --- |
| metallic (grey) | dark grey → grey → light grey → white |
| red | brown → red → light red → white |
| green | dark grey → green → light green → white |
| blue | blue → light blue → cyan → white |

All ramps also preserve black silhouette pixels. They colour the generated surface shading; `--surface-fill textured` continues to use the original `map_Kd` image. Coloured ramps require native encoding; black/white dithering remains available with grey. Auto-generated filenames include a non-grey palette suffix, so the different looks have distinct output names.

## Performance

PAL VICE 3.10, stock C64 timing: 985,248 CPU cycles/second and 19,656 cycles/refresh. Measurement follows 134 warmup pictures and observes 1,504 PAL refreshes, approximately 30 seconds. Emulator Warp only accelerates the offline test; the reported FPS and GIF timings use emulated PAL time.

| Measurement | Wireframe | Metallic (grey) | Red | Green | Blue |
| --- | ---: | ---: | ---: | ---: | ---: |
| Average displayed FPS | **20.00** | **15.13** | **15.10** | **15.13** | **15.13** |
| Fastest observed interval, as FPS | 50.12 | 25.06 | 25.06 | 25.06 | 25.06 |
| Slowest observed interval, as FPS | 16.71 | 12.53 | 12.53 | 12.53 | 12.53 |
| Longest picture hold | 59.85 ms | 79.80 ms | 79.80 ms | 79.80 ms | 79.80 ms |
| Observed holds (PAL refreshes) | 1–3 | 2–4 | 2–4 | 2–4 | 2–4 |
| Display-buffer flips in the window | 600 | 454 | 453 | 454 | 454 |
| Single-turn GIF | 6.44 s | 8.48 s | 8.48 s | 8.46 s | 8.48 s |
| CRT file (bytes) | 303,760 | 361,216 | 353,008 | 361,216 | 361,216 |
| Encoded frame data (bytes) | 233,306 | 279,935 | 277,791 | 279,215 | 280,945 |

All five use 128 orientations, a 896-byte frame directory, an 8,192-byte frame staging buffer and a 3,072-byte metadata cache. The combined showcase contains 640 pictures and lasts **40.34 seconds**.

The fastest/slowest values describe individual picture holds, not sustained throughput. They are calculated from PAL refresh counts, avoiding interrupt-entry timing jitter. Listed staging/cache/directory RAM is only part of the runtime footprint; the renderer also uses its three bitmap/screen buffers, code and other state.

HORS-V3 precomputes projection, visibility and metallic lighting on the host. The C64 executes cartridge-streamed bitmap and colour updates. All five demos start automatically and loop; these are the automatic variants without interactive direction controls.

## Validation

- 259 completed pictures checked per cart: two full turns plus three buffer-reuse samples, **1,295 total**.
- Every bitmap and colour byte matched the independent host oracle across all three buffers.
- All 128 orientations also appeared in the actual display-buffer measurements; HUD, VIC bank selection and black border/background passed.
- EasyFlash mapper ID 32, reset vectors, CHIP packets, PETSCII name and the exact bundled EasyAPI payload passed validation.
- Cart SHA-256 values stayed unchanged after VICE runs.
- All individual GIFs and the combined showcase were reopened to verify their frame counts and encoded durations. Surface/texture tests cover the original features, colour ramps and grey/metallic aliases.

[Saved results](evidence/results.json) · [File and source fingerprints](validation.json)

These results cover PAL VICE. Physical C64 hardware and NTSC were not tested. Full release validation also runs the existing renderer matrix and HORS-V3 collection. Required test transcripts use tracked `.txt` files.

## Run

Open any `.crt` in VICE, or use the toolkit launcher from the repository root:

```bash
python c643d.py run-cart examples/stanford_dragon/cartridges/stanford_dragon-wireframe-hors-v3.crt
python c643d.py run-cart examples/stanford_dragon/cartridges/stanford_dragon-metallic-hors-v3.crt
```

The launcher disables CRT write-back and starts PAL/windowed playback at normal emulation speed.

## Rebuild and measure

Run from the repository root. Requires Python, NumPy, Pillow, 64tass and VICE `cartconv`; VICE `x64sc` plus its data files are needed for verification. Blender and network downloads are not required.

```bash
# Verify the included files and recorded evidence, without running VICE.
python examples/stanford_dragon/verify.py --check

# Optional: reproduce the OBJ from the bundled original PLY.
python examples/stanford_dragon/prepare_model.py

# Build fresh carts and compressed host oracles under build/stanford-dragon/.
python examples/stanford_dragon/build.py

# Verify those rebuilds, measure displayed FPS and produce new GIFs.
python examples/stanford_dragon/verify.py --run \
  --cartridge-dir build/stanford-dragon \
  --vice x64sc --vice-data /usr/local/share/vice
```

The build accepts `--tass`, `--cartconv`, `--variants wireframe metallic red green blue` and `--output-dir`. The verifier accepts `--output-dir`; fresh reports and GIFs default to `build/stanford-dragon-verification/`. [recipe.json](recipe.json) contains the exact renderer, camera and encoding arguments. Normal rebuilds leave the shipped examples and evidence in place.
