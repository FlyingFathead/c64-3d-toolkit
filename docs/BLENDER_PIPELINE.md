> Current conversion default: **hors-renderer-v3**, including authored wireframe scenes. [Checkpoint and cache troubleshooting](HORS_V3_DEFAULTS_CHECKPOINT.md).

# Blender animated-scene pipeline

[Blender FAQ and troubleshooting](BLENDER_FAQ.md) covers the old right-edge
cutoff, full-width rebuilding, camera framing, mirroring and calibration scenes.

The v0.7.2 release used hors-render-v2-scene EasyFlash output; the current checkpoint defaults to HORS-V3. See
[current scene streaming](CARTRIDGE_SCENES.md) and [build targets](HORS_RENDER_V2.md).
Use `--renderer yunroll` explicitly for the preserved resident PRG path. Its
255-sample/table-RAM limits differ from the streamed scene directory's 2048
sample maximum; per-frame and total cartridge capacity can limit either earlier.

Blender is an optional authoring front end. The classic procedural, OBJ, MTL,
and SVG commands do not import `bpy`, launch Blender, or require Blender to be
installed.

For an animated `.blend` scene, the toolkit launches Blender itself:

```text
scene.blend
    -> blender --background ... --python tools/blender_export.py
    -> evaluated objects + active camera for each sampled frame
    -> temporary .c643dscene interchange data
    -> existing hidden-line / colour / DDA compiler
    -> HORS-V3 scene stream by default, or an explicitly selected renderer
```

Blender exports geometry, motion, deformation, materials and camera state.
The host projects/clips that geometry and encodes it for the selected renderer.
HORS-V3 is the current default; older stream formats and explicit resident PRG
renderers retain their own frame, metadata and memory limits.

## Install and verify Blender

The current Blender LTS from <https://www.blender.org/download/> is recommended
for newly authored scenes. Ubuntu 24.04 LTS (`noble`) provides Blender 4.0.2
with working bundled `bpy` as a supported older fallback:

```bash
sudo apt install blender
```

Blender 4.0.2 and Blender 5.2 provide the required camera API.
This does not make `.blend` files backward-compatible: use 5.2 for files saved
by 5.2, or keep authoring/export on the same major version.

Verify the exact integration used by the toolkit:

```bash
blender --background --disable-autoexec --python-expr 'import bpy; print("BLENDER:", bpy.app.version_string); print("CAMERA API:", hasattr(bpy.types.Object, "calc_matrix_camera"))'
```

Windows can install Blender through WinGet:

```powershell
winget install -e --id BlenderFoundation.Blender
```

macOS can use Homebrew:

```bash
brew install --cask blender
```

The official download is available at <https://www.blender.org/download/>.

The `--blend` path performs its own headless `import bpy` preflight. Merely
finding an executable is not considered enough. If Blender is absent or its
embedded Python cannot import `bpy`, the build stops before scene processing
and prints platform-specific installation instructions.

### Embedded-script security

The toolkit invokes Blender with `--disable-autoexec` before opening any
`.blend` scene. This prevents embedded Blender Python scripts from being
automatically executed merely because a scene is being compiled. The headless
preflight uses the same setting.

This is a secure default for imported or third-party `.blend` files. Scenes
that intentionally depend on Blender auto-run scripts should be reviewed and
exported explicitly in a trusted Blender workflow, then compiled from the
resulting `.c643dscene` interchange file.

Do not add `bpy` to the toolkit's Python requirements. `blender_export.py` is
run by Blender's bundled Python, where `bpy` is already present. The ordinary
toolkit remains dependency-free Python.

## Compile an existing Blender scene

The scene needs an active perspective camera and at least one mesh object:

```bash
./build.sh \
    --blend scenes/horse_intro.blend \
    --frame-start 1 \
    --frame-end 96 \
    --sample-step 2 \
    --run
```

`--frame-start` and `--frame-end` default to the Blender scene range. A sample
step of 2 exports frames 1, 3, 5, and so on. The default scene cartridge path
accepts up to 2048 samples, subject to encoded frame and cartridge capacity.
Explicit resident PRG builds accept at most 255 samples and usually reach the
table-RAM limit earlier.

Blender scene builds always preserve authored frame selection. If the tables do
not fit, the toolkit fails and suggests a larger `--sample-step`, a shorter
range, or simpler geometry. It never silently changes 48 authored frames into
36 frames as the legacy 360-degree spinner is allowed to do.

Blender's active camera is authoritative. The toolkit does not normalize,
rotate, or auto-fit Blender geometry. Frame the shot in Blender. Version 1
requires:

- a perspective camera;
- stable vertex and polygon topology across sampled frames;
- geometry in front of the camera. Projected edges may cross the viewport and
  are clipped to the C64 frame; near-plane crossings are not yet supported.

New `.blend` builds now use the full **320×192** artwork area by default. The
bottom eight pixels remain the cartridge HUD row. The earlier 256-pixel width
left an unused 64-pixel strip on the right; a Blender camera adjustment could
not make that renderer draw into it. Full-width clipping now reaches x=319,
and host-generated clear spans are split safely so reused buffers clear it too.

For a matching preview, use **320×192 or 960×576**, square pixels, and frame the
shot through Blender's active perspective camera. Projection is calculated for
the selected output width/height; source lighting, antialiasing and arbitrary
material shaders are not included in the wireframe renderer. Native 8×8-cell
colour limits still apply.

