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

OBJ metadata can define source up-axis, pose, scale, visibility, feature-angle, and source-colour settings. SVG presets additionally carry contour simplification/extrusion settings, a monochrome fallback colour, and an animation mode (`spin`, `recede`, or `crawl`).

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
  "use_colors": true,
  "svg_tolerance": 20.0,
  "svg_curve_step": 12.0,
  "svg_depth": 0.0,
  "svg_connector_stride": 8
}
```

Current OBJ compilation expects meshes to already be reasonably low-poly. Automatic topology-aware OBJ simplification is roadmap work. SVG contours already have a dedicated geometric simplification stage controlled by `--svg-tolerance`.

`import-obj` preserves directly referenced `mtllib` files next to the imported OBJ. The compiler consumes `usemtl` plus diffuse MTL `Kd` values and maps them to native C64 wire colours. `import-svg` does the same for per-contour stroke/fill colours.

Pass `--no-colors` while importing to write `"use_colors": false` into the
preset, or while building to ignore colours for that invocation. `--color`
forces a single named/numeric C64 foreground colour.

## Title-art-inspired HiFi additions

- `horse_head_hifi`: 135 vertices, 299 edges, 178 faces. Full bust, pointed ears, cheek/bridge facets, purple/blue/cyan MTL palette.
- `sunflower_torus_hifi`: 243 vertices, 443 edges, 238 faces. Torus centre, 16 individually bent/cupped petals, curved stem and leaves.

Both have separate OBJ/MTL/JSON presets, closed manifold components, and surface-depth hidden-line culling. The original assets are retained. Materials provide static facet colours; MTL specular settings apply in desktop viewers, while the C64 uses native hires wire colours. See [HiFi showcase](../examples/hifi_showcase/README.md).
