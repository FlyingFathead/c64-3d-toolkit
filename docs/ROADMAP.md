# Roadmap

## Renderer / performance

- Cycle-profile `yunroll` hot paths in the VICE monitor.
- Explore self-modified absolute bitmap accesses where they beat `(zp),Y`.
- V7 implements generator-selected cell/byte clearing; explore finer plans when decoding cost justifies them.
- Add a renderer benchmark/report mode that records estimated and measured costs.
- Keep `step` and `bytechunk` as regression baselines while optimizing `yunroll`.

### Memory and CPU profiles, independent of the application

Proposed future profiles are **compact**, **balanced** and **speed-focused**.
Each could serve demos or games: a demo may also need RAM and CPU time for SID
music, sprites, text, transitions and other effects. Measure code bytes, lookup
tables, buffer allocations and worst-frame cycles before choosing how much to
unroll; a smaller kernel's speed cost must be benchmarked rather than assumed.

Keep shared line drawing separate from the frame producer and presentation
policy. A sequence player supplies authored frames; an interactive application
could select precomputed views/poses, or eventually supply dynamically projected
vectors. Free camera/object motion would require C64-side transformation and
visibility work beyond the current host-precomputed pipeline. Input latency,
audio/logic budgets, buffering and memory ownership belong in that integration
layer. V7 now implements `--prefer fps|ram` for the Y kernels, with FPS as the
default. Broader allocation profiles and interactive 3D remain future work.

V6 implements faster partial X-major byte drawing and direct metadata
loading on the existing demo pipeline; see the [measured results](CARTRIDGE_STREAM_V6.md).
V7 adds lossless run joining, selective byte clearing and smaller Y kernels;
see its [measured tradeoffs](CARTRIDGE_STREAM_V7.md). Retaining unchanged bitmap
regions remains a follow-up experiment. Region comparisons
must use the actual picture in the recycled buffer, including resolved colours.

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
- Optional headless Blender scene evaluation through Blender's bundled `bpy`, including multiple mesh objects, evaluated stable-topology animation, active-camera projection, material colour mapping, strict authored-frame semantics, and a Blender-neutral `.c643dscene` interchange.
- Script-generated falling-cubes rigid-body Blender example.

Next:

- Optional vertex welding and duplicate cleanup.
- Degenerate face/edge cleanup.
- Topology-aware mesh simplification/decimation to a target C64 budget.
- Preserve/select sharp and silhouette-important edges during simplification.
- Cost-aware detail target: not only face count, but estimated line pixels / table RAM / renderer cycles.
- More built-ins (icosphere, pyramid, ship-like benchmark meshes).
- Near-plane clipping for Blender shots that deliberately cross the camera plane.
- Optional topology-changing Blender scene support and compressed/delta frame tables.


## Cartridge / streaming backend

The current v0.6.5 demo cart streams all twelve entries through V4 with a
fixed RAM working set. Earlier 0.6.3 groundwork provided native cartridge boot,
bank switching, cartconv integration and menu controls; 0.6.4 added the streaming
variants and HiFi assets. Version 0.6.5 fixes launching from the animated menu.

Completed streaming work includes the frame-block format, bank-contained ROM
storage, bounded staging and metadata caches, ROM copy profiling, and matched
V3/V4 measurements. Opt-in V5 adds lossless stream reduction and picture reuse;
V6 adds partial-byte drawing and direct metadata loading with matched V5/V6
measurements. The authored scene path supports long, paced finite sequences.
The current carts are in `examples/cart_demos/` and `examples/cart_marbles/`;
released older carts are preserved in `examples/old/`.

Next milestones:

- compare copy-to-RAM, direct-ROM and hybrid/cache strategies;
- explore topology sharing, frame deltas and cheap compression using measured
  cycle, ROM and RAM budgets;
- investigate SID/demo headroom and integration of authored sequences;
- verify the current cartridge and controls on physical hardware.

The detailed cartridge-specific plan lives in
[`CARTRIDGE_ROADMAP.md`](CARTRIDGE_ROADMAP.md).

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
    -> Wavefront OBJ / SVG, or evaluated Blender scene frames
    -> c64-3d-toolkit import-obj / import-svg
    -> topology diagnostics / contour simplification
    -> simplify to a C64-friendly budget
    -> preview / cost estimate
    -> vector/hidden-line compile
    -> 64tass
    -> PRG / VICE / real C64
       or EasyFlash pack -> cartconv -> CRT / VICE / cartridge
```

The CLI remains first-class even if a GUI is added.

## Host-side asset workflow additions

- Interactive/graphical OBJ/SVG preview and animation inspection while retaining a first-class CLI workflow.
- Topology-aware mesh simplification/decimation to a C64 vertex/edge/face and table-RAM budget.
- Display existing OBJ/MTL material groups and SVG contour colours in the future host preview.
- Explore optional dither/style policies for mixed-colour hires cells while preserving the current deterministic dominant-colour mode.
- SVG clipping/mask/text-layout support where it can be made deterministic and C64-budget aware.
