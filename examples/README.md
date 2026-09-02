# Examples

## Blender animated-scene examples

Blender sources live under `examples/blender/` so generated `.blend` files do
not clutter the project root.

- `falling_cubes_c64.py` generates the smaller six-cube, coloured rigid-body
  scene intended for C64 compilation.
- `falling_cubes_full.py` generates Harry's deterministic five-cluster / 40-cube
  authoring and stress scene.
- `falling_cubes_full.blend` is the actual Blender-4.00 scene generated and
  tested on Ubuntu 24.04 with Blender 4.0.2.

Generate and compile the C64-oriented variant:

```bash
blender --background --python examples/blender/falling_cubes_c64.py
./build.sh --blend examples/blender/falling_cubes_c64.blend \
    --frame-start 1 --frame-end 72 --sample-step 3 --run
```

The full 40-cube file proves the richer rigid-body authoring workflow but can
exceed the current C64 limit of 255 visible runs per frame and available table
RAM. It is not represented as a prebuilt PRG in `examples.json`.

Run `./build.sh --generate-examples` to compile the bundled reference programs into this directory.

Current generated reference set:

- `torus.prg` - default 10x5 torus, `yunroll`
- `torus_dense.prg` - 72-vertex 12x6 torus, `yunroll`
- `cube.prg` - built-in cube
- `sphere.prg` - modest procedural sphere
- `horse_head.prg` - bundled 64-vertex OBJ reference model
- `sunflower_torus.prg` - classic monochrome build of the bundled sunflower
- `sunflower_torus_color.prg` - OBJ/MTL colour build; brown centre, yellow petals, green stem/leaves
- `space_horse_spin_color.prg` - bundled SVG logo spinning as yellow planar 3-D wire geometry
- `space_horse_crawl_color.prg` - same SVG on a tilted plane moving toward a horizon

Reference PRGs are reproducible build products. Regenerate them after compiler/renderer or asset changes with:

```bash
./build.sh --generate-examples
```

Assembler labels/listings remain transient under `build/`.
