# Cart Demos — hors-render-v2

**Toolkit 0.7.2 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Entries | Colours |
| --- | ---: | --- |
| [c643d-demo-v0.7.2-hors-render-v2-all-ram.crt](c643d-demo-v0.7.2-hors-render-v2-all-ram.crt) | 12 | Per entry |
| [c643d-demo-v0.7.2-hors-render-v2-all.crt](c643d-demo-v0.7.2-hors-render-v2-all.crt) | 12 | Per entry |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos/c643d-demo-v0.7.2-hors-render-v2-all-ram.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

The original twelve-animation menu retains styles, normal PLAY ALL and HiFi mode. FPS/RAM variants use the same source pictures. F5 is exhibition playback; benchmark with normal PLAY ALL only.

```bash
python3 tools/build_hors_v2_examples.py --only cart_demos
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and cleanup](../../docs/RELEASE_0.7.2.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
