# Roadmap

## Renderer / performance

- Cycle-profile `yunroll` hot paths in the VICE monitor.
- Explore self-modified absolute bitmap accesses where they beat `(zp),Y`.
- Improve dirty-byte clearing using generator-side cycle-cost estimates.
- Add a renderer benchmark/report mode that records estimated and measured costs.
- Keep `step` and `bytechunk` as regression baselines while optimizing `yunroll`.

## Mesh / OBJ pipeline

Implemented foundation:

- Wavefront OBJ parsing for vertices and polygon faces.
- Named `objects/` presets with JSON metadata.
- `import-obj`, `list-objects`, `inspect`, and `--object` workflow.
- Y-up/Z-up conversion.
- X/Y/Z spin-axis selection.
- Topology diagnostics.
- Consistent winding repair for concave closed meshes.
- Bundled `horse_head.obj` non-procedural reference object.

Next:

- Optional vertex welding and duplicate cleanup.
- Degenerate face/edge cleanup.
- Topology-aware mesh simplification/decimation to a target C64 budget.
- Preserve/select sharp and silhouette-important edges during simplification.
- Cost-aware detail target: not only face count, but estimated line pixels / table RAM / renderer cycles.
- More built-ins (icosphere, pyramid, ship-like benchmark meshes).

## Host UI / tooling

- Optional graphical OBJ import/preview application.
- Interactive orientation and up-axis selection.
- Detail/poly/vertex budget slider.
- Preview projected hidden-line output for any sampled orientation.
- Show estimated C64 cost and table-RAM usage before compiling.
- Export/import the same JSON object presets used by the CLI.

## Intended workflow

```text
Blender / modeller / generated mesh
    -> Wavefront OBJ
    -> c64-3d-toolkit import-obj
    -> topology diagnostics / repair
    -> simplify to a C64-friendly budget
    -> preview / cost estimate
    -> vector/hidden-line compile
    -> 64tass
    -> PRG / VICE / real C64
```

The CLI remains first-class even if a GUI is added.

## Host-side asset workflow additions

- Interactive/graphical OBJ preview and rotation inspection while retaining a first-class CLI workflow.
- Topology-aware mesh simplification/decimation to a C64 vertex/edge/face and table-RAM budget.
- Optional use of preserved OBJ/MTL material groups in host preview and future C64 style/export modes.
