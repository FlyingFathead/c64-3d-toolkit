# Examples

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
