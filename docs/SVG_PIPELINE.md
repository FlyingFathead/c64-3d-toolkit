# SVG pipeline

`c64-3d-toolkit` can import SVG vector artwork and turn it into wire geometry that uses the same host compiler and C64 line renderers as OBJ/procedural meshes.

## Basic use

```bash
./build.sh import-svg path/to/logo.svg --as logo
./build.sh --object logo --run
```

One-off build without adding a preset:

```bash
./build.sh --svg path/to/logo.svg --name LOGO --run
```

The bundled reference asset is `objects/space_horse.svg`.

```bash
./build.sh --object space_horse --run
./build.sh --object space_horse_crawl --run
```

## Geometry conversion

SVG is not triangulated as a filled 2-D shape. Instead, the importer:

1. parses common SVG paths/primitives;
2. applies basic SVG transforms;
3. flattens curves/arcs into polylines;
4. simplifies those polylines with a geometric tolerance;
5. converts SVG Y-down coordinates to toolkit Y-up coordinates;
6. stores contours as explicit wire edges;
7. optionally duplicates the contours in Z and adds sparse front/back connectors for a shallow wire extrusion.

Keeping SVG contours as explicit wire edges is deliberate. Letter holes and concave logo shapes do not need unreliable fan triangulation merely to exist in the wireframe renderer.

## Controls

```text
--svg-tolerance N          simplification tolerance in SVG source units
--svg-curve-step N         curve sampling step before simplification
--svg-depth N              extrusion depth after toolkit normalisation; 0=flat
--svg-connector-stride N   connect every Nth front/back contour vertex
```

A higher simplification tolerance means fewer vertices/edges and less generated table RAM. As with dense OBJ meshes, the C64 budget matters more than host-side parsing cost.

## Animation transforms

The generated frame table is no longer limited to a 360-degree spin. Available host-side transforms are:

- `spin`: historical rotation around `--spin-axis`;
- `recede`: keep the object front-facing and move it away from the camera;
- `crawl`: rotate the object onto a fixed X-tilted virtual plane, then move it upward and away toward a horizon.

```bash
./build.sh --object space_horse --animation spin --run
./build.sh --object space_horse --animation recede --run
./build.sh --object space_horse --animation crawl \
  --animation-tilt 62 --animation-travel 105 --animation-rise 42 --run
```

The animation is still a finite precomputed orientation/pose sequence; the C64 loops through the generated frames and rasterizes every vector line itself.

## SVG colour -> C64 colour

`import-svg` inspects visible stroke/fill colours and maps the first useful artwork colour to the nearest entry in the 16-colour C64 palette. The source SPACE HORSE stroke is `#FFE81F`, which maps to C64 yellow.

Override it with:

```bash
./build.sh --object space_horse --color white --run
./build.sh --svg logo.svg --color 7 --run
```

Current hires demos use one foreground/background colour pair across the generated bitmap screens, so this is object/demo-level colour selection, not per-vector multicolour rendering.

## Current SVG support

Supported vector input includes:

- paths using `M/L/H/V/C/S/Q/T/A/Z` (absolute and relative forms);
- polyline/polygon;
- line;
- rectangle;
- circle/ellipse;
- inherited `fill`/`stroke` style for colour inference;
- matrix/translate/scale/rotate/skew transforms.

A full-canvas rectangle is treated as an exported-artwork background and ignored. Raster `<image>` content, masks, filters, gradients, text layout, clipping paths and CSS-heavy rendering are not interpreted. Convert text to paths before import when exact lettering matters.

SVG geometry is currently contour/wire geometry, not a filled solid. A nonzero `--svg-depth` adds front/back contour copies and wire connectors, but the importer does not synthesize filled cap surfaces through glyph holes. The result is intentionally a see-through wire object rather than a filled extruded font solid.

The importer is intentionally dependency-free and uses the Python standard library.
