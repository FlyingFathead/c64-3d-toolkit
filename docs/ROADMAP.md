# Roadmap

## Renderer / performance

- Cycle-profile `yunroll` hot paths in the VICE monitor.
- Explore self-modified absolute bitmap accesses where they beat `(zp),Y`.
- V7 implements generator-selected cell/byte clearing; explore finer plans when decoding cost justifies them.
- Extend the existing comparison and stage-profile tools with better cost estimates.
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
layer. `--prefer fps|ram` selects Y kernels in V7 through hors-render-v1, with
FPS as the default. Broader allocation profiles and interactive 3D remain future work.

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

The current v0.7.1 menu streams all twelve entries through hors-render-v1,
using fixed RAM buffers and metadata caches. V2–V7 established banking,
staging, lossless vector optimizations and authored sequences. V8 added sparse
byte-span pictures, V9 direct-ROM byte drawing, and hors-render-v1 prefers byte
encoding whenever it fits the frame arena. The renderer comparison and stage
profilers are implemented; see [the matched chart](PERFORMANCE_COMPARISON.md).

Current examples include the menu, standalone objects, Horse/Sunflower and the
accepted 640-sample Marbles presentation. Superseded generated outputs belong
in `../c64-3d-toolkit-history/`, outside the checkout. Renderer sources remain.

Next milestones:

- build on measured direct-ROM results to evaluate further hybrid/cache strategies;
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

## Larger cartridge targets and measured encoding selection

- Preserve EasyFlash as the existing 1 MiB target; this is not a universal C64 capacity limit.
- Prototype independent GMod3 and GMod4 backends. GMod3 is documented by VICE and can serve as an emulator-first experiment; GMod4 is the successor hardware target, subject to confirming the exact emulator/hardware revision available for validation.
- Keep cartridge hardware selection separate from renderer/encoding policy. Proposed hardware options are not implemented CLI switches yet.
- Add explicit ROM budgets and reports for useful payload, bank allocation, padding, reserved space and runtime RAM.
- Use the byte-policy measurements toward `hors-optimizer-v1`: choose verified speed/space tradeoffs without changing source pictures or historical renderers.
- Require boot, bank-boundary, pixel, IRQ/return and normal PLAY ALL tests before declaring a backend supported. Validate physical hardware separately from emulator results.

See [capacity limits](CARTRIDGE_CAPACITY.md) and the [larger-backend implementation plan](GMOD_BACKENDS.md).

### GMod validation order

- [ ] GMod3: minimal boot and exhaustive bank-read probe using the supplied VICE toolchain, then an independent streaming backend.
- [ ] GMod4: audit and build the manufacturer VICE patch for the 2026 register layout, test ordinary banking first, then an independent streaming backend.
- [ ] Preserve the existing EasyFlash benchmark environment and all historical implementations; record emulator-only versus physical-hardware validation separately.

## hors-render-v1 status

hors-render-v1 byte-first EasyFlash builds are integrated in 0.7.1. Dense 25/20 FPS exports and recovery runs exposed capacity/timing limits; the 640-sample, 16 FPS Marbles compromise is accepted. Next: improve packing and worst-frame cost, resolve general timing selection, then test music coexistence. Automatic mixed-renderer selection remains planned. GMod3/GMod4 remain separate backend work; see [GMod details](GMOD_BACKENDS.md).
