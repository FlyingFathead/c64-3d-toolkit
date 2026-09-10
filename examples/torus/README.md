# Torus — hors-render-v2

**Toolkit 0.7.2 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [torus-hors-render-v2.crt](torus-hors-render-v2.crt) | 192 | Monochrome |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/torus/torus-hors-render-v2.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only torus
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and cleanup](../../docs/RELEASE_0.7.2.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
