# Examples

Run `./build.sh --generate-examples` to compile the bundled reference programs into this directory.

Current reference set:

- `torus.prg` - default 10x5 torus, `yunroll`
- `torus_dense.prg` - 72-vertex 12x6 torus, `yunroll`
- `cube.prg` - built-in cube
- `sphere.prg` - modest procedural sphere
- `horse_head.prg` - bundled 64-vertex OBJ reference model
- `sunflower_torus.prg` - bundled sunflower OBJ/MTL with a torus-shaped centre
- `space_horse_spin.prg` - bundled SVG logo spinning as planar 3-D wire geometry
- `space_horse_crawl.prg` - same SVG on a tilted plane moving toward a horizon

The reference PRGs are committed for convenience, but they are reproducible build products. Regenerate them after compiler/renderer or asset changes with:

```bash
./build.sh --generate-examples
```

Assembler labels/listings remain transient under `build/`.
