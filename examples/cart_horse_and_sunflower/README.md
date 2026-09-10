# Cart Horse And Sunflower — hors-render-v2

**Toolkit 0.7.2 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [horse_and_sunflower-hors-render-v2-scene-ram.crt](horse_and_sunflower-hors-render-v2-scene-ram.crt) | 84 | Yes |
| [horse_and_sunflower-hors-render-v2-scene.crt](horse_and_sunflower-hors-render-v2-scene.crt) | 84 | Yes |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v2-scene-ram.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only cart_horse_and_sunflower
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and cleanup](../../docs/RELEASE_0.7.2.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
