# Hifi Showcase — hors-render-v2

**Toolkit 0.7.4 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [horse_head_hifi-hors-render-v2.crt](horse_head_hifi-hors-render-v2.crt) | 192 | Yes |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/hifi_showcase/horse_head_hifi-hors-render-v2.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only hifi_showcase
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and loading](../../docs/RELEASE_0.7.4.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
