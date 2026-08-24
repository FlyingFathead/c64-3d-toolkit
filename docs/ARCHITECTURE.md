# Architecture

`c64-3d-toolkit` is split deliberately into a host compiler and a small C64 runtime.

## Host side

Python owns the expensive/general operations:

```text
procedural shape / OBJ / SVG preset
        -> mesh/contour cleanup + source conversion
        -> initial pose
        -> sampled animation transform (spin / recede / crawl)
        -> perspective projection
        -> face visibility + host Z-buffer where surfaces exist
        -> hidden-line clipping
        -> renderer-specific vector record encoding
        -> dirty clear data + HUD
```

Named OBJ and SVG assets live under `objects/`. JSON sidecars store stable object metadata so the CLI and future graphical tooling can use the same project format.

OBJ data enters as polygon surfaces. SVG data enters as explicit contour edges: curves are flattened and simplified on the host, and an optional shallow Z extrusion can duplicate/connect those contours without pretending glyph holes are simple filled polygons.

## C64 side

The C64 renderer receives sampled vector records, not complete bitmap frames. It:

- clears/reuses hidden hires buffers;
- rasterizes visible wireframe runs;
- presents completed buffers through the VIC-II;
- maintains the guest-side FPS display.

Current renderer backends are kept independently selectable for benchmarking/regression:

- `step`
- `bytechunk`
- `yunroll`

The generated demo can choose a C64 hires foreground colour. SVG imports can infer that colour from source artwork; the current renderer still uses one foreground/background pair for the whole demo rather than per-vector colours.

## Animation tables

The runtime still only advances a finite table of precomputed frames. What changed is the host transform used to produce those frames:

- `spin` rotates around X/Y/Z as before;
- `recede` translates a front-facing object away from the camera;
- `crawl` fixes the object onto an X-tilted virtual plane and translates it upward/away.

This lets 2-D vector artwork behave as geometry in perspective without adding a matrix engine to the 6510 runtime.

## Memory pressure

Geometry detail affects both runtime cost and generated table RAM. The compiler therefore keeps requested geometry first and reduces sampled frame count when necessary. `--strict-frames` changes that policy to fail instead.

This is particularly relevant for arbitrary OBJ meshes and vector logos. The bundled 64-vertex horse head currently compiles at 36 sampled orientations; the bundled SPACE HORSE SVG presets are intentionally simplified to a C64-friendly wire count and auto-fit to the table budget.

## Future simplifier / GUI

A future OBJ simplification stage and graphical preview should call the same Python mesh/pipeline modules rather than reimplementing the compiler. CLI object metadata is intentionally JSON for this reason. SVG already has a contour-specific simplification stage; host preview should expose its tolerance and animation controls visually.
