# v0.7.7 — Pretzel Logic - The Great Texture Update

HORS-V3 adds opt-in solid surfaces, metallic shading and image textures to the toolkit. HORS-V2 wireframe remains the default.

## HORS-V3

The new renderer's short name is **HORS-V3**, with the canonical CLI name **`hors-renderer-v3`**. The preview spelling `hors-render-v3` remains an alias. Existing renderers and released cartridges retain their functionality; the default remains HORS-V2 wireframe.

- Add `--surface-fill` / `--surface-fills` with `material`, `metallic` and `textured` presets. Without a fill option, objects stay wireframe.
- Fill faces with MTL diffuse colours, or generate a faceted metallic appearance with grey and white lighting.
- Support opaque MTL `map_Kd` images with OBJ UV coordinates, perspective-correct host sampling and nearest-C64-colour mapping. The hires two-colours-per-cell limit still applies.
- Share colour addresses across frames, skip redundant old-colour clearing, and omit per-frame colour updates for uniform materials.
- Provide optional `--compact-color-dictionary` encoding. Direct colour bytes stay the speed default; compact trades playback speed for cartridge capacity.
- Include separate interactive metallic cartridges for both direct and compact encoding, with persistent cursor/joystick rotation and the top-right `INTERACTIVE` label. Their per-cell shading is preserved.
- Add background-only controls: F4 manual, F5 automatic, F6/F7 rate, F8 black-border lock, Ctrl+F7 custom border and F2 reset flash. Only original black pixels change; nonblack metallic shades stay intact. The border follows the displayed background by default.
- Add the requested compact metallic Pretzel GIF immediately beneath the version heading in the main README.
- Record performance, storage, image checks and input validation in [the HORS-V3 results](HORS_RENDER_V3_RESULTS.md) and [the performance comparison](PERFORMANCE_COMPARISON.md#hors-v3-surfaces-and-textures).

## Measured performance

Sande's full Pretzel mesh, 128 orientations, PAL VICE 3.10, actual display-buffer flips:

| Variant | Automatic FPS | Interactive FPS |
| --- | ---: | ---: |
| White wireframe | 17.96 | — |
| Plain MTL fill | 18.26 | — |
| Metallic B/W dither | 18.46 | — |
| Metallic direct colours | 14.70 | 14.30 |
| MTL image texture | 14.70 | — |
| Metallic compact dictionary | 12.46 | 12.20 |

Compact reduces the metallic frame stream from 296,092 to 274,460 bytes (7.3%), with a 15.2% reduction in automatic displayed FPS. It also fits 192 metallic orientations where the direct encoding exceeds current packing capacity. Interactive controls idle on black cost about 2.7% in direct mode and 2.1% in compact mode versus automatic rotation.


| Interactive background mode | Direct FPS | Compact FPS |
| --- | ---: | ---: |
| Fixed blue | 13.80 | 12.20 |
| Automatic, default rate | 13.53 | 11.93 |
| Automatic, fastest rate | 12.50 | 11.10 |

The background remap uses 256 additional RAM bytes and leaves frame-stream sizes unchanged. Fast cycling is limited to one change per produced picture. The default rate is about one second per change.

Both interactive variants passed 562 forward/reverse completed-picture checks, 20 direction input checks, 47 background-control input checks, and 272 palette-changing pictures across all three buffers, in addition to their ordinary bitmap, colour and display-FPS verification. Sixteen focused surface/texture tests and four existing compatibility tests passed. Full release validation is recorded in `docs/benchmarks/release-0.7.7/`. Real hardware and NTSC are not measured.

## Try and reproduce

See [the included examples and controls](../examples/hors_v3_preview/README.md). Use `python tools/run_hors_v3_perfs.py --check` to verify that the saved evidence matches the included source and cartridges. Run `python tools/compare_renderers.py --check` to check the complete comparison fingerprint.


## Install

Download `c64-3d-toolkit-v0.7.7.zip` and its SHA256SUMS file into the parent directory of your checkout, then:

```bash
cd /path/to/checkout-parent &&
sha256sum -c c64-3d-toolkit-v0.7.7-SHA256SUMS.txt &&
unzip -o c64-3d-toolkit-v0.7.7.zip &&
cd c64-3d-toolkit &&
python tools/compare_renderers.py --check &&
python tools/run_hors_v3_perfs.py --check
```



## Release validation

- 233 unit tests run, 3 skipped.
- All 26 canonical jobs passed, covering 22,901 completed pictures.
- 25 current HORS-V2 cartridges passed 10,751 completed-picture checks; native endings, menus, HiFi transitions and colour controls also passed.
- All 11 HORS-V3/reference cartridges were rebuilt and measured again; both interactive variants passed direction, background, border, rate and reset-flash checks.
- Original assembly files and historical versioned cartridges remain byte-for-byte unchanged.

Detailed machine-readable evidence: [validation.json](benchmarks/release-0.7.7/validation.json).
