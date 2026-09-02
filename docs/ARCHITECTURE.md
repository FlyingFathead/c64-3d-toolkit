# Architecture

`c64-3d-toolkit` is split deliberately into a host compiler and a small C64 runtime.

## Host side

Python owns the expensive/general operations:

```text
procedural shape / OBJ / SVG preset, or Blender-authored scene frames
        -> mesh/contour cleanup + source colour conversion to VIC-II 0..15
        -> initial pose
        -> sampled animation transform (spin / recede / crawl)
        -> perspective projection
        -> face visibility + host Z-buffer where surfaces exist
        -> hidden-line clipping
        -> renderer-specific vector record encoding
        -> dirty clear data + optional hires colour spans + HUD
```

Named OBJ and SVG assets live under `objects/`. JSON sidecars store stable object metadata so the CLI and future graphical tooling can use the same project format.

Animated `.blend` files follow a separate optional front end. The normal Python
process launches Blender headlessly; Blender's bundled Python and `bpy` evaluate
the dependency graph, object/world/camera transforms, modifiers, armatures,
rigid bodies, materials, and camera projection. A versioned `.c643dscene`
interchange carries camera-space geometry into the same hidden-line, colour,
DDA, table-emission, assembler, and C64 runtime used by legacy sources. The
normal toolkit never imports `bpy`.

OBJ data enters as polygon surfaces; `usemtl` assigns MTL `Kd` colours to faces. SVG data enters as explicit contour edges with per-contour stroke/fill colours: curves are flattened and simplified on the host, and an optional shallow Z extrusion can duplicate/connect those contours without pretending glyph holes are simple filled polygons.

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

Coloured builds update the screen RAM paired with each render bitmap before drawing. When a triple-buffer slot is recycled, its old material cells are first restored to the global `SCREEN_COLOR`, preventing stale colour trails. That cold-path helper lives in the otherwise-unused `$4000-$43ff` gap between bitmap #0 and screen RAM #1. VIC-II hires mode only permits one foreground/background pair per 8x8 cell, so the host chooses the dominant visible wire colour for cells containing several source colours. Tables already contain native four-bit VIC-II codes as complete screen bytes; there is no runtime RGB parsing or palette lookup.

If the imported asset resolves to only one colour, the compiler uses the
historical global `SCREEN_COLOR` byte instead. No colour spans or runtime call
are emitted in that case.

The colour feature is compile-time isolated with `COLORS_ENABLED`. Monochrome
builds assemble out the colour call/routine and keep the historical clear and
line table byte layout. This protects the established white-on-black renderer's
speed, table budget, and geometry behavior.

## Animation tables

The runtime still only advances a finite table of precomputed frames. What changed is the host transform used to produce those frames:

- `spin` rotates around X/Y/Z as before;
- `recede` translates a front-facing object away from the camera;
- `crawl` fixes the object onto an X-tilted virtual plane and translates it upward/away.
- Blender scene frames preserve arbitrary authored object/deformation/camera state.

This lets 2-D vector artwork behave as geometry in perspective without adding a matrix engine to the 6510 runtime.

## Memory pressure

Geometry detail affects both runtime cost and generated table RAM. The compiler therefore keeps requested geometry first and reduces sampled frame count when necessary. `--strict-frames` changes that policy to fail instead.

Blender scene frames are always strict. Automatically reducing an authored
frame sequence could remove semantically important animation states, so an
oversized scene fails with sampling/range/detail suggestions instead.

This is particularly relevant for arbitrary OBJ meshes and vector logos. The bundled 64-vertex horse head currently compiles at 36 sampled orientations; the bundled SPACE HORSE SVG presets are intentionally simplified to a C64-friendly wire count and auto-fit to the table budget.

## Future simplifier / GUI

A future OBJ simplification stage and graphical preview should call the same Python mesh/pipeline modules rather than reimplementing the compiler. CLI object metadata is intentionally JSON for this reason. SVG already has a contour-specific simplification stage; host preview should expose its tolerance and animation controls visually.
