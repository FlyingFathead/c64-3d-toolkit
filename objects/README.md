# Objects

This directory contains reusable low-poly OBJ assets and optional JSON metadata presets.

A named object normally consists of:

```text
my_object.obj
my_object.json
# optional material files referenced by mtllib
my_object.mtl
```

Import one with:

```bash
./build.sh import-obj ~/models/my_object.obj --as my_object --up z
```

Then:

```bash
./build.sh --object my_object --run
```

Included reference objects:

- `horse_head.obj` (64 vertices, 124 edges, 65 faces)
- `sunflower_torus.obj` + `sunflower_torus.mtl` (76 vertices, 142 edges, 70 faces)

The JSON sidecar can define:

```json
{
  "name": "MY OBJECT",
  "file": "my_object.obj",
  "up_axis": "z",
  "spin_axis": "y",
  "rotate": [0.0, 0.0, 0.0],
  "scale": 1.0
}
```

Current OBJ compilation expects models to already be reasonably low-poly. Automatic topology-aware simplification is roadmap work.


`import-obj` preserves directly referenced `mtllib` files next to the imported OBJ. MTL data is not yet used by the C64 wireframe renderer, but is kept for future host-side preview/material tooling.
