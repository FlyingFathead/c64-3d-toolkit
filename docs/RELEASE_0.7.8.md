# v0.7.8: The Stanford Dragon Has Arrived!

The Stanford Dragon lands on the Commodore 64 in five HORS-V3 demo cartridges: **wireframe, metallic (grey), red, green and blue**. The official Stanford res4 mesh retains all **5,205 vertices, 15,796 edges and 11,102 triangles**, with 128 viewing orientations per cart.

**New in HORS-V3: red, green and blue shading ramps for generated surface textures**, alongside the original metallic (grey). Choose the look from the CLI with `--surface-palette grey|red|green|blue`. `--surface-fill grey` is an alias for `--surface-fill metallic`.

[Watch the showcase GIF](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.8/examples/stanford_dragon/stanford_dragon-showcase.gif): one complete turn each of wireframe, metallic, red, green and blue, in that order. Individual GIFs, prebuilt carts, source geometry, rebuild commands and performance results are in [the Stanford Dragon example](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.8/examples/stanford_dragon/README.md). Playback follows measured PAL VICE display timing.

## CLI

```bash
python c643d.py build --renderer hors-renderer-v3 \
  --obj examples/stanford_dragon/stanford_dragon.obj \
  --name "STANFORD DRAGON" --obj-up y --spin-axis y --frames 128 \
  --surface-fill metallic --surface-palette red
```

Use `green` or `blue` for the other colour ramps. The default is `grey`; `metallic` and `gray` also alias the grey palette. Coloured shading uses native C64 colours and respects the two-colours-per-8×8-cell hires limit. The original black/white dither mode requires the grey palette. Imported image textures and MTL face colours retain their previous behaviour.

HORS-V3 performs projection, visibility and lighting on the host and streams bitmap/colour drawing data to the C64. HORS-V2 remains the toolkit default; older explicit renderers remain available.

## Measured Dragon performance

PAL VICE 3.10, stock C64 timing, 128 orientations per cart. Average FPS counts actual display-buffer flips over 1,504 PAL refreshes after warmup.

| Look | Average displayed FPS | Frame stream | CRT file |
| --- | ---: | ---: | ---: |
| Wireframe | 20.00 | 233,306 bytes | 303,760 bytes |
| Metallic (grey) | 15.13 | 279,935 bytes | 361,216 bytes |
| Red | 15.10 | 277,791 bytes | 353,008 bytes |
| Green | 15.13 | 279,215 bytes | 361,216 bytes |
| Blue | 15.13 | 280,945 bytes | 361,216 bytes |

The combined GIF shows all five complete rotations in **40.34 seconds**. All **1,295 completed-picture checks** passed; every orientation was also verified in the actual display buffers. [Detailed timings, RAM use and evidence](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.8/examples/stanford_dragon/README.md#performance).

The release unit suite passed: **239 tests, 3 skipped**. Existing release validation passed **25 cartridges** and **10,751 picture checks**. The full historical renderer comparison and all **11** existing HORS-V3 workloads were rerun. Existing HORS-V3 cartridge binaries remained byte-for-byte identical to v0.7.7.

## Release integration

- Lead the main README with the Dragon showcase, retain the previous Pretzel release with its metallic GIF, and move older announcements to [release history](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.8/docs/RELEASE_HISTORY.md).
- Integrate all five Dragon builds, independent picture checks, display measurements, GIF captures and a combined showcase into the release workflow.
- Add Dragon performance to the generated main comparison and its source/evidence checks.
- Rebuild current release cartridges and refresh the existing renderer comparison for 0.7.8.
- Give incremental packages a distinct filename, preserving the full ZIP when a baseline is supplied.
- Save required HORS-V3 test transcripts as tracked `.txt` files and derive the evidence path from `VERSION`.
- Add Stanford University Computer Graphics Laboratory and Thomas "skoe" Giesel / EasyFlash / EasyAPI to the main README credits.

Model provenance and Stanford's usage terms are included with the example. PAL VICE validation is recorded in [release evidence](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.8/docs/benchmarks/release-0.7.8/validation.json); physical C64 hardware and NTSC are not measured.

## Install and check

Extract the incremental ZIP from the parent of the existing checkout. It contains a `c64-3d-toolkit/` top-level directory. Then run from the checkout:

```bash
python examples/stanford_dragon/verify.py --check
python tools/run_hors_v3_perfs.py --check
python tools/compare_renderers.py --check
```
