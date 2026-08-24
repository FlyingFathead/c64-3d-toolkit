# Objects

This directory contains reusable low-poly OBJ assets, SVG vector assets, and optional JSON metadata presets.

A named OBJ object normally consists of:

```text
my_object.obj
my_object.json
# optional material files referenced by mtllib
my_object.mtl
```

A named SVG object normally consists of:

```text
my_logo.svg
my_logo.json
```

Import either format with:

```bash
./build.sh import-obj ~/models/my_object.obj --as my_object --up z
./build.sh import-svg ~/art/my_logo.svg --as my_logo
```

Then:

```bash
./build.sh --object my_object --run
./build.sh --object my_logo --run
```

Included reference assets:

- `horse_head.obj` (64 vertices, 124 edges, 65 faces)
- `sunflower_torus.obj` + `sunflower_torus.mtl` (76 vertices, 142 edges, 70 faces)
- `space_horse.svg` with spinner and crawl presets

OBJ metadata can define source up-axis, pose, scale, visibility and feature-angle settings. SVG presets additionally carry contour simplification/extrusion settings, a C64 foreground colour, and an animation mode (`spin`, `recede`, or `crawl`).

Example SVG preset fields:

```json
{
  "name": "MY LOGO",
  "file": "my_logo.svg",
  "spin_axis": "y",
  "animation": "crawl",
  "animation_tilt": 62.0,
  "animation_travel": 105.0,
  "animation_rise": 42.0,
  "color": "yellow",
  "svg_tolerance": 20.0,
  "svg_curve_step": 12.0,
  "svg_depth": 0.0,
  "svg_connector_stride": 8
}
```

Current OBJ compilation expects meshes to already be reasonably low-poly. Automatic topology-aware OBJ simplification is roadmap work. SVG contours already have a dedicated geometric simplification stage controlled by `--svg-tolerance`.

`import-obj` preserves directly referenced `mtllib` files next to the imported OBJ. MTL data is kept for interchange/future host preview; the current C64 wireframe renderer does not use MTL shading.
