# Release history

[Back to the main page](../README.md)

The main page features **v0.7.8: The Stanford Dragon Has Arrived!** and the previous release, **v0.7.7: Pretzel Logic - The Great Texture Update**. Earlier releases and announcements are collected here.

## Release notes

| Version | Release notes and highlights |
| --- | --- |
| [v0.7.8](RELEASE_0.7.8.md) | The Stanford Dragon Has Arrived! Five Dragon carts and red, green and blue surface-shading ramps |
| [v0.7.7](RELEASE_0.7.7.md) | Pretzel Logic - The Great Texture Update: HORS-V3 surfaces, textures and interactive metallic Pretzel |
| [v0.7.6](RELEASE_0.7.6.md) | Sande's Pretzel and TAC-2 model kit, controls and performance comparisons |
| [v0.7.5](RELEASE_0.7.5.md) | Legacy cartridge compatibility and release validation |
| [v0.7.4](RELEASE_0.7.4.md) | EasyFlash / EasyAPI metadata and cartridge loading |
| [v0.7.3](RELEASE_0.7.3.md) | Independent output colours and cartridge colour controls |
| [v0.7.2](RELEASE_0.7.2.md) | HORS-V2 becomes the default, with measured renderer improvements |
| Earlier versions | [Full changelog](../CHANGELOG.md) and [pipeline history](PIPELINE_VERSIONING.md) |

## v0.7.6: Sande's model kit

New models by **Sande**, with reproducible builds, a separate
[Sande performance comparison](PERFORMANCE_COMPARISON.md#sandes-models),
and optional cursor/joystick rotation and F-key palette controls.
See [Sande's demo kit](../examples/demos_sande/README.md).
Defaults are black and white. Separate HORS-V2 `-color` carts use Sande's
original MTL materials: [Pretzel](../examples/demos_sande/sande_pretzel-hors-render-v2-color.crt)
and [TAC-2](../examples/demos_sande/sande_tac2-hors-render-v2-color.crt).

## v0.7.4–v0.7.5: Cartridge loading and compatibility

By default, generated carts include genuine EasyAPI and PETSCII names, checked metadata
placement, and stronger reset initialization. The shared VICE launcher disables
CRT write-back and offers temporary default settings for troubleshooting.
Use `--legacy-cart` to reproduce the discontinued cartridge packing and boot method.
It warns before conversion, omits EAPI/name metadata and keeps the original scene
layout. Standard generation remains the default; generated legacy names end in
`-legacy`. See [legacy compatibility mode](CARTRIDGE_LOADING.md#legacy-compatibility-mode).

## v0.7.3: Colour controls

The independent colours and F3/F4/F7/F8 controls introduced in 0.7.3 remain
available in Demo Cart 1, Demo Cart 2.0 and [COLOR COMBO TEST](../examples/color_combo_test/README.md).
See [output colours](OUTPUT_COLORS.md) for options and inversion examples.

## v0.7.2: HORS-V2 becomes the default

**Since version 0.7.2, `hors-render-v2` is the default.** Prebuilt cartridges,
measured multi-pass optimization, and a complete release build/check pipeline.

The biggest measured gain is **Ripples Lite: 12.46 → 16.88 display FPS,
+35.48%**, using matching samples in normal PAL VICE PLAY ALL. The new
seven-scene showcase improved by **5.71–35.48%** over hors-render-v1.
The original twelve-animation comparison improved by **2.53–10.00%**.
The independent Linux run reproduced the beta measurements exactly; stable
v2 retains that drawing kernel. See the [complete comparison](PERFORMANCE_COMPARISON.md)
and [showcase results](HORS_RENDER_V2_RESULTS.md) for the actual workloads.
These are emulated C64 timings, not host wall-clock speed or the HUD counter.

Historical performance claims describe the workloads and comparison methods recorded for those releases. Use the [current performance comparison](PERFORMANCE_COMPARISON.md) for the latest verified measurements.
