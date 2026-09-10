# Cart Demos V2 — hors-render-v2

**Toolkit 0.7.2 · stable hors-render-v2 prebuilt examples.**

| Cartridge | Samples | Colours |
| --- | ---: | --- |
| [demo-cart-2-preview-hors-v2.crt](demo-cart-2-preview-hors-v2.crt) | 24 / 18 / 48 / 48 / 48 / 48 / 100 | Per entry |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt
```

Press SPACE when an identification screen is shown. Companion labels and manifests identify the exact build.

Seven complete scenes: Colour Cube 24, Colour Torus 18, Twist Tunnel, Ribbon Dance, Orbital Cubes, Wave Lattice and Ripples Lite. These are distinct from the canonical twelve-animation comparison inputs. The measured Ripples Lite gain is 35.48% over v1.

Cross Swell and Liquid Floor are optional source loops under `scenes/`; rebuild with `--water` to select them. Capacity failures never reduce the sample count.

```bash
python3 tools/build_demo_cart_v2.py --renderer hors-render-v2
```

[Full performance comparison](../../docs/PERFORMANCE_COMPARISON.md) · [Release build and cleanup](../../docs/RELEASE_0.7.2.md)

Old preview binaries are in prior release ZIPs or `../c64-3d-toolkit-history/pre-hors-v2/` relative to the repository root.
