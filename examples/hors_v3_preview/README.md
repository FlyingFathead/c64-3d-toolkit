# HORS-V3 surfaces and textures

Included in v0.7.7, **Pretzel Logic - The Great Texture Update**. The existing directory name is retained for download compatibility. As of v0.7.9, HORS-V3 is the conversion default; the comparison/menu builder retains V2.

## Try the cartridges

Open the `.crt` files in `cartridges/` with VICE or your normal EasyFlash setup. Start with `sande_pretzel-surface-metallic-128-v3.crt`. `previews/` contains actual VICE PNGs and animated GIFs. The test was performed in PAL VICE; real hardware has not been checked in this preview.

| Option | Meaning |
| --- | --- |
| No fill option | Wireframe; existing source-material colour behaviour |
| `--surface-fill material` | Solid faces using nearest-C64 MTL Kd colours |
| `--surface-fill metallic` | Faceted grey/white lighting baked on the host |
| `--surface-fill textured` | OBJ UVs and MTL `map_Kd` diffuse image |
| `--surface-encoding dither` | Black/white ordered-dither version of metallic |
| `--compact-color-dictionary` | Optional packed four-bit colour-pair indices |

`hors-renderer-v3` is the canonical long renderer name; `hors-render-v3` remains an alias for preview commands. `--surface-fills` aliases `--surface-fill`. A bare `--surface-fill` means `material`. `--compact-color-lookup` aliases `--compact-color-dictionary`; `--v3-color-encoding literal|indexed4` is the explicit encoding selector. Direct `literal` colour bytes are the default: compact was smaller but slower on this mesh.

HORS-V3 is the default for object and authored wireframe conversions. Filled
surfaces use the standard 192-line viewport; standalone spin/recede/crawl and
interactive rotation are supported. `--hide-hud` hides the bottom text without
changing this viewport. Filled authored scenes and custom surface intros/endings
are not integrated. [Current SVG and material options](../../docs/HORS_V3_DEFAULTS_CHECKPOINT.md).


## Coloured shading in v0.7.8

HORS-V3 now supports **red, green and blue surface-shading ramps**, alongside the original metallic grey. Use `--surface-fill metallic --surface-palette red`, `green` or `blue`. `--surface-fill grey` (also `gray`) aliases `metallic`; palette names `metallic` and `gray` alias `grey`. The default grey output is preserved. These ramps colour the generated shaded surfaces; imported `map_Kd` textures and plain MTL materials keep their existing colours.

[Stanford Dragon: all six carts, including golden, timed GIFs and performance](../stanford_dragon/README.md).

v0.7.9 adds the remaining C64 hue families and `--surface-ramp` custom stops.
The original four shading ramps remain unchanged.

## Build your own

Run these commands at the repository root. Surface generation requires NumPy and Pillow in addition to the existing toolkit toolchain; 64tass and cartconv assemble the cartridge.

```sh
python c643d.py build --renderer hors-renderer-v3 --obj examples/demos_sande/sande_pretzel.obj --name "SANDE PRETZEL" --obj-up y --spin-axis y --frames 128 --surface-fill metallic
```

For the smaller colour stream, add `--compact-color-dictionary`. On this Pretzel it also allows `--frames 192`, which the direct metallic stream cannot fit. No frame count or geometry is reduced silently. For plain imported surface colours, use `--surface-fill material`. For the lighter metallic appearance, use `--surface-fill metallic --surface-encoding dither`.

```sh
python c643d.py build --renderer hors-renderer-v3 --obj examples/hors_v3_preview/texture-demo/pretzel-test-texture.obj --name "SANDE PRETZEL" --obj-up y --spin-axis y --frames 128 --surface-fill textured
```

The texture example keeps Sande's original vertices and faces but adds generated planar UVs and a new four-grey diagnostic image. Neither the UVs nor this image came from Sande. The original OBJ/MTL under `examples/demos_sande/` is unchanged.

For your own textures provide OBJ `vt` coordinates, face UV indices, `mtllib` and `usemtl`, and an opaque image referenced by `map_Kd`. Paths are relative to the MTL. Kd multiplies the image before mapping to the nearest C64 colours. Two colours per 8×8 hires cell remain the physical limit; complex image patterns are approximated to fit. This preview handles opaque diffuse colour, not transparency, bump/normal maps or modern PBR shading.

