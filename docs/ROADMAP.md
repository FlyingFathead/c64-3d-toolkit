# Roadmap

## Renderer / performance

- Cycle-profile `yunroll` hot paths in the VICE monitor.
- Explore self-modified absolute bitmap accesses where they beat `(zp),Y`.
- Improve dirty-byte clearing using generator-side cycle-cost estimates.
- Add a renderer benchmark/report mode that records estimated and measured costs.
- Keep `step` and `bytechunk` as regression baselines while optimizing `yunroll`.

## Mesh / asset pipeline

Implemented foundation:

- Wavefront OBJ parsing for vertices and polygon faces.
- Named `objects/` presets with JSON metadata for OBJ and SVG assets.
- `import-obj`, `import-svg`, `list-objects`, `inspect`, and `--object` workflow.
- Y-up/Z-up conversion.
- X/Y/Z spin-axis selection plus `recede` and tilted-plane `crawl` animation transforms.
- Topology diagnostics.
- Consistent winding repair for concave closed meshes.
- Bundled `horse_head.obj`, `sunflower_torus.obj`, and `space_horse.svg` reference assets.
- SVG path/primitive flattening, contour simplification, optional wire extrusion, and SVG-colour -> C64-colour mapping.
- Per-face OBJ/MTL and per-contour SVG colour propagation into dominant-colour VIC-II hires cells, with a compile-time-isolated monochrome path.

Next:

- Optional vertex welding and duplicate cleanup.
- Degenerate face/edge cleanup.
- Topology-aware mesh simplification/decimation to a target C64 budget.
- Preserve/select sharp and silhouette-important edges during simplification.
- Cost-aware detail target: not only face count, but estimated line pixels / table RAM / renderer cycles.
- More built-ins (icosphere, pyramid, ship-like benchmark meshes).

## Host UI / tooling

- Optional graphical OBJ/SVG import/preview application.
- Interactive orientation and up-axis selection.
- Detail/poly/vertex budget slider.
- Preview projected hidden-line output for any sampled orientation.
- Show estimated C64 cost and table-RAM usage before compiling.
- Export/import the same JSON object presets used by the CLI.

## Intended workflow

```text
Blender / modeller / vector editor / generated asset
    -> Wavefront OBJ / SVG
    -> c64-3d-toolkit import-obj / import-svg
    -> topology diagnostics / contour simplification
    -> simplify to a C64-friendly budget
    -> preview / cost estimate
    -> vector/hidden-line compile
    -> 64tass
    -> PRG / VICE / real C64
```

The CLI remains first-class even if a GUI is added.

## Host-side asset workflow additions

- Interactive/graphical OBJ/SVG preview and animation inspection while retaining a first-class CLI workflow.
- Topology-aware mesh simplification/decimation to a C64 vertex/edge/face and table-RAM budget.
- Display existing OBJ/MTL material groups and SVG contour colours in the future host preview.
- Explore optional dither/style policies for mixed-colour hires cells while preserving the current deterministic dominant-colour mode.
- SVG clipping/mask/text-layout support where it can be made deterministic and C64-budget aware.
