# c64-3d-toolkit

Host-assisted low-poly wireframe 3D compiler/runtime for a **stock Commodore 64**.

The toolkit preprocesses 3D geometry on the host machine and generates 6510/6502 assembly data and runnable C64 `.prg` files. It includes procedural test meshes, OBJ import, several visibility modes, multiple renderers, and prebuilt example programs.

## Requirements

Requires:

* [VICE](https://vice-emu.sourceforge.io/) — Commodore 64 emulator; the toolkit uses `x64sc` by default.
* [64tass](https://tass64.sourceforge.net/) — 6502/6510 cross-assembler.
* Python 3.

On Debian/Ubuntu and derivatives, VICE and 64tass can normally be installed with:

```bash
sudo apt install vice 64tass
```

Verify that the required tools are available with:

```bash
./build.sh doctor
```

## Quickstart

Build and run one of the included procedural objects:

```bash
./build.sh --shape torus --run
```

Build and run an imported OBJ preset:

```bash
./build.sh --object horse_head --run
```

or:

```bash
./build.sh --object sunflower_torus --run
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

This currently produces `torus.prg`, `torus_dense.prg`, `cube.prg`, `sphere.prg`, `horse_head.prg`, and `sunflower_torus.prg`. Auxiliary labels/listings remain in `build/`; the runnable PRGs are copied to `examples/`.

## Dependency checks

Every build now performs an early preflight. `64tass` is required unless `--no-assemble` is used. VICE is optional for build-only work but required for `--run`. Override executable names/paths with `--tass` and `--vice`.

```bash
./build.sh doctor
```

On Debian/Ubuntu, distro VICE packages can be DFSG-stripped and omit Commodore ROM images. The emulator executable may therefore exist but still fail at machine startup until compatible ROMs are installed/configured. This is separate from the toolkit preflight, which only verifies that the executable is present.

## Current state

The reference torus now runs around **15-18 FPS** with `yunroll` on stock PAL C64 timing in VICE during development. It is native 320x200 hires, hidden-line clipped, triple-buffered, and does not use pre-rendered bitmap animation frames.

The project grew out of the rotating-torus benchmark, a.k.a. **THE WORLD'S MOST DANGEROUS ROTATING DONUT**, and is now being generalized into a reusable mesh-to-C64 pipeline.

The repository includes the actual `objects/horse_head.obj` low-poly model (64 vertices / 124 edges / 65 faces) and `objects/sunflower_torus.obj` + `.mtl` (76 vertices / 142 edges / 70 faces) as bundled non-procedural reference objects.

## What happens on the host vs. the C64?

The host-side Python compiler performs expensive work that makes sense to precompute for a ~1 MHz target:

- procedural mesh generation or Wavefront OBJ parsing
- normalization and coordinate-system conversion
- face-winding repair
- sampled rotation orientations
- perspective projection
- face visibility
- host-side Z-buffer hidden-line clipping
- C64-oriented line-step encoding
- dirty-area generation

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

Texture/normal indices are currently ignored. Polygon faces are triangulated internally for visibility/Z-buffer work while polygon boundary edges remain the wireframe edges. Direct `mtllib` references are preserved by `import-obj`; MTL data is currently kept for interchange/future host preview rather than used by the C64 wireframe renderer.

### Current limitation

The toolkit does **not yet contain a general mesh decimator**. Imported meshes should currently already be reasonably low-poly. Automatic simplification to a requested C64 face/edge budget is on the roadmap; it will be implemented as a real topology-aware stage rather than deleting random faces and pretending that is decimation.

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
├── c64/
│   ├── renderer-step.asm
│   ├── renderer-bytechunk.asm
│   └── renderer-yunroll.asm
├── tools/c643d/
│   ├── assets.py
│   ├── cli.py
│   ├── mesh.py
│   ├── shapes.py
│   ├── objio.py
│   ├── pipeline.py
│   ├── emit.py
│   └── font.py
├── objects/
│   ├── README.md
│   ├── horse_head.obj
│   ├── horse_head.json
│   ├── sunflower_torus.obj
│   ├── sunflower_torus.mtl
│   └── sunflower_torus.json
├── generated/
├── build/
├── tests/
└── docs/
    ├── ARCHITECTURE.md
    ├── OBJ_PIPELINE.md
    ├── REFERENCES.md
    └── ROADMAP.md
```

## Roadmap

The intended eventual workflow is:

```text
Blender / modeller / generated mesh
        |
        v
Wavefront OBJ
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

Still WIP. The torus remains the performance/reference object; the horse head and sunflower are bundled arbitrary low-poly OBJ references. The next major mesh-pipeline feature is topology-aware simplification/decimation, while renderer work can continue independently.

## Credits

By [FlyingFathead](https://github.com/FlyingFathead)) with ChaosWhisperer lurking somewhere in the machinery.