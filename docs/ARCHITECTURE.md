# Architecture

`c64-3d-toolkit` is split deliberately into a host compiler and a small C64 runtime.

## Host side

Python owns the expensive/general operations:

```text
shape generator / OBJ preset
        -> mesh cleanup + winding
        -> source-axis conversion + initial pose
        -> sampled X/Y/Z-axis animation
        -> perspective projection
        -> face visibility + host Z-buffer
        -> hidden-line clipping
        -> renderer-specific vector record encoding
        -> dirty clear data + HUD
```

Named OBJ assets live under `objects/`. An optional JSON sidecar stores stable object metadata so both the CLI and a future graphical importer can use the same project format.

## C64 side

The C64 renderer receives sampled vector records, not complete bitmap frames. It:

- clears/reuses hidden hires buffers
- rasterizes visible wireframe runs
- presents completed buffers through the VIC-II
- maintains the guest-side FPS display

Current renderer backends are kept independently selectable for benchmarking/regression:

- `step`
- `bytechunk`
- `yunroll`

## Memory pressure

Mesh detail affects both runtime cost and generated table RAM. The compiler therefore keeps requested mesh topology first and reduces sampled orientation count when necessary. `--strict-frames` changes that policy to fail instead.

This is particularly relevant for arbitrary OBJ meshes. For example, the bundled 64-vertex horse head currently compiles at 36 sampled orientations with the current table layout while keeping all of its mesh geometry.

## Future simplifier / GUI

A future simplification stage and graphical preview should call the same Python mesh/pipeline modules rather than reimplementing the compiler. CLI object metadata is intentionally JSON for this reason.
