<p align="center">
  <img src="assets/c64-3d-toolkit_banner.png"
       alt="c64-3d-toolkit — Build modern 3D. Fit it in 64K."
       width="100%">
</p>

# c64-3d-toolkit

Host-assisted low-poly wireframe 3D compiler/runtime for a **stock Commodore 64**, with first-class support for animated **Blender `.blend` scenes**, **Wavefront OBJ + MTL**, **SVG artwork**, and built-in procedural geometry.

Animate objects, cameras, modifiers, armatures, or rigid-body scenes in Blender; import coloured OBJ/MTL meshes or SVG paths; or use the classic procedural meshes and animation transforms. The toolkit preprocesses the result on the host, performs projection and hidden-line visibility, then generates 6510/6502 assembly data and runnable C64 `.prg` files whose vectors are drawn live by the C64.

## Requirements

Required:

* [VICE](https://vice-emu.sourceforge.io/) — Commodore 64 emulator; the toolkit uses `x64sc` by default.
* [64tass](https://tass64.sourceforge.net/) — 6502/6510 cross-assembler.
* Python 3.

Recommended:

* [Blender](https://www.blender.org/) 4.0 or newer — the key authored-scene pipeline: animate geometry, physics, and a virtual camera in Blender, then compile those sampled scene frames into vectors drawn live on the C64. Blender supplies its own `bpy` Python environment; do **not** add `bpy` to `requirements.txt` or install it with `pip`.

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
blender --background --python-expr 'import bpy; print("BLENDER:", bpy.app.version_string); print("BPY OK")'
```

Verify that the required tools are available with:

```bash
./build.sh doctor
```

Preflight reports resolved executable paths and versions for 64tass and VICE.
`doctor` additionally launches optional Blender headlessly and reports both its
version and whether `bpy` imports successfully. Every `--blend` build repeats
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
blender --background --python-expr 'import bpy; print("BLENDER:", bpy.app.version_string); print("BPY OK")'
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
tass_args =
vice_args = +VICIIfull

[macos]
# tass = /opt/homebrew/bin/64tass
# vice = /Applications/vice-arm64-gtk3-3.8/bin/x64sc

[windows]
# tass = C:\Tools\64tass\64tass.exe
# vice = C:\Tools\VICE\bin\x64sc.exe
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

## Quickstart

Build and run one of the included procedural objects:

```bash
./build.sh --shape torus --run
```

Build and run an imported OBJ preset:

```bash
./build.sh --object horse_head --run
```

Compile an authored Blender scene and camera animation:

```bash
./build.sh --blend scenes/intro.blend --frame-start 1 --frame-end 96 --sample-step 2 --run
```

The toolkit checks that Blender can run headlessly and import its bundled
`bpy` module before processing a `.blend` file. See
[`docs/BLENDER_PIPELINE.md`](docs/BLENDER_PIPELINE.md) for installation,
stable-topology constraints, material colours, and the generated falling-cubes
rigid-body example.

The Blender examples live under `examples/blender/`, not in the project root:

```bash
# Generate the C64-budget-oriented six-cube scene beside its script.
blender --background --python examples/blender/falling_cubes_c64.py

# Compile 24 samples from that generated scene.
./build.sh --blend examples/blender/falling_cubes_c64.blend \
    --frame-start 1 --frame-end 72 --sample-step 3 --run
```

For stateful simulations such as rigid bodies, the exporter evaluates every
intervening Blender frame sequentially and stores only the requested samples.
Thus `--sample-step 3` reduces C64 table frames without skipping physics steps.
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

Build all included example `.prg` files:

```bash
./build.sh --generate-examples
```

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


## Examples

The repository has an `examples/` manifest. Build all reference PRGs at once:

```bash
./build.sh --generate-examples
# equivalent:
./build.sh generate-examples
```

This currently produces `torus.prg`, `torus_dense.prg`, `cube.prg`, `sphere.prg`, `horse_head.prg`, monochrome `sunflower_torus.prg`, coloured `sunflower_torus_color.prg`, `space_horse_spin_color.prg`, and `space_horse_crawl_color.prg`. Auxiliary labels/listings remain in `build/`; the runnable PRGs are copied to `examples/`.

## Dependency checks

Every build now performs an early preflight. `64tass` is required unless `--no-assemble` is used. VICE is optional for build-only work but required for `--run`. Override executable names/paths with `--tass` and `--vice`.

```bash
./build.sh doctor
```

On Debian/Ubuntu, distro VICE packages can be DFSG-stripped and omit Commodore ROM images. The emulator executable may therefore exist but still fail at machine startup until compatible ROMs are installed/configured. This is separate from the toolkit preflight, which only verifies that the executable is present.

## Current state

The reference torus now runs around **15-18 FPS** with `yunroll` on stock PAL C64 timing in VICE during development. It is native 320x200 hires, hidden-line clipped, triple-buffered, and does not use pre-rendered bitmap animation frames.

The project grew out of the rotating-torus benchmark, a.k.a. **THE WORLD'S MOST DANGEROUS ROTATING DONUT**, and is now being generalized into a reusable mesh-to-C64 pipeline.

The repository includes the actual `objects/horse_head.obj` low-poly model (64 vertices / 124 edges / 65 faces), `objects/sunflower_torus.obj` + `.mtl` (76 vertices / 142 edges / 70 faces), and the bundled `objects/space_horse.svg` vector-logo demo.

## What happens on the host vs. the C64?

The host-side Python compiler performs expensive work that makes sense to precompute for a ~1 MHz target:

- procedural mesh generation, Wavefront OBJ parsing, or SVG contour flattening/simplification
- normalization and coordinate-system conversion
- face-winding repair
- sampled animation transforms (`spin`, `recede`, or tilted-plane `crawl`)
- perspective projection
- face visibility
- host-side Z-buffer hidden-line clipping
- C64-oriented line-step encoding
- dirty-area and hires screen-colour span generation

The C64 still rasterizes the visible wireframe itself into VIC-II hires bitmap RAM. `step`, `bytechunk`, and `yunroll` are vector/line renderers, not bitmap-frame players.

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

### `step`

The v0.7-style packed-step renderer. The host precomputes minor-axis decisions and the 6510 rasterizes the lines pixel-by-pixel. Kept as a regression/benchmark reference.

### `bytechunk`

The v0.8 renderer. Full aligned X-major chunks are combined into VIC-II bitmap-byte masks, reducing repeated bitmap read/modify/write operations. Stable reference path.

### `yunroll`

Current fastest path. Keeps byte-chunk X-major rendering and additionally unrolls Y-major scanline phases. Measured around **15-18 FPS** on the default 10x5 torus in the current development setup.

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
│   └── renderer-yunroll.asm
├── tools/c643d/
│   ├── assets.py
│   ├── cli.py
│   ├── colors.py
│   ├── mesh.py
│   ├── shapes.py
│   ├── objio.py
│   ├── svgio.py
│   ├── toolchain.py
│   ├── pipeline.py
│   ├── emit.py
│   └── font.py
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
└── docs/
    ├── ARCHITECTURE.md
    ├── CONFIGURATION.md
    ├── OBJ_PIPELINE.md
    ├── SVG_PIPELINE.md
    ├── WINDOWS_SETUP.md
    ├── REFERENCES.md
    └── ROADMAP.md
```

## Roadmap

The intended eventual workflow is:

```text
Blender / modeller / vector editor / generated asset
        |
        v
Wavefront OBJ / SVG
        |
        v
import + inspect
        |
        v
normalize / repair / simplify
        |
        v
preview + C64 cost estimate
        |
        v
hidden-line / vector compilation
        |
        v
64tass
        |
        v
PRG -> VICE / real C64
```

A graphical host-side importer/previewer is planned, but the command-line path will remain first-class.

## Status

Version 0.5.1 is a small Windows-setup release on top of 0.5.0's colour-wireframe pipeline. It adds the Windows setup helper and documentation without changing the C64 renderer: Python, Git, and VICE can be detected or installed through WinGet, while 64tass remains an explicit manual trust decision on Windows.

## Credits

By [FlyingFathead](https://github.com/FlyingFathead), _with ChaosWhisperer lurking somewhere in the machinery._
