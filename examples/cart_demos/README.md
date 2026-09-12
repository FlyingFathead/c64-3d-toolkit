# Cart Demos — hors-render-v2

**Toolkit 0.7.6 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Entries | Colours |
| --- | ---: | --- |
| [c643d-demo-v0.7.7-hors-render-v2-all-ram.crt](c643d-demo-v0.7.7-hors-render-v2-all-ram.crt) | 12 | Per entry |
| [c643d-demo-v0.7.7-hors-render-v2-all.crt](c643d-demo-v0.7.7-hors-render-v2-all.crt) | 12 | Per entry |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos/c643d-demo-v0.7.7-hors-render-v2-all-ram.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

The original twelve-animation menu retains styles, normal PLAY ALL and HiFi mode. FPS/RAM variants use the same source pictures. F5 is exhibition playback; benchmark with normal PLAY ALL only.

During playback: **F3** cycles monochrome foreground, **F4** cycles monochrome
background, **F7** cycles the independent border, and **F8** restores the preset.
Source-coloured entries preserve their palette and support F7/F8 border changes.
Menu F4 remains the HiFi shortcut. See [controls and formats](../../docs/OUTPUT_COLORS.md)
and [0.7.3 regression results](../../docs/COLORS_0.7.3_VALIDATION.md).

```bash
python3 tools/build_hors_v2_examples.py --only cart_demos
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and loading](../../docs/RELEASE_0.7.6.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
