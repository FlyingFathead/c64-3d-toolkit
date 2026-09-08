<p align="center">
  <img src="assets/c64-3d-toolkit_banner.png"
       alt="c64-3d-toolkit — Build modern 3D. Fit it in 64K."
       width="100%">
</p>

# c64-3d-toolkit

Host-assisted low-poly wireframe 3D compiler/runtime for a **stock Commodore 64**, with first-class support for animated **Blender `.blend` scenes**, **Wavefront OBJ + MTL**, **SVG artwork**, built-in procedural geometry, and **EasyFlash `.crt` cartridge output**.

**0.6.9: V9 direct cartridge rendering, now the default.** In the shared-controller comparison suite
(three normal PLAY ALL loops), V9 displays **5,271 frames versus V8's 5,181
(+1.7% overall)** with FPS preference. HiFi sunflower gains **16.1%**, Space Horse Crawl **2.6%**; several
other demos gain a little and six have unchanged frame counts. V9 removes an
intermediate ROM-to-RAM copy for byte pictures and tightens the page-copy loop.
All pictures, colours, samples and older renderer implementations are preserved.
V9 is now the default build and cartridge-menu renderer; select older methods explicitly.
The comparison also identifies five demos where resident `yunroll` beats V9 streaming.
Use the per-animation chart when choosing a method; newest does not mean fastest on every input.

[Try V9 FPS](examples/cart_demos/c643d-demo-v0.6.9-yunroll-cart-v9-all.crt)
• [V9 RAM](examples/cart_demos/c643d-demo-v0.6.9-yunroll-cart-v9-all-ram.crt)
• [Compare every method per animation](docs/PERFORMANCE_COMPARISON.md)
• [V9 measurements and limits](docs/CARTRIDGE_STREAM_V9.md)
• [Apply the 0.6.9 overlay](docs/UPGRADING_0.6.9.md)

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.** Normal PLAY ALL keeps 10 seconds per demo; F5 retains the two
15-second HiFi holds. Compare matching FPS/RAM preferences and PAL settings.

The [V8 cartridge](examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt)
and [V8 implementation/results](docs/CARTRIDGE_STREAM_V8.md) remain available,
along with every older rendering method. V9 is an additional choice.

Animate objects, cameras, modifiers, armatures, or rigid-body scenes in Blender; import coloured OBJ/MTL meshes or SVG paths; or use the classic procedural meshes and animation transforms. The toolkit preprocesses the result on the host, performs projection and hidden-line visibility, then generates 6510/6502 assembly data and runnable C64 demos. The original renderers draw vectors live on the C64; V8 optionally copies precomputed bitmap-byte spans for qualifying pictures.

**More animation than one RAM load can hold.** Build standalone `.prg` demos,
menu-driven `.crt` cartridges, or standalone EasyFlash vector streams. The
`yunroll-cart-v9` menu uses a fixed RAM working set for all twelve demos. Its
`yunroll-cart-v9-scene` counterpart supports authored Blender scenes, including
[Don't Lose Your Marbles](examples/cart_marbles/README.md) and the new
[horse-and-sunflower close-up](examples/blender_horse_and_sunflower/README.md).
The [HiFi showcase](examples/hifi_showcase/README.md) retains the standalone
192-orientation horse and sunflower V2 examples for comparison.

**One renderer per comparison cart.** The V9 menu uses V9 for **all twelve demos**,
including the original Blender and SVG examples. The plain `cart-demos` command
now defaults to V9; select older methods with `--stream-renderer`.
The menu scrolls ten entries between fixed borders in all three styles, with
PLAY ALL above the list. A `+` on a border indicates more entries in that direction.
Historical files from `examples/old/` are supplied in a separate legacy archive.
The editable Horse and Sunflower scene stays separate from the twelve-demo menu.

V4 is a small further improvement over V3: the matched menu carts reach about
**8.08 vs 8.00 FPS** for the HiFi horse and **5.60 vs 5.53 FPS** for the sunflower
in PAL VICE. Both use 128 HiFi orientations; standalone HiFi carts retain 192.
See [the uniform cart and V4 guide](docs/CARTRIDGE_STREAM_V4.md) for all twelve
measurements, memory layout, rebuilding and verification.
The [renderer comparison table](#renderers) covers every variant, including
V5's lossless stream reduction, V6 runtime changes, V7 run joining/RAM preference
V8 adaptive vector/byte-span selection, and V9 direct ROM byte drawing.

**v0.6.5 fixes launching from the animated-colour menu**, including the reported
`JAM at $0008`. See [upgrading to 0.6.5](docs/UPGRADING_0.6.5.md) for the update
and archive command.

**v0.6.6 adds [Don't Lose Your Marbles](examples/cart_marbles/README.md), an early-beta standalone cartridge demo:** coloured cubes and marbles hit a table during an orbiting shot, the tabletop fractures into a star field, and a native intro/credits/BASIC epilogue frames the scene. HUD and clean builds are included. The existing twelve-demo V4 cart is preserved. Audio remains future work.

## Try it first

**V8 playback:** normal PLAY ALL keeps 10 seconds per demo, matching earlier releases.
Press **F5 in the menu** for the exhibition loop: HiFi horse and HiFi sunflower
get 15 seconds each; the other entries stay at 10. Use normal PLAY ALL for
matched timing comparisons. Existing isolated FPS profiles are labelled separately.

**0.6.8 / V8:** [FPS menu](examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt),
[RAM menu](examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all-ram.crt),
Marbles [clean](examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v8-scene-clean.crt)
and [HUD](examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v8-scene.crt).
Clean Marbles' average render cost falls **33.4%**, with samples above budget
falling from **47 to 8 of 200**. Its unchanged sample cadence limits the
throughput gain to **5.1%**. Horse & Sunflower remains about **4.28 samples/s**;
V8 does not improve every scene. See the [full V8 comparison](docs/CARTRIDGE_STREAM_V8.md).

```bash
x64sc -pal +easyflashcrtwrite -cartcrt examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt
python tools/build_v8_examples.py
```

The earlier V7 release is retained below for direct comparison.

**v0.6.7 / yunroll-v7, FPS preferred by default:** try the
[twelve-demo V7 cart](examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt)
or Marbles [clean](examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v7-scene-clean.crt)
and [HUD](examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v7-scene.crt).
V7 joins compatible drawing runs and clears fewer bitmap bytes. Matched PAL
VICE throughput improves **0.2–14.6% over V6**, preserving every original pixel,
colour and sample. The menu CRT shrinks from **927,568 to 804,448 bytes**.

**PLAY ALL** sits above the scrolling demo list: RETURN starts an endless cycle,
10 seconds per animation by default; SPACE skips, RUN/STOP or F1 returns to the
menu. F1 in the menu still cycles default/decorative/flashing demoscene styles.
After the last demo, a white-on-black **THANK YOU FOR WATCHING** screen displays
the toolkit version and project URL for ten seconds, then the cycle restarts.
F1 on that screen returns to the same menu style.
Use `--play-all-seconds N` to change the duration at build time. Optional
`--prefer ram` builds smaller Y kernels; supplied comparison carts end in `-ram`.
See [V7 measurements, memory tradeoffs and rebuilding](docs/CARTRIDGE_STREAM_V7.md).
The older V4/V5/V6 menu cartridges are in the separate oldies ZIP; their
[benchmark evidence](docs/benchmarks/cart_demos/) remains in the source tree.
The V4 reference vectors are now a 399,186-byte compressed host asset, so
`tools/build_v5_examples.py`, `tools/build_v6_examples.py` and
`tools/build_v7_examples.py` rebuild without restoring an old menu cartridge.
The general `cart-demos` command now defaults to V9; select V7 explicitly for historical comparisons.

Playback note: V5 twitching was reported with NVIDIA on Linux/Wayland; the same
cartridges played smoothly on the user's Windows 11 machine. Host presentation
is suspected; this is not a confirmed renderer or driver defect.

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
# Rebuild all three FPS carts from the shipped vector samples:
python tools/build_v7_examples.py
```

You do not need to author a scene or rebuild the toolkit just to see what it does.
The repository ships **ready-to-run C64 examples**, including ordinary `.prg`
demos and a bundled **EasyFlash demo cartridge** containing twelve animations.

Try the new streamed HiFi cartridges directly in VICE:

```bash
x64sc -cartcrt examples/hifi_showcase/horse_head_hifi-yunroll-cart-v2.crt
x64sc -cartcrt examples/hifi_showcase/sunflower_torus_hifi-yunroll-cart-v2.crt
```

For the twelve-animation menu, launch the shipped demo cartridge:

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
```

That boots the **c64-3d-toolkit v0.6.7 V7 demo cart** directly. Use the cursor keys
to choose an animation and RETURN to launch it. In the menu, F1 cycles the live
presentation through `default`, `decorative`, and `demoscene`. While a demo is
running, F1 or RUN/STOP returns to the menu and SPACE launches the next demo.

The repository also includes standalone PRG examples under [`examples/`](examples/),
covering procedural geometry, OBJ/MTL models, SVG artwork, and the Blender
falling-cubes scene. For example, with VICE:

```bash
x64sc -autostart examples/torus/torus.prg
x64sc -autostart examples/horse_head/horse_head.prg
x64sc -autostart examples/blender_falling_cubes/falling_cubes_c64_color-yunroll.prg
```

So there are two easy ways in:

1. **Just run the included demos** in VICE and see the C64 output immediately.
2. **Build your own** procedural, OBJ/MTL, SVG, or Blender-authored scene with the toolkit.

### Cartridge output in v0.6.7

c64-3d-toolkit can build bank-switched C64 cartridge images in **`.crt` format**
in addition to traditional `.prg` files. The repository includes the ready-made
[the final V7 menu cartridge](examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt), plus
its bank map and manifest under `examples/cart_demos/metadata/`, so it can be tried without rebuilding
it first.

To rebuild and immediately run the demo cartridge yourself:

```bash
./build.sh cart-demos --run
# or build the shipped cartridge examples without running them:
./build.sh --generate-cart-demos
```

The generated EasyFlash CRT contains twelve bundled animations and all three menu
presentations. `--menu-style default|decorative|demoscene` selects only the
startup style; F1 can switch styles live afterwards. For example:

```bash
./build.sh cart-demos --menu-style decorative --output c643d-demo-decorative
./build.sh cart-demos --menu-style demoscene --output c643d-demo-demoscene --run
```

Every entry uses the selected renderer. Original PRG vector tables are read
without changing the source PRGs, preserving their camera, culling, colours and
sample counts. Both HiFi models use 128 orientations. Frame data occupies
580,017 bytes spread across available ROMH and ROML chips in one 1 MiB EasyFlash.

```bash
./build.sh cart-demos --stream-renderer yunroll-cart-v4
# Optional historical renderer build, output goes to examples/old/cart_demos/:
./build.sh cart-demos --stream-renderer yunroll-cart-v3
# After overlaying the v0.6.7 update, archive obsolete files outside the project:
python tools/clean_release.py
```

The cleanup command verifies a backup ZIP outside the project before removing
`examples/old/`, older menu carts, generated videos and Blender backup files.
Local edits are preserved in that ZIP. The active menu folder contains the
final FPS/RAM carts, with supporting files in `metadata/` and `reports/`.
Editable `.blend` scenes and current runnable examples stay in the project.
See [upgrading and repository cleanup](docs/UPGRADING_0.6.7.md).

## Requirements

Required:

* [VICE](https://vice-emu.sourceforge.io/) — Commodore 64 emulator; the toolkit uses `x64sc` by default.
* [64tass](https://tass64.sourceforge.net/) — 6502/6510 cross-assembler.
* Python 3.

Required only for cartridge / `.crt` output:

* `cartconv` from [VICE](https://vice-emu.sourceforge.io/) — converts packed cartridge ROM data to the EasyFlash `.crt` container. Normal `.prg` builds do **not** require `cartconv`.

Recommended for the authored `.blend` scene path:

* [Blender](https://www.blender.org/) — use the current Blender LTS for newly authored scenes. Blender 4.0.2 remains a supported older fallback on Ubuntu 24.04. Animate geometry, physics, modifiers, armatures, materials, and a virtual camera in Blender, then compile sampled scene frames into vectors drawn live on the C64. Blender supplies its own `bpy` Python environment; do **not** add `bpy` to `requirements.txt` or install it with `pip`.

Blender is required for `.blend` scene builds. Classic procedural, OBJ/MTL,
and SVG builds remain fully usable without it.

### 🐧 Linux setup

On Debian/Ubuntu and derivatives, VICE and 64tass can normally be installed with:

```bash
sudo apt install vice 64tass
```

Blender is recommended. Ubuntu 24.04 LTS (`noble`) provides Blender 4.0.2 with
a working bundled `bpy`; install it to use the animated `.blend` scene pipeline:

```bash
sudo apt install blender
```

The same distribution-package route is appropriate on later Ubuntu/Debian
releases when `apt show blender` reports an available package. Verify the
headless Python integration with:

```bash
blender --background --disable-autoexec --python-expr 'import bpy; print("BLENDER:", bpy.app.version_string); print("BPY OK")'
```

Verify that the required tools are available with:

```bash
./build.sh doctor
```

Preflight reports resolved executable paths and versions for 64tass and VICE.
`doctor` also reports optional `cartconv` availability (required only for
cartridge/`.crt` output) and launches optional Blender headlessly to report both
its version and whether `bpy` imports successfully. Every `--blend` build repeats
that Blender/`bpy` check before reading the scene.

### 🪟 Windows setup

If Git is not already installed, install Git for Windows first through WinGet:

```powershell
winget install --id Git.Git -e --source winget
```

Then clone the toolkit and run the Windows setup helper:

```powershell
git clone https://github.com/FlyingFathead/c64-3d-toolkit.git
cd c64-3d-toolkit
.\setup-windows.cmd
```

For the optional Blender scene pipeline, install the official Blender package
through WinGet:

```powershell
winget install -e --id BlenderFoundation.Blender
```

Open a new PowerShell window after installation and verify Blender's bundled
Python environment:

```powershell
blender --background --disable-autoexec --python-expr 'import bpy; print("BLENDER:", bpy.app.version_string); print("BPY OK")'
```

If `blender` is not added to `PATH`, the toolkit also searches normal Blender
Foundation installation directories under Program Files. An exact executable
can be selected with `--blender` or `config/c643d.ini`.

For installer and recovery help:

```powershell
.\setup-windows.cmd -Help
```

If the toolkit came from a release ZIP or was copied from another machine, run `setup-windows.cmd` directly from the toolkit directory. The helper detects existing tools and can install missing Python, Git, and VICE through Microsoft's WinGet `winget` source. Existing WinGet packages are kept by default, with explicit upgrade and same-version reinstall choices.

64tass remains a deliberate manual trust decision on Windows: setup does not automatically download or execute it. You can provide an existing `64tass.exe`, search common locations, or optionally scan a selected drive. Manual candidates are validated without execution and SHA-256 is shown before confirmation. Existing `[windows]` paths in `config/c643d.ini` are preserved unless you explicitly change them.

See [`docs/WINDOWS_SETUP.md`](docs/WINDOWS_SETUP.md) for the complete Windows bootstrap, recovery, path-search, and trust/provenance notes.

### Toolchain configuration and macOS/Windows paths

The toolkit now has an optional local configuration file for tool paths and default arguments. Copy the example if `64tass` or `x64sc` are not directly in `PATH`, or if your installation needs custom command-line arguments:

```bash
cp config/c643d.ini.example config/c643d.ini
```

`config/c643d.ini` is gitignored. If it is absent, built-in defaults are used. Command-line options override the config. The default VICE arguments include `+VICIIfull`, so `--run` opens VICE windowed rather than inheriting a saved fullscreen setting.

```ini
[toolchain]
tass = 64tass
vice = x64sc
cartconv = cartconv
tass_args =
vice_args = +VICIIfull

[macos]
# tass = /opt/homebrew/bin/64tass
# vice = /Applications/vice-arm64-gtk3-3.8/bin/x64sc
# cartconv = /Applications/vice-arm64-gtk3-3.8/bin/cartconv

[windows]
# tass = C:\Tools\64tass\64tass.exe
# vice = C:\Tools\VICE\bin\x64sc.exe
# cartconv = C:\Tools\VICE\bin\cartconv.exe
```

On macOS, the easiest command-line installation is typically:

```bash
brew install tass64 vice
```

For a VICE package downloaded from the VICE site and moved into `/Applications`, prefer the package's real command-line binary directly, for example `vice = /Applications/vice-arm64-gtk3-3.8/bin/x64sc`. The architecture/frontend/version part of the directory name varies by download (for example ARM64 vs. Intel and GTK3 vs. SDL2). The toolkit also probes common package layouts and accepts a VICE distribution directory or `.app` path, but pointing straight at `bin/x64sc` is the least ambiguous option.

Existing direct overrides still work:

```bash
./build.sh --shape torus --tass /path/to/64tass --vice /path/to/x64sc --run
./build.sh --shape torus --vice-arg=+VICIIfull --run
./build.sh --shape torus --no-vice-default-args --run
```

See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for precedence, per-platform sections, `C643D_CONFIG`, `--config`/`--no-config`, and macOS package details.

## Build your own

Once the toolchain is installed, the smallest build/run path is one of the
included procedural objects:

```bash
./build.sh --shape torus --run
```

Build and run an imported OBJ preset:

```bash
./build.sh --object horse_head --run
```

Rebuild the complete twelve-animation EasyFlash demo cartridge:

```bash
./build.sh cart-demos --run
```

For low-level cartridge-backend development, the smaller bank-switch diagnostic
is still available as `./build.sh cartridge-smoke --run`.

Compile the included authored Blender rigid-body scene:

```bash
./build.sh --blend examples/blender_falling_cubes/falling_cubes_c64.blend \
    --frame-start 1 --frame-end 72 --sample-step 4 --run
```

The toolkit checks that Blender can run headlessly and import its bundled
`bpy` module before processing a `.blend` file. Blender is invoked with
`--disable-autoexec` before the scene is opened, so embedded scripts in a
`.blend` file are not auto-executed by the toolkit. See
[`docs/BLENDER_PIPELINE.md`](docs/BLENDER_PIPELINE.md) for installation,
stable-topology constraints, material colours, and the generated falling-cubes
rigid-body example.

The Blender examples live under `examples/blender_falling_cubes/`, not in the project root:

```bash
# Generate the C64-budget-oriented six-cube scene beside its script.
blender --background --python examples/blender_falling_cubes/falling_cubes_c64.py

# Compile 18 samples from that generated scene.
./build.sh --blend examples/blender_falling_cubes/falling_cubes_c64.blend \
    --frame-start 1 --frame-end 72 --sample-step 4 --run
```

For stateful simulations such as rigid bodies, the exporter evaluates every
intervening Blender frame sequentially and stores only the requested samples.
Thus `--sample-step 4` keeps the 72-frame motion span while reducing the stored C64 table frames enough for the expanded 192-line default viewport, without skipping physics evaluation between samples.
The exporter warns explicitly if every sampled frame is geometrically identical.

`falling_cubes_full.py` and the included Blender-4.00
`falling_cubes_full.blend` contain Harry's deterministic 40-cube authoring
scene. They are useful as a Blender/rigid-body stress example; the smaller
variant exists because the full scene can exceed the C64 renderer's per-frame
vector and table-RAM budgets.

or:

```bash
./build.sh --object sunflower_torus --run
```

The sunflower reads `usemtl`/`Kd` data from `sunflower_torus.mtl` and maps it to
C64 brown, yellow, and green. To deliberately keep the historical white-on-black
wireframe path:

```bash
./build.sh --object sunflower_torus --no-colors --run
```

The bundled SVG logo can be spun as a 3-D plane or sent away on a tilted crawl plane:

```bash
./build.sh --object space_horse --run
./build.sh --object space_horse_crawl --run
```

Build the manifest-driven procedural/OBJ/SVG reference `.prg` files and all release regression variants:

```bash
./build.sh --generate-examples
```

Reference PRGs are grouped into per-example directories under `examples/`. The unsuffixed overlay build uses the current 256x192 viewport; `_legacy144.prg` keeps the older 256x144 performance/reference framing; `_no_overlay.prg` uses the full 256x200 bitmap height; `_rastertime_profiler.prg` is the separate debug renderer. This makes viewport/FPS comparisons explicit instead of silently replacing the old 144-line behavior.

When upgrading an existing pre-0.6.2 checkout by overlay ZIP, preview and then apply the one-time layout migration so old flat PRGs / `examples/blender/` copies do not remain behind:

```bash
python tools/migrate_examples_layout.py
python tools/migrate_examples_layout.py --apply
```

The migration never overwrites a differing destination file; identical duplicates are removed and conflicts are left untouched with a warning.

The Blender regression set is kept separate because Blender is optional. The historical colour `falling_cubes_c64_color-yunroll_legacy144.prg` is retained in `examples/blender_falling_cubes/`; current 192/200/debug PRGs are generated and checksum-verified with `test-examples --blender-only` / `generate-examples --blender-only`.

Build + run the reference torus with the current fastest renderer:

```bash
./build.sh --shape torus --run
```

Make the torus denser:

```bash
# 72 vertices / 72 quad faces = 12 x 6 torus
./build.sh --shape torus --vertices 72 --run

# same topology, explicitly
./build.sh --shape torus --major-segments 12 --minor-segments 6 --run

# target approximate face/poly count
./build.sh --shape torus --polycount 100 --run
```

Run the included low-poly horse head or sunflower:

```bash
./build.sh --object horse_head --run
./build.sh --object sunflower_torus --run
```

The horse OBJ is open/non-manifold in a few places, so its preset uses full `surface` Z-buffer visibility. This intentionally avoids face-normal pre-culling on unreliable topology; the Z-buffer also tracks face ownership so muzzle edges cannot self-occlude against their own adjacent faces. You can compare the lighter modes or the older front-face-only method with:

```bash
./build.sh --object horse_head --visibility surface_features --run
./build.sh --object horse_head --visibility surface_creases --feature-angle 40 --run
./build.sh --object horse_head --visibility frontface --run
```

Import your own OBJ into the project, then build it:

```bash
./build.sh import-obj ~/models/my_ship.obj --as my_ship --up z
./build.sh --object my_ship --run
```

Or compile a one-off OBJ without importing it:

```bash
./build.sh --obj ~/models/my_ship.obj --obj-up z --name MY_SHIP --run
```

SVG artwork can be imported as wire geometry too. Curves are flattened and simplified on the host; `--svg-depth` optionally gives the contours a shallow Z extrusion:

```bash
./build.sh import-svg ~/art/logo.svg --as logo --animation spin
./build.sh --object logo --run

# one-off, shallow 3-D extrusion
./build.sh --svg ~/art/logo.svg --svg-depth 4 --color yellow --run
```

Animation modes are `spin`, `recede`, and `crawl`. `recede` keeps the artwork front-facing while moving it away from the camera; `crawl` tilts it onto a virtual plane and moves it upward/away toward a horizon:

```bash
./build.sh --object space_horse --animation recede --run
./build.sh --object space_horse --animation crawl --animation-tilt 62 --run
```

Renderer comparison:

```bash
./build.sh --shape torus --renderer step --run       # v0.7-style reference
./build.sh --shape torus --renderer bytechunk --run  # v0.8 stable path
./build.sh --shape torus --renderer yunroll --run    # current fastest path
```

Useful inspection commands:

```bash
./build.sh inspect --shape torus --vertices 72
./build.sh inspect --object horse_head
./build.sh list-shapes
./build.sh list-objects
```

## Horse-head visibility note

The bundled horse is deliberately compiled with `--visibility surface`. Its OBJ contains boundary and non-manifold topology, so using adjacent face normals as a pre-cull can make legitimate muzzle/snout edges disappear at some rotations. Full surface mode lets the host-side Z-buffer decide visibility instead.

`surface_features` retains the cheaper v0.3.1 behavior: ordinary two-face manifold edges are pre-culled when both adjacent faces are back-facing, while boundary/non-manifold edges survive to the surface depth test. `surface_creases` is the crease-aware variant and preserves sharp manifold edges according to `--feature-angle`.

```bash
./build.sh --object horse_head --visibility surface_features --run
./build.sh --object horse_head --visibility surface_creases --feature-angle 40 --run
```

The emitter can spill whole per-orientation line blocks into otherwise-unused RAM below bitmap #2, so the full horse surface mode still fits 36 sampled orientations without reducing the mesh.


## Current render/build controls (v0.6.6)

These controls were introduced in v0.6.2 and remain the current v0.6.6 PRG behaviour. They expand the default drawable area while keeping alternate/debug paths out of the production renderer:

```bash
# production HUD/FPS path: automatic 256x192 drawable viewport
./build.sh --shape torus --run

# legacy/performance framing: same production renderer, 256x144 drawable viewport
./build.sh --shape torus --viewport-height 144 --run

# separate no-overlay ASM: no HUD/FPS/text, automatic full 256x200 viewport
./build.sh --shape torus --no-text-overlay --run

# derivative yunroll debug ASM: border marks actual main-loop render CPU time
./build.sh --shape torus --rastertime-profiler --run
```

`--viewport-height LINES` may override the automatic height (8..200, multiple of 8). `--overwrite-policy allow|warn|error` controls existing PRG/LBL/LST outputs; the built-in default is `warn`. These defaults may also be stored in `[render_defaults]` in `config/c643d.ini`; command-line options take precedence.

The no-overlay and raster-profiler implementations are separate ASM derivatives. Normal `step`, `bytechunk`, and `yunroll` production sources contain no conditional profiler/overlay-removal instrumentation and pay no extra byte or cycle cost for these modes.

### PRG checksum regression tests

```bash
# test every manifest example in 192-line normal, 144-line legacy, 200-line no-overlay and profiler variants
./build.sh test-examples

# one example only
./build.sh test-examples --only cube

# compare against a named historical/current checksum set
./build.sh test-examples --reference-set legacy-v0.6.0-v0.6.1

# actually reproduce that reference set's recorded historical build settings
./build.sh test-examples --variants normal --reference-set legacy-v0.6.0-v0.6.1 --reproduce-reference
```

Each generated PRG is reported as `MATCHING`, `CHANGED`, or `ABSENT`, followed by totals. Reference SHA-256 values and byte sizes live in `tests/data/golden_prg_checksums.json`. The historical v0.6.0/v0.6.1 set is retained alongside the preserved v0.6.2 PRG compatibility baseline instead of being overwritten. Cartridge work does not replace that golden PRG set.

To install all deterministic reference PRGs into their per-example directories (normal, `_legacy144`, `_no_overlay`, and `_rastertime_profiler`):

```bash
./build.sh --generate-examples
```

## Examples

The repository has an `examples/` manifest for the dependency-free procedural,
OBJ/MTL, and SVG reference builds:

```bash
./build.sh --generate-examples
# equivalent:
./build.sh generate-examples
```

For each manifest entry this produces the current 192-line normal `.prg`, a byte-comparable `_legacy144.prg` performance/reference build, a `_no_overlay.prg` full-height build, and a `_rastertime_profiler.prg` debug build. Auxiliary labels/listings remain transient; runnable reference PRGs are placed in the manifest entry's `examples/<name>/` directory.

Blender-authored examples are intentionally outside `examples.json` because
Blender is optional. `examples/blender_falling_cubes/` contains the six-cube C64 scene, the 40-cube authoring/stress scene, and the byte-exact historical 144-line colour PRG. Current Blender PRGs are regenerated only on Blender-capable hosts and verified against the preserved v0.6.2 PRG checksum baseline.

## Dependency checks

Every build now performs an early preflight. `64tass` is required unless `--no-assemble` is used. VICE is optional for build-only work but required for `--run`. Override executable names/paths with `--tass` and `--vice`.

```bash
./build.sh doctor
```

On Debian/Ubuntu, distro VICE packages can be DFSG-stripped and omit Commodore ROM images. The emulator executable may therefore exist but still fail at machine startup until compatible ROMs are installed/configured. This is separate from the toolkit preflight, which only verifies that the executable is present.

## Current state

The historical 256x144 `yunroll` torus (`torus_legacy144.prg`) measured around
**15-18 FPS** on stock PAL C64 timing in VICE during development. The current
256x192 default and 256x200 no-overlay builds deliberately draw/clear more of
the bitmap and can therefore run slower depending on scene complexity. The original
vector variants remain native hires, hidden-line clipped and triple-buffered,
without pre-rendered bitmap animation frames. V8 retains hires and triple
buffering but adds precomputed sparse bitmap-byte pictures as an explicit
alternative to runtime vector drawing.

As of **v0.6.6**, the toolkit is a reusable multi-source compiler/runtime rather
than only a rotating-mesh benchmark. It accepts procedural geometry, OBJ/MTL,
SVG, versioned `.c643dscene` interchange data, and animated Blender `.blend`
scenes. Blender-authored builds can preserve arbitrary object motion, stable-
topology deformation, rigid-body simulation, materials, and active-camera
animation while the stock C64 still rasterizes the resulting vectors itself.

Version 0.6.4 introduced the independent cartridge streaming variants. Version
0.6.5 fixes the animated-menu loader handoff and keeps one current V4 cart with
all twelve entries streamed using the same renderer. The original `yunroll-cart`
scaffold and earlier renderer variants are retained.

The project grew out of the rotating-torus benchmark, a.k.a. **THE WORLD'S MOST
DANGEROUS ROTATING DONUT**.

The repository includes the actual `objects/horse_head.obj` low-poly model
(64 vertices / 124 edges / 65 faces), `objects/sunflower_torus.obj` + `.mtl`
(76 vertices / 142 edges / 70 faces), the bundled `objects/space_horse.svg`
vector-logo demo, and Blender rigid-body examples under `examples/blender_falling_cubes/`.

## What happens on the host vs. the C64?

The host side performs the expensive/general work that makes sense to precompute
for a ~1 MHz target:

- procedural mesh generation, Wavefront OBJ/MTL parsing, and SVG contour
  flattening/simplification
- optional headless Blender scene evaluation through Blender's bundled `bpy`
- dependency-graph evaluation of object transforms, rigid bodies, modifiers,
  armatures, stable-topology deformation, materials, and the active camera
- versioned `.c643dscene` interchange loading for Blender-neutral scene builds
- normalization, coordinate conversion, and face-winding repair for legacy
  procedural/OBJ/SVG sources
- sampled legacy transforms (`spin`, `recede`, or tilted-plane `crawl`) or
  authored Blender frame selection
- perspective projection and viewport clipping for authored scene sources
- face visibility and host-side Z-buffer hidden-line clipping
- C64-oriented line-step encoding
- dirty-area and hires screen-colour span generation

Blender scenes use strict authored-frame semantics: if the selected samples do
not fit the C64 table budget, the build fails with sampling/range/detail
suggestions rather than silently discarding authored frames.

The C64 still rasterizes the visible wireframe itself into VIC-II hires bitmap
RAM. `step`, `bytechunk`, and `yunroll` are vector/line renderers, not
bitmap-frame players.

## Shapes and topology

Built-ins:

```text
torus
cube
sphere
```

Repository objects:

```text
objects/horse_head.obj
objects/horse_head.json
objects/sunflower_torus.obj
objects/sunflower_torus.mtl
objects/sunflower_torus.json
objects/space_horse.svg
objects/space_horse.json
objects/space_horse_crawl.json
```

For procedural shapes, use either the actual segmentation or an approximate target:

```bash
--major-segments N --minor-segments N    # torus
--lat-segments N --lon-segments N        # sphere
--polycount N                            # approximate face count
--vertices N                             # approximate vertex count
```

For the torus, `major_segments * minor_segments` equals both the vertex count and quad-face count. Example:

```text
10 x 5  ->  50 verts, 100 edges, 50 faces
12 x 6  ->  72 verts, 144 edges, 72 faces
14 x 7  ->  98 verts, 196 edges, 98 faces
```

Higher detail consumes both CPU time and generated table RAM. If a requested mesh no longer fits with 48 orientations, the compiler preserves mesh detail and automatically reduces the orientation-table count unless `--strict-frames` is used.

## OBJ pipeline

### Import a model into `objects/`

```bash
./build.sh import-obj path/to/model.obj --as model_name --up y
```

This creates:

```text
objects/model_name.obj
objects/model_name.json
```

The JSON sidecar stores object-specific metadata such as:

- display name
- source up-axis (`y` or `z`)
- preferred spin axis (`x`, `y`, or `z`)
- initial rotation
- object scale

Then build it with:

```bash
./build.sh --object model_name --run
```

List imported/preset objects:

```bash
./build.sh list-objects
```

Inspect topology before compiling:

```bash
./build.sh inspect --object model_name
```

The inspector reports vertices, edges, faces, n-gon mix, boundary edges, non-manifold edges, and isolated vertices.

### Current OBJ support

The parser supports:

- `v` vertices
- polygonal `f` faces
- positive and negative OBJ indices
- `v/vt`, `v//vn`, and `v/vt/vn` tokens
- triangles, quads, and n-gons

Texture/normal indices are currently ignored. Polygon faces are triangulated internally for visibility/Z-buffer work while polygon boundary edges remain the wireframe edges. Direct `mtllib` references are preserved by `import-obj`; `usemtl` assignments and diffuse `Kd` colours are read and mapped to the nearest C64 palette entries.

OBJ/MTL and SVG source colours are enabled automatically. Disable them with any
of the equivalent flags below; this retains the original monochrome table format
and hot renderer loop:

```bash
./build.sh --object sunflower_torus --no-color --run
./build.sh --object sunflower_torus --no-colors --run
./build.sh --object sunflower_torus --ignore-colors --run
```

If an OBJ has no usable `mtllib`/`usemtl`/`Kd` data, or an SVG has no explicit
usable stroke/fill colour, the compiler simply uses the single-colour path
(white by default). It does not enable the per-cell colour machinery. Before
frame generation, the build prints which of those paths it selected and names
the source file it inspected.

`--color yellow` (or `--color 7`) forces one monochrome foreground colour and
also bypasses per-material/per-contour mapping.

### Current limitation

The toolkit does **not yet contain a general mesh decimator**. Imported meshes should currently already be reasonably low-poly. Automatic simplification to a requested C64 face/edge budget is on the roadmap; it will be implemented as a real topology-aware stage rather than deleting random faces and pretending that is decimation.

## SVG pipeline

SVG artwork is treated as vector contour geometry rather than as a bitmap. The importer understands common SVG path commands and basic vector primitives, flattens Bezier/arc curves to line segments, simplifies them for the C64 budget, flips SVG Y-down coordinates into the toolkit's Y-up space, and stores the result as explicit wire edges. This avoids inventing filled triangles through concave glyphs or letter holes.

Import and build:

```bash
./build.sh import-svg path/to/logo.svg --as logo
./build.sh --object logo --run
```

Useful controls:

```text
--svg-tolerance N          contour simplification tolerance in source SVG units
--svg-curve-step N         curve sampling step before simplification
--svg-depth N              shallow wire extrusion depth; 0 keeps a flat plane
--svg-connector-stride N   connect every Nth front/back vertex when extruded
--color NAME|0..15         force one C64 foreground colour
--no-colors                ignore source colours; classic white-on-black
--animation spin|recede|crawl
--animation-tilt DEG       crawl-plane tilt
--animation-travel N       distance travelled away from the camera
--animation-rise N         upward travel for crawl mode
```

`import-svg` inspects each visible contour's stroke/fill colour and maps it to the nearest C64 palette entry. The bundled SPACE HORSE asset uses `#FFE81F`, which maps to C64 yellow. Multi-colour SVGs retain distinct contour colours.

Native hires bitmap mode selects foreground/background per 8x8 character cell,
not per pixel. The host therefore counts the visible coloured line pixels in each
touched cell and assigns the dominant colour when several materials/contours
share that cell. It emits horizontal screen-colour spans containing ready-to-store
VIC-II colour bytes. RGB parsing and nearest-colour searches never run on the C64.
Single-colour sources use the existing global hires foreground byte and therefore
need no colour table or runtime update pass.

The bundled examples are:

```bash
./build.sh --object space_horse --run        # Y-axis spinner
./build.sh --object space_horse_crawl --run  # tilted plane -> horizon
```

`recede` is also available for the front-facing logo-moving-away effect:

```bash
./build.sh --object space_horse --animation recede --run
```

See [`docs/SVG_PIPELINE.md`](docs/SVG_PIPELINE.md) for the current parser/geometry details and limitations.

## Horse head

The canonical included object is:

```text
objects/horse_head.obj
```

Topology:

```text
VERTS: 64
EDGES: 124
FACES: 65
```

Its metadata declares the source as Z-up and the toolkit converts it to internal Y-up coordinates before compiling:

```bash
./build.sh --object horse_head --renderer yunroll --run
```

On the host-side compiler, the full horse currently exceeds the line-table budget at 48 and 40 orientations, so the compiler automatically selects **36 orientations** while preserving all 64 vertices / 65 faces.

Table-RAM messages during auto-fit are informational: the compiler retries with fewer precomputed rotation orientations while keeping the mesh itself intact. It now explicitly prints that vertices/edges/faces are preserved. Use `--strict-frames` if you would rather fail than auto-reduce the orientation count.

## Spin axis and pose

Named objects can define a preferred spin axis in their JSON metadata. Override it from the CLI:

```bash
./build.sh --object horse_head --spin-axis x --run
./build.sh --object horse_head --spin-axis y --run
./build.sh --object horse_head --spin-axis z --run
```

Initial pose can be changed with:

```bash
--rotate-x DEG --rotate-y DEG --rotate-z DEG
```

The historical spinner is now one animation mode. Named presets may select another mode, and the CLI can override it:

```bash
--animation spin
--animation recede
--animation crawl --animation-tilt 62 --animation-travel 105 --animation-rise 42
```

## Renderers

`build`, `cart-stream` and `cart-demos` default to V9. `build --scene` / `--blend`
uses V9-scene; use `--renderer yunroll` explicitly for resident PRG output.

[See comparison chart for details on performance differences](docs/PERFORMANCE_COMPARISON.md).

The chart covers each named demo, ties/best methods, size and fixed RAM allocations.
Reproduce it with `python tools/compare_renderers.py --vice-data /usr/local/share/vice`;
generated files stay in ignored `comparison-tests/` (or an external `--workspace`).
**Run `python tools/compare_renderers.py --check` before publishing.**
Optional `--max-fps 10` and `--lock-to-min-fps` create paced comparison reels;
both default off and never replace the uncapped performance chart.

Toolkit releases such as **0.6.9** and renderer generations such as **V9**
are separate version numbers. The original paths draw vectors on the C64;
V8 adds adaptive precomputed byte-span pictures. Projection and hidden-line
visibility are computed on the host for all methods.

| Variant | Data / output | Main change or purpose |
| --- | --- | --- |
| `step` | Resident tables / PRG | Packed steps, pixel-by-pixel drawing; regression baseline. |
| `bytechunk` | Resident tables / PRG | Combine full aligned eight-pixel X-major chunks into bitmap-byte masks. |
| `yunroll` | Resident tables / PRG | Add unrolled Y-major scanline phases; default PRG renderer. |
| `yunroll-cart` | Resident tables / cartridge scaffold | Initial cartridge reference, before the banked frame-streaming backend. |
| `yunroll-cart-v2` | EasyFlash frame stream | Fixed RAM staging, three bitmap buffers, cached clear/colour metadata and 16-bit run counts; preserved early `cart-stream` renderer. |
| `yunroll-cart-v3` | EasyFlash frame stream | Faster dispatch/header decoding, batched run counting, Y-major fall-through and copy-path improvements. |
| `yunroll-cart-v4` | EasyFlash frame stream | Remove the per-line dispatch call/return pair; preserved early twelve-demo menu renderer. |
| `yunroll-cart-v4-scene` | Authored EasyFlash sequence | V4 drawing with paged directories, 16-bit frame indexing, pacing and a finite intro/ending. |
| `yunroll-cart-v5` / `-v5-scene` | EasyFlash stream / sequence | Lossless redundant-run removal, identical-picture sharing/reuse, full-block Y drawing and four-section page copies. |
| `yunroll-cart-v6` / `-v6-scene` | EasyFlash stream / sequence | V5 data savings plus partial X-major byte accumulation and direct loading into the recycled slot's metadata cache. Preserved rc3 comparison. |
| `yunroll-cart-v7` / `-v7-scene` | EasyFlash stream / sequence | Join compatible runs without changing pixels, choose cell/byte clearing, optional smaller Y kernels. FPS preferred by default; menu adds PLAY ALL. |
| `yunroll-cart-v8` / `-v8-scene` | Hybrid EasyFlash stream / sequence | V7 vector fallback plus smaller precomputed bitmap-byte spans. No extra fixed buffers; same samples and colours. |
| `yunroll-cart-v9` / `-v9-scene` | Direct-ROM hybrid stream / sequence | V8 picture payloads with direct ROM-to-bitmap byte drawing and a leaner page copier. Normal PLAY ALL is the A/B reference. |

### `step`

The v0.7-style packed-step renderer. The host precomputes minor-axis decisions and the 6510 rasterizes the lines pixel-by-pixel. Kept as a regression/benchmark reference.

### `bytechunk`

The v0.8 renderer. Full aligned X-major chunks are combined into VIC-II bitmap-byte masks, reducing repeated bitmap read/modify/write operations. Stable reference path.

### `yunroll`

Default PRG renderer. Keeps byte-chunk X-major rendering and additionally unrolls Y-major scanline phases. The historical 256x144 default 10x5 torus measured around **15-18 FPS** in the development setup; wider 192/200-line viewport builds perform more drawing/clearing work and may run slower. Those historical PRG figures are not a matched comparison with the cartridge builds below.

### What V5 optimizes

V5 removes whole line records whose pixels are already supplied by retained
records, including exact duplicates. It resolves cell colours first and keeps
the original colour spans, so bitmap and colour attributes remain identical.
It also stores identical complete pictures once in ROM. Each logical animation
sample still exists: an already resident picture can be reused without drawing;
a ROM reference whose picture has left the three buffers must be drawn again.
This preserves sample order and holds, including colour-only changes.

The C64 path also processes complete eight-pixel Y-major blocks with one count
update, and copies full pages as four 64-byte sections with one shared index.
Memoizing host DDA selection reduces compilation work; that part does not raise
C64 FPS. These changes preserve hires geometry, colours and animation samples.

Measured sizes of the shipped carts:

| Cartridge | V4 CRT bytes | V5 CRT bytes | Bytes saved | Reduction |
| --- | ---: | ---: | ---: | ---: |
| Twelve-demo menu | 968,608 | 927,568 | 41,040 | 4.24% |
| Marbles, clean | 525,376 | 418,672 | 106,704 | 20.31% |
| Marbles, HUD | 525,376 | 418,672 | 106,704 | 20.31% |

The vector payload falls from 580,017 to 538,330 bytes in the menu cart
(7.19%), and from 405,972 to 323,159 bytes in Marbles (20.40%). Marbles has
200 distinct pictures: its savings come from redundant line removal, not
dropping or holding animation samples. CRT sizes also include stored chip
headers, runtime code and bank padding; the EasyFlash target remains 1 MiB.

### What V6 adds

Partial X-major heads and tails now accumulate bits before writing each affected
bitmap byte. After clearing the old buffer, the streamer places incoming
clear/colour metadata directly in that buffer's cache and stages only the line
records. This removes the extra staging-to-cache copy. ROM mapping is still
restored between bounded copy bursts.

V6 keeps V5's vector payload and the same shipped CRT sizes. In the matched
regular horse build, resident code/data grows by **90 bytes net**; the lookup
tables and allocated buffers do not grow. Clean Marbles' mean render cost drops
3.63%, and its paced 200-sample scene takes 31.43 seconds versus V5's 32.07.
The [V6 guide](docs/CARTRIDGE_STREAM_V6.md) records all twelve FPS comparisons,
worst-frame costs, RAM accounting and verification limits.

```bash
./build.sh cart-demos --stream-renderer yunroll-cart-v6
python tools/build_v6_examples.py
```

### What V7 adds

V7 joins connected, compatible paths under fewer line headers, using their exact
packed step decisions. It also chooses trimmed byte clearing where cheaper,
without increasing metadata size. Original resolved colours and sample timing
are preserved. `--prefer fps` is the default; `--prefer ram` saves **1,052
resident code bytes** in the matched regular horse build, at a measured speed
cost. Tables and bitmap/staging allocations stay the same.

The HiFi horse reaches **10.018 FPS versus V6's 8.742**, and the HiFi sunflower
**6.989 versus 6.139**. Clean Marbles takes **30.45 seconds versus 31.43**, with
all 200 samples and seven PAL ticks per sample retained. Full comparisons,
worst-frame costs and the menu's F1/party launch regression check are in the
[V7 guide](docs/CARTRIDGE_STREAM_V7.md).

| Cartridge | V6 CRT bytes | V7 CRT bytes | Saved |
| --- | ---: | ---: | ---: |
| Twelve-demo menu | 927,568 | 804,448 | 123,120 (13.27%) |
| Marbles, clean | 418,672 | 353,008 | 65,664 (15.68%) |
| Marbles, HUD | 418,672 | 353,008 | 65,664 (15.68%) |

PLAY ALL is a fixed item above the V7 menu list. It loops all twelve animations,
10 seconds each by default, with SPACE to skip and RUN/STOP/F1 to return.
`--play-all-seconds` accepts 1..255, measured as 50 PAL ticks per second.
F1 in the menu continues to cycle all three styles, including the flashing party
menu. The `-ram` comparison cartridges are supplied alongside the FPS defaults.

```bash
python tools/build_v7_examples.py
python tools/build_v7_examples.py --prefer ram
./build.sh cart-demos --stream-renderer yunroll-cart-v7 --play-all-seconds 20
```

A broader compact/balanced renderer with adjustable buffer and table allocations
remains [planned](docs/ROADMAP.md#memory-and-cpu-profiles-independent-of-the-application).
The current preference changes Y kernels. Either preference can serve a demo
or a game; input/sequence handling and memory budgets belong above shared drawing.

## HUD

Generated demos show topology at lower left and live guest-side FPS at lower right:

```text
TORUS V:050 E:100                 FPS:017
HORSE HEAD V:064 E:124            FPS:...
```

`V` means vertices and `E` means unique mesh edges. `--polycount` refers to faces, not vertices.

## Repository layout

```text
c64-3d-toolkit/
├── README.md
├── build.sh
├── c643d.py
├── setup-windows.cmd
├── setup-windows.ps1
├── config/
│   └── c643d.ini.example
├── c64/
│   ├── renderer-step.asm
│   ├── renderer-bytechunk.asm
│   ├── renderer-yunroll.asm
│   ├── renderer-yunroll-cart.asm
│   └── cart/
│       └── easyflash-smoke.asm
├── tools/
│   ├── blender_export.py
│   ├── asm_sanity.py
│   └── c643d/
│       ├── assets.py
│       ├── blender.py
│       ├── cartridge.py
│       ├── cli.py
│       ├── checksums.py
│       ├── colors.py
│       ├── emit.py
│       ├── font.py
│       ├── mesh.py
│       ├── objio.py
│       ├── pipeline.py
│       ├── sceneio.py
│       ├── shapes.py
│       ├── svgio.py
│       └── toolchain.py
├── examples/
│   ├── blender/
│   │   ├── falling_cubes_c64.py
│   │   ├── falling_cubes_c64.blend
│   │   ├── falling_cubes_full.py
│   │   └── falling_cubes_full.blend
│   ├── examples.json
│   └── *.prg
├── objects/
│   ├── README.md
│   ├── horse_head.obj
│   ├── horse_head.json
│   ├── sunflower_torus.obj
│   ├── sunflower_torus.mtl
│   ├── sunflower_torus.json
│   ├── space_horse.svg
│   ├── space_horse.json
│   └── space_horse_crawl.json
├── generated/
├── build/
├── tests/
│   └── data/golden_prg_checksums.json
└── docs/
    ├── ARCHITECTURE.md
    ├── BLENDER_PIPELINE.md
    ├── CARTRIDGE_PIPELINE.md
    ├── CARTRIDGE_REFERENCES.md
    ├── CARTRIDGE_ROADMAP.md
    ├── CONFIGURATION.md
    ├── OBJ_PIPELINE.md
    ├── SVG_PIPELINE.md
    ├── WINDOWS_SETUP.md
    ├── REFERENCES.md
    └── ROADMAP.md
```

## Roadmap

The current source paths already converge on the same host compiler/runtime:

```text
Blender .blend      .c643dscene      OBJ/MTL      SVG      procedural
     |                   |              |          |           |
     v                   |              v          v           v
headless bpy export -----+------> source-specific ingest / scene frames
                                      |
                                      v
                         projection / visibility / clipping
                                      |
                                      v
                           vector + colour table emission
                                      |
                                      v
                                   64tass
                                      |
                         +------------+-------------+
                         |                          |
                         v                          v
                  PRG -> VICE / C64       EasyFlash pack/cartconv
                                                    |
                                                    v
                                             CRT -> VICE / cart
```

Future work includes topology-aware mesh simplification, better host-side preview
and C64 cost estimation, and richer authoring tools. A graphical importer/
previewer is planned, but the command-line path will remain first-class.

## Status

**Version 0.6.6 includes the Marbles early beta.** The production PRG pipeline
remains compatible with the verified v0.6.2 baseline, while cartridge work is
kept in a separate EasyFlash backend. Current cartridge milestones include:

- native EasyFlash boot and deterministic bank switching;
- `.crt` creation through optional VICE `cartconv` tooling;
- explicit `cartconv` discovery, configuration, `doctor` reporting, and useful
  failure messages;
- a menu-driven multi-animation demo cartridge built with `cart-demos` or
  `--generate-cart-demos`, with live F1 menu-style cycling, F1/RUN-STOP menu return, and SPACE next-demo controls;
- cartridge bank maps and JSON manifests;
- C64-side VICE/debug-cart validation of banked payload copying; and
- the independent `yunroll-cart-v2` streamer, 16-bit run counts and HiFi demos.

The final demo cartridge streams all twelve entries through V7. Their animation tables consume cartridge ROM while a fixed frame
buffer and per-bitmap metadata caches are reused in RAM. The current V2 limits
include 255 orientations, an 8 KiB frame block, and OBJ/SVG/procedural inputs;
Long Blender scenes use the separate `yunroll-cart-v4-scene` extension; see [the scene guide](docs/CARTRIDGE_SCENES.md).

The animated Blender scene pipeline introduced in v0.6.0 remains first-class.
`.blend` builds run Blender headlessly with its own bundled `bpy`, evaluate
authored object/camera/material state including stable-topology deformation and
rigid-body motion, and feed the same hidden-line/colour/vector compiler used by
the existing procedural, OBJ/MTL, and SVG paths. Authored Blender frame
selection remains strict: table overflow fails with actionable
sampling/range/detail suggestions instead of silently reducing the animation.

The Windows setup helper introduced in v0.5.1 also remains included: Python,
Git, and VICE can be detected or installed through WinGet, while 64tass remains
an explicit manual trust decision on Windows.

---

For the complete release history and detailed changes, see
[`CHANGELOG.md`](CHANGELOG.md).

---

## Credits

By [FlyingFathead](https://github.com/FlyingFathead), _with ChaosWhisperer lurking somewhere in the machinery._

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.**
