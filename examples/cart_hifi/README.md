# Cart Hifi — hors-render-v2

**Toolkit 0.7.6 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [c643d-hifi-v0.7.8-hors-render-v2.crt](c643d-hifi-v0.7.8-hors-render-v2.crt) | 84 / 128 / 128 | Per entry |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_hifi/c643d-hifi-v0.7.8-hors-render-v2.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

```bash
python3 tools/build_hors_v2_examples.py --only cart_hifi
```

The finite Horse & Sunflower scene is followed by two ten-second HiFi spinners and the native thanks/title loop.

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and loading](../../docs/RELEASE_0.7.6.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
