# Examples

Generated/reference PRGs are grouped by logical demo so the examples tree does not become a flat pile of binaries.

```text
examples/
  cube/
  torus/
  torus_dense/
  sphere/
  horse_head/
  sunflower_torus/
  space_horse_spin/
  space_horse_crawl/
  blender_falling_cubes/
  examples.json
  README.md
```

For normal non-Blender examples, the standard regression lanes are:

- `name.prg` - current 256x192 overlay/HUD build.
- `name_legacy144.prg` - 256x144 performance/reference build. Historical files are retained byte-for-byte where available.
- `name_no_overlay.prg` - separate no-overlay ASM using the full 256x200 bitmap height.
- `name_rastertime_profiler.prg` - separate yunroll debug ASM, 256x192.

Run the complete standard matrix:

```bash
./build.sh test-examples
```

Build only one viewport lane when comparing performance:

```bash
./build.sh test-examples --variants normal
./build.sh test-examples --variants legacy144
```

Regenerate checked-in standard example PRGs deliberately with:

```bash
./build.sh generate-examples
```

## Blender falling-cubes example

Blender sources and generated PRGs live together under `examples/blender_falling_cubes/`.

- `falling_cubes_c64.py` generates the smaller six-cube rigid-body scene intended for C64 compilation.
- `falling_cubes_full.py` / `.blend` are the 40-cube authoring/stress scene and can exceed C64 frame/table limits.
- `falling_cubes_c64_color-yunroll_legacy144.prg` preserves the original 256x144, sample-step-3, 24-sample colour build.
- Current 192/200-line falling-cubes builds use sample-step 4 (18 stored samples) to stay inside C64 table RAM.

Generate the scene:

```bash
blender --background --python examples/blender_falling_cubes/falling_cubes_c64.py
```

Compile it directly:

```bash
./build.sh --blend examples/blender_falling_cubes/falling_cubes_c64.blend \
  --frame-start 1 --frame-end 72 --sample-step 4 --run
```

Blender regression builds are intentionally separate because Blender is optional:

```bash
./build.sh test-examples --blender-only
```

The Blender-only matrix contains the authored-colour and forced-monochrome current 192/200/debug variants, plus the historical colour `_legacy144` build. Use `generate-examples --blender-only` only when intentionally refreshing those PRGs.

Assembler labels/listings remain transient under `build/`.

The old duplicate `space_horse_spin.prg` and `space_horse_crawl.prg` aliases are retained in the historical checksum database but are no longer shipped as duplicate files; the explicit `_color` / `_legacy144` names identify the maintained outputs.

## Upgrading an older checkout

An overlay ZIP cannot delete the old flat files by itself. Preview and apply the safe migration once:

```bash
python tools/migrate_examples_layout.py
python tools/migrate_examples_layout.py --apply
```

Existing destination files are never overwritten when their contents differ.
