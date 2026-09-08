⚠️🐴 Attention! For best quality, please enjoy each animation with `hors-render-v1` or a newer variant.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

**Current hors-render-v1 cartridge:** [play the example](../cart_horse_and_sunflower/README.md).

# Horse and sunflower

**0.6.7 — standalone scene test, kept separate from the multi-demo menu.**

A very close side-view shot of the HiFi horse sniffing the HiFi sunflower.
The original purple/blue/cyan horse and yellow/brown/green flower retain all
378 vertices, 416 polygons and their original material assignments. The flower
faces partly toward the camera. Only the horse moves: approach, two gentle
sniffs, linger, then ease back into a seamless loop.

- [Editable Blender scene](horse_and_sunflower.blend)
- [Standalone C64 cartridge and emulator preview](../cart_horse_and_sunflower/README.md)
- [Scene generator](horse_and_sunflower.py)

![Blender close-up at the sniff](horse_and_sunflower-blender-preview.png)

## Opening and editing

Open `horse_and_sunflower.blend` in Blender 4.0 or newer. The saved view is the
active camera. The timeline runs from 1 to 250 at 25 FPS. The `Horse_motion`
empty carries the only animation; its child is the original horse mesh.
Timeline markers identify the approach, sniffing beats and return.

The camera uses a fixed 82 mm perspective lens and 4:3 framing at 768×576.
The tight crop of the neck, ear tips and lower stem is intentional. The flower
and camera have no animation. The scene contains no external texture files.

`Original HiFi meshes - C64 export` contains the two source meshes. Coloured
CURVE objects in `Coloured wire preview - Blender only` draw the original edges
for the desktop render; the C64 exporter ignores them. Mesh material viewport
colours and `c643d_color` properties retain the source MTL palette. Black surface
shaders occlude the rear preview edges. The original asset files are unchanged.

Blender's smooth wire render shows the composition. The C64 capture shows its
256×192 rasterized geometry, native 8×8-cell colour choices and actual emulator
timing. The C64 bitmap is 320×200, so this existing renderer also has an unused
strip on the right and a blank bottom HUD row in the clean build.

## Rebuilding

From the project root, with Blender, 64tass and VICE's cartconv available:

```bash
python tools/build_horse_and_sunflower.py
```

This uses the saved `.blend`, exports 84 samples (every third source frame),
and builds a looping `yunroll-cart-v7-scene` cartridge with `--prefer fps`.
Use `--blender /path/to/blender`, `--tass /path/to/64tass` and
`--cartconv /path/to/cartconv` when those tools are not on PATH.
`--regenerate` recreates the scene from the original OBJ/MTL files; omit it to
preserve your Blender edits. `--prefer ram` is available as a comparison build.

To regenerate only the Blender scene:

```bash
blender --background --python-exit-code 1 --python examples/blender_horse_and_sunflower/horse_and_sunflower.py
```

The standalone cart requests six PAL ticks per sample (8.33 FPS), but this large
two-mesh close-up currently exceeds that budget. In PAL VICE the unchanged
84-sample loop takes **19.71 seconds, about 4.3 samples per second**. Samples are
retained in order. This first test establishes the shot and correct output;
its playback speed remains an area for future work. It stays separate from the menu.

## Verification

The saved scene was reopened in Blender 4.0.2 and checked against both source
OBJs/MTLs: exact topology, material IDs and vertex coordinates within Blender's
float precision. Camera/flower transforms stay constant across the full loop;
the horse's closing pose equals its opening pose. No horse/flower surface
intersections were found at the twelve checked rest, approach and sniff poses.
See [scene validation](scene-validation.json).

The shared export regression checks a moving ordinary and mirrored mesh with a
rotated, shifted camera. Projection agrees with Blender within **0.00002 pixels**,
outward normals match and face material IDs are preserved. See
[camera validation](blender-camera-validation.json) and
[the pipeline guide](../../docs/BLENDER_PIPELINE.md).

```bash
blender --background --python-exit-code 1 --python tools/verify_blender_camera.py -- --output build/blender-camera-validation.json
blender --background examples/blender_horse_and_sunflower/horse_and_sunflower.blend --python-exit-code 1 --python examples/blender_horse_and_sunflower/verify_scene.py
```