`--viewport-width 256` explicitly retains the old width (preview at 256×192 or
768×576). New `.c643dscene` exports record their viewport width; `--scene`
retains it. Interchange files without width metadata retain the legacy 256
width. An explicit width override on an existing interchange file changes only
clipping, not its stored camera projection. Re-export the `.blend` to calculate
a new full-width camera projection. Existing CRT binaries and historical
benchmark vectors are unchanged; rebuild the source to use the new width.

See the [zoom and tracking-camera test cards](../examples/blender_viewport_test/README.md)
for editable scenes, actual VICE screenshots, edge/centre checks and measured
costs. Optional [input flips](INPUT_FLIPS.md) affect the artwork only.

In **0.6.7**, the exporter preserves outward face orientation when converting
Blender's negative-forward camera Z to the toolkit's positive-forward Z. It
also accounts for reflected object transforms and matches Blender's treatment
of camera object scale. This fixes front-face feature
culling and material choice for newly exported scenes. Use
`tools/verify_blender_camera.py` through Blender to check projection, normals and
material IDs against the actual evaluated Blender scene. Existing `.c643dscene`
files retain their stored polygon order; re-export the `.blend` to apply the fix.

The [horse-and-sunflower close-up](../examples/blender_horse_and_sunflower/README.md)
includes its Blender scene, C64 cartridge and a preview made from C64 output.

Stable topology still permits rigid-body motion, parenting, constraints,
armatures, shape keys, and deforming modifiers that do not add/remove vertices
or polygons. Animated booleans, remeshing, fracture systems that create new
shards during the sampled range, and topology-changing Geometry Nodes are not
supported in version 1.

Set `c643d_export = false` as a custom property on a mesh object to omit it.
Hidden-for-render mesh objects are also omitted.

## Materials and C64 colours

Blender material diffuse colours are mapped to the nearest VIC-II palette
entry during export. For exact selection, add a custom integer property named
`c643d_color` with a value from 0 through 15 to a material or mesh object.
Material properties take precedence over object properties.

Existing colour options remain available:

```bash
./build.sh --blend scene.blend --no-colors
./build.sh --blend scene.blend --color yellow
```

## Falling-cubes example

The C64-oriented bundled generator creates a complete scene containing six coloured cubes,
rigid-body gravity/collisions, a passive floor, and a camera:

```bash
blender --background \
    --python examples/blender_falling_cubes/falling_cubes_c64.py
```

Compile 18 authored samples from its 72 Blender frames:

```bash
./build.sh \
    --blend examples/blender_falling_cubes/falling_cubes_c64.blend \
    --frame-start 1 \
    --frame-end 72 \
    --sample-step 4 \
    --run
```

Rigid-body and other stateful simulations are evaluated sequentially from the
scene/cache start through the last requested frame. Only frames selected by
`--sample-step` are stored in the interchange and C64 tables. This preserves
physics evolution while retaining the intended C64 frame budget. The canonical six-cube
reference uses a step of 4 because the expanded 192-line resident PRG viewport
made the older 24-sample/step-3 build exceed its table-RAM budget. That PRG
constraint is not the streamed cartridge's animation-capacity limit. A warning is
printed if all captured frames are geometrically identical.

The example uses separate stable-topology cubes. They fall, collide, tumble,
and scatter; they do not dynamically fracture into newly created shards. To
make a break-apart shot under the version-1 constraint, model the shards as
separate objects from frame 1 and initially arrange/animate them as a whole.

The same directory also contains `falling_cubes_full.py` and Harry's actual
Blender-4.00 `falling_cubes_full.blend`: five clusters containing 40 small
cubes, a passive floor, and deterministic rigid-body setup. That fuller scene
is included as an authoring/stress reference. It can exceed the present C64
resident PRG limit of 255 visible runs in one frame and available table RAM.
Streamed scene builds allow 16-bit run counts but still require each encoded
frame to fit 8 KiB and the sequence to fit ROM. The six-cube variant remains
the small compile example.

The canonical six-cube scene also has a dedicated regression selector. It builds
both the authored-colour scene and a forced monochrome version in the current
192/200-line lanes, plus the historical authored-colour 144-line reference and
raster-time-profiler PRGs:

```bash
./build.sh test-examples --blender-only
```

This is deliberately separate from the normal example batch so Blender remains
optional. Narrow the run with `--variants normal|legacy144|no-overlay|rastertime-profiler`
or `--only falling_cubes_c64_color-yunroll` /
`--only falling_cubes_c64-yunroll`. Use `generate-examples --blender-only` only
when intentionally refreshing the checked-in Blender PRGs.

## Blender path configuration

`blender` in `PATH` normally needs no configuration. Otherwise use:

```bash
./build.sh --blend scene.blend --blender /path/to/blender
```

or `config/c643d.ini`:

```ini
[toolchain]
blender = blender

[windows]
blender = C:\Program Files\Blender Foundation\Blender 4.0\blender.exe

[macos]
blender = /Applications/Blender.app
```

`./build.sh doctor` reports whether optional Blender discovery succeeds.

## Interchange format

The exporter emits versioned `.c643dscene` JSON containing stable topology,
per-frame camera-space vertices, source frame numbers, and projection values.
Normal `--blend` builds keep this file temporary. It can also be compiled
directly for debugging or other future scene producers:

```bash
./build.sh --scene exported.c643dscene --run
```
