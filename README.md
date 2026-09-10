<p align="center">
  <img src="assets/c64-3d-toolkit_banner.png" alt="c64-3d-toolkit" width="100%">
</p>

# c64-3d-toolkit

## 👀💦👉 LOOKI LOOKI! `hors-render-v2` just dropped — UP TO 35.5% FASTER!

**Version 0.7.2 makes `hors-render-v2` the default.** New prebuilt cartridges,
measured multi-pass optimization, and a complete release build/check pipeline.

The biggest measured gain is **Ripples Lite: 12.46 → 16.88 display FPS,
+35.48%**, using matching samples in normal PAL VICE PLAY ALL. The new
seven-scene showcase improved by **5.71–35.48%** over hors-render-v1.
The original twelve-animation comparison improved by **2.53–10.00%**.
The independent Linux run reproduced the beta measurements exactly; stable
v2 retains that drawing kernel. See the [complete comparison](docs/PERFORMANCE_COMPARISON.md)
and [showcase results](docs/HORS_RENDER_V2_RESULTS.md) for the actual workloads.
These are emulated C64 timings, not host wall-clock speed or the HUD counter.

**Performance tables:** [Original twelve animations](docs/PERFORMANCE_COMPARISON.md#best-method-for-each-animation) · [Demo Cart 2.0: all seven scenes](docs/PERFORMANCE_COMPARISON.md#demo-cart-20)

### Grab a cartridge and hit SPACE

| Prebuilt | What is inside |
| --- | --- |
| [Twelve-demo cart — FPS](examples/cart_demos/c643d-demo-v0.7.2-hors-render-v2-all.crt) | The original twelve animations, menu styles, PLAY ALL and HiFi mode |
| [Twelve-demo cart — RAM](examples/cart_demos/c643d-demo-v0.7.2-hors-render-v2-all-ram.crt) | Same material, smaller drawing kernels |
| [Demo Cart 2.0](examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt) | Colour cube, colour torus, twist tunnel, ribbon dance, orbital cubes, wave lattice and Ripples Lite |
| [HiFi reel](examples/cart_hifi/c643d-hifi-v0.7.2-hors-render-v2.crt) | Horse & Sunflower followed by two HiFi spinners |
| [Marbles](examples/cart_marbles/marbles-hors-render-v2-16fps-force-bytes.crt) | All 640 authored samples, original 16 FPS target, native intro and ending |
| [Horse & Sunflower](examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v2-scene.crt) | Authored scene, with a separate RAM build in the same folder |

```bash
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos/c643d-demo-v0.7.2-hors-render-v2-all.crt
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt
```

Press **SPACE** on the identification screen. In the menu, use the cursor keys
and RETURN; F1 changes styles or returns from playback. Normal PLAY ALL is the
benchmark path. **F5 is an exhibition mode and must not be used to compare FPS.**

[Browse all current examples](examples/README.md).

## What the toolkit does

A host-assisted 3D compiler and native C64 renderer: import OBJ, SVG or baked
Blender scenes; compute projection and visibility on the host; pack drawing
data into EasyFlash; let the 6510 update VIC-II bitmaps and colours at runtime.
It is not a general live-geometry engine. No cartridge coprocessor is required.

V2 groups literal bitmap spans into bounded cartridge-mapping batches, reducing
repeated mapping setup. Every frame is an independent picture. It reuses the
vector-dispatch page only after requiring all frames to use direct spans.
No extra RAM allocation is introduced by the drawing helper. ROM usage can
grow when a measured gap-bridging choice buys higher display throughput.

The stable host encoder also avoids constructing an unused vector stream just
to obtain metadata. A large intermediate vector representation therefore does
not reject a valid literal picture. Final metadata, frame-bank and cartridge
capacity limits still apply; inputs are never silently simplified to fit.

## Build your own

Python 3, 64tass and VICE/cartconv are required for cartridge builds and tests.
Blender is optional for `.blend` export; shipped example rebuilds use frozen
pictures and do not require Blender or a physics rebake.

```bash
python c643d.py doctor
python c643d.py build --shape cube --frames 192
python c643d.py build --object horse_head
python c643d.py build --scene examples/autotune/colour-cube.c643dscene --frame-ticks 1
python c643d.py cart-demos --prefer fps
python c643d.py cart-demos --prefer ram
```

`build`, `cart-stream` and `cart-demos` default to **hors-render-v2**.
Scene inputs select its scene integration. Explicit `--renderer hors-render-v2-scene`
is also accepted. The command name is **hors-render-v2**, not `hors-renderer-v2`.
Use `--renderer yunroll` explicitly when you want resident PRG output.

- [Configuration](docs/CONFIGURATION.md), [Windows setup](docs/WINDOWS_SETUP.md)
- [OBJ](docs/OBJ_PIPELINE.md), [SVG](docs/SVG_PIPELINE.md), [Blender](docs/BLENDER_PIPELINE.md)
- [Stable v2 details](docs/HORS_RENDER_V2.md), [architecture](docs/ARCHITECTURE.md)

## Measure, choose, measure again

```bash
python tools/autotune_scene.py examples/cart_demos_v2/scenes/ripples_lite.c643dscene \
  --out ../ripples-v2-search --mono --width 320 --jobs 3 \
  --renderers hors-render-v1-scene hors-render-v2 \
  --ticks 1 2 3 4 --plans optimized raw --gaps 3 6 10 --batches 1024 2048 \
  --tass 64tass --cartconv cartconv --vice ./VICE-BATCH.sh \
  --vice-data /usr/local/share/vice
```

Geometry is frozen once. Each candidate is built and checked against the same
pictures, then measured in VICE. CLI, Markdown, JSON and CSV reports retain
wins, losses, failed candidates, display pacing, stage costs and RAM/ROM
allocation components. The search covers its requested candidates; it does not
claim a universal maximum. A pacing change is reported separately from a
renderer throughput improvement.

## Compile and validate an entire release

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
JOBS=3 VICE_DATA=/usr/local/share/vice bash COMPILE-RELEASE.sh \
  --workspace ../c64-072-release-build
```

This makes an isolated source copy, builds every stable example, validates
pictures, endings and menus, runs the original renderer matrix, updates the
chart and produces a complete ZIP. Results and logs stay beside the checkout.
Add `--install` to install only after all checks pass. Add `--baseline-zip PATH`
to also generate a patch ZIP. The pipeline never commits, tags or pushes. Root `VERSION` supplies the build
identity; an alternate-version VICE test guards startup, menu and thanks labels.

To apply a supplied patch and archive superseded previews:

```bash
cd ~/NeuralNetwork
unzip -o c64-3d-toolkit-0.7.2-hors-v2-overlay.zip -d c64-3d-toolkit
cd c64-3d-toolkit
python tools/cleanup_examples.py --apply
```

Old prebuilt CRTs, their companions and resident PRG previews move to
`../c64-3d-toolkit-history/pre-hors-v2/`, outside the checkout. Changed local
copies are preserved in separate hash-named archive paths. All replacement
hashes are checked before cleanup begins. Running cleanup again is harmless.
Runnable legacy previews are available in older release ZIPs; compact frozen
regression inputs remain available for reproducible tests.

## Earlier renderers remain available

| Selection | Preserved implementation |
| --- | --- |
| `step`, `bytechunk`, `yunroll` | Resident PRG renderers |
| `yunroll-cart` | Original resident cartridge scaffold |
| `yunroll-cart-v2` through `yunroll-cart-v9` | Earlier streamed generations |
| `hors-render-v1`, `hors-render-v1-scene` | Original v1 / internal V10 implementations |
| **`hors-render-v2`, `hors-render-v2-scene`** | **Current default, with object, scene and menu integration** |

A new pipeline is added incrementally. Old assembly, encoders and comparisons
stay intact. The resident `yunroll` method still narrowly wins the canonical
CUBE workload; the chart retains that result. See [pipeline versioning](docs/PIPELINE_VERSIONING.md).

[Changelog](CHANGELOG.md) · [Documentation index](docs/README.md)
