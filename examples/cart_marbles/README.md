# Cart Marbles — hors-render-v2

**Toolkit 0.7.4 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [marbles-hors-render-v2-16fps-force-bytes.crt](marbles-hors-render-v2-16fps-force-bytes.crt) | 640 | Yes |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_marbles/marbles-hors-render-v2-16fps-force-bytes.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only cart_marbles
```

All 640 original samples, the 16 FPS fractional PAL target, no HUD, native intro and complete ending are retained. The migrated v2 scene measured **41.50 seconds** in PAL VICE; 16 FPS is its target, not a promise that every frame meets the deadline. Rebuilds use frozen accepted pictures, not a new Blender physics simulation.

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and loading](../../docs/RELEASE_0.7.4.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
