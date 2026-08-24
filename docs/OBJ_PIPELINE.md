# OBJ pipeline

## Current pipeline

```text
OBJ -> parse -> inspect -> coordinate conversion -> normalize -> winding repair
    -> sampled rotations -> projection -> hidden-line clipping -> C64 vector records
    -> 64tass -> PRG
```

The importer deliberately keeps the OBJ parser small and dependency-free.

## Repository presets

`import-obj` copies the source OBJ into `objects/` and writes a JSON sidecar. This separates persistent object metadata from one-off build flags and gives a future GUI a stable project format to edit.

## Diagnostics

`inspect` reports topology features that matter to the hidden-line compiler:

- vertex/edge/face counts
- triangle/quad/n-gon mix
- boundary edges
- non-manifold edges
- isolated vertices

Non-manifold/open meshes are allowed, but automatic winding and hidden-line results are necessarily more heuristic than for closed orientable meshes.

## Simplification roadmap

The intended low-poly converter should eventually support a target C64 budget (faces/vertices/edges and estimated raster cost). A proper implementation should preserve silhouette and important sharp edges. Random face deletion is explicitly not considered a valid decimator.

Likely stages:

1. vertex welding / duplicate cleanup
2. degenerate face removal
3. topology diagnostics
4. quadric-error or clustering-based simplification
5. optional sharp/silhouette edge preservation
6. host preview and per-orientation C64 cost estimate
7. compile to the selected renderer

A GUI can sit on top of the same CLI/library pipeline later.

## Hidden-line handling for imperfect OBJ meshes

Imported meshes are not assumed to be closed/manifold. `surface`,
`surface_features`, and `surface_creases` build a host-side reciprocal-depth
Z-buffer from the mesh surface. The Z-buffer also stores the winning source
face for each pixel. A wire edge is considered visible when the nearest surface
pixel belongs to one of that edge's own adjacent faces, which prevents numerical
self-occlusion of feature edges while still allowing unrelated geometry to hide
it.

`surface_features` is the cheaper v0.3.1-style mode: ordinary two-face manifold
edges are pre-culled when both adjacent faces are back-facing, while boundary and
non-manifold edges are retained. `surface_creases` starts from the same rule but
also preserves sharp manifold crease edges selected by `--feature-angle`. Full
`surface` performs no face-normal edge pre-cull and is the bundled `horse_head`
default; `sunflower_torus` uses `surface_features`.

## Materials

`import-obj` preserves directly referenced `mtllib` files next to the imported
OBJ and rewrites flattened references when necessary. Material data is not yet
used by the C64 wireframe renderer; preserving it keeps imported assets intact
for future graphical preview/material tooling.