## Interactive metallic Pretzel

Open `cartridges/sande_pretzel-surface-metallic-128-v3-interactive.crt` for the faster direct-colour version, or `cartridges/sande_pretzel-surface-metallic-128-v3-indexed4-interactive.crt` for the compact version. Build one by adding `--interactive-cart` to the metallic command above.

| Input | Action |
| --- | --- |
| RUN/STOP (Esc in VICE) / Shift+H | Open/close help; Space also closes |
| `+` / `-` / `0` | Faster, slower, reset angular speed |
| Shift+S | Toggle the included forward starfield (starts off) |
| Shift+I / Shift+F / Shift+U | Toggle name/counts, FPS/speed feedback, or all HUD including INTERACTIVE |
| `1` / `2` / `3` / `4` | Reset / more / fewer stars / switch light and full fields |
| Cursor right | Rotate forward; direction persists after release |
| Shift+Cursor right (left) | Rotate backward; either C64 Shift key works |
| Joystick port 1 or 2, left/right | Select the same backward/forward rotation |
| Opposed joystick directions | Keep the current direction |
| F2 (Shift+F1) | White reset flash, black background, following border, cycling off, default rate |
| F3 | No action; surface shades stay unchanged |
| F4 (Shift+F3) | Cycle the black background pixels through the C64 palette |
| F5 | Start/stop automatic background cycling |
| F6 (Shift+F5) | Decrease cycling speed |
| F7 | Increase cycling speed |
| F8 (Shift+F7) | Toggle persistent black border / following background |
| Ctrl+F7 | Cycle and retain an independent border colour |

Stars start disabled unless `--starfield-default enabled` is selected.
`--starfield-profile light|full` selects the initial and F2-reset profile (full
unless specified); `--no-starfield` removes both fields but retains help/speed.
The original intro waits for SPACE and keeps the Shift+H hint on its own row.

The top-right `INTERACTIVE` label uses the HUD font. Nonblack surface shades remain intact. Colour controls replace original black pixels only, including any black pixels inside an imported texture. The border follows the background by default; black lock and custom border colours persist through background changes until toggled or reset. F5 advances the palette sequentially, with a default interval of 50 PAL ticks (about one second). F6/F7 choose 200, 100, 50, 25, 12, 6, 3 or 1 tick. Events run at most once per produced picture, so the fastest visible rate is limited by rendering speed. Holding a function key produces one action; release it before the next press. V3 still traverses precomputed Y-axis orientations rather than transforming arbitrary camera angles on the C64.

## Rebuild and benchmark

```sh
python tools/run_hors_v3_perfs.py --check
python tools/build_hors_v3_examples.py --tass /path/to/64tass --cartconv /path/to/cartconv
python tools/run_hors_v3_perfs.py --run --vice /path/to/x64sc --vice-data /path/to/vice-data --cartridge-dir build/hors-v3-preview
```

Both tools accept `--variants` followed by IDs from `recipe.json`, for example `metallic compact compact-192`. The build tool writes to `build/hors-v3-preview`; the verifier writes fresh JSON and captures to `build/hors-v3-verification`. The V2 metallic row is a comparison harness which replays the saved host picture oracle through unmodified V2 assembly. It does not enable a V2 surface CLI.

[Full measured results, chart, memory cost and validation scope](../../docs/HORS_RENDER_V3_RESULTS.md).

The release runner rebuilds and verifies these examples before generating the complete performance comparison. Run `python tools/compare_renderers.py --check` and `python tools/run_hors_v3_perfs.py --check` after installation.

## Shared exhibition controls

The two interactive carts use the shared two-page help (left/right while help is open). `5` toggles exhibition, `6` selects ordered/random, and `7`/`8` adjusts the interval. Each Pretzel cart contains one animation, so exhibition keeps playing it with HUD/stars initially off. Stars remain off at normal startup unless explicitly enabled at build time. [Options, controls and compiled-style limits](../../docs/EXHIBITION.md).
