# Blender Falling Cubes — hors-render-v2

**Toolkit 0.7.4 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [falling_cubes_c64-hors-render-v2.crt](falling_cubes_c64-hors-render-v2.crt) | 18 | Monochrome |
| [falling_cubes_c64_color-hors-render-v2.crt](falling_cubes_c64_color-hors-render-v2.crt) | 18 | Yes |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/blender_falling_cubes/falling_cubes_c64-hors-render-v2.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only blender_falling_cubes
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and loading](../../docs/RELEASE_0.7.4.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
