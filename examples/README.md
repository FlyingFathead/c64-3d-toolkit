# Examples

Ready-to-run cartridges, Blender scenes, and generated/reference PRGs are grouped by demo.

## Cartridge demos

| Example | Contents | Renderer |
|---|---|---|
| [Twelve-demo menu cartridge](cart_demos/README.md) | Preserved v0.6.5 menu cart, scrolling menus and three menu styles; includes the HiFi horse and sunflower | `yunroll-cart-v4` throughout |
| [Don't Lose Your Marbles](cart_marbles/README.md) | v0.6.6 early beta: intro, collisions, fracture/star field, credits and BASIC epilogue; HUD and clean CRTs | Separate `yunroll-cart-v4-scene` extension |
| [HiFi showcase cartridges](hifi_showcase/README.md) | Separate 192-orientation horse and sunflower CRTs, captures and reports | `yunroll-cart-v2` |

Launch the current menu cart from the project root:

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt
```

Or launch the new standalone scene:

```bash
x64sc -cartcrt examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene.crt
```

Use the `-clean.crt` variant in the same folder for the intro and scene without
the title/FPS HUD. Older comparison carts and reports are preserved under
`old/cart_demos/`. Cartridge builds are separate from the standard PRG
`test-examples` matrix below.

## Example folders

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
  blender_marbles/
  cart_demos/
  cart_marbles/
  hifi_showcase/
  old/cart_demos/
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

## Orbiting cubes-and-marbles Blender example

[`blender_marbles/`](blender_marbles/README.md) contains a separate 40-second
source scene: 45 falling objects across six alternating pours, a full camera
orbit, and a 32-piece tabletop fracture that drifts into a constellation.
The live rigid-body source, baked animation and deterministic generator ship together.

The standalone early-beta cartridge plays once, including its native intro,
typing joke, credits and staged BASIC reboot. See the
[V4 scene-streaming guide](../docs/CARTRIDGE_SCENES.md) for measured duration,
build commands, HUD/clean options, memory limits and validation.
The original falling-cubes assets and twelve-demo menu cartridge are unchanged.

## Upgrading an older checkout

An overlay ZIP cannot delete the old flat files by itself. Preview and apply the safe migration once:

```bash
python tools/migrate_examples_layout.py
python tools/migrate_examples_layout.py --apply
```

Existing destination files are never overwritten when their contents differ.

## Streamed HiFi cartridges

[`hifi_showcase/`](hifi_showcase/README.md) contains separate horse and sunflower EasyFlash CRTs, each with 192 orientations. These use the independent `yunroll-cart-v2` frame streamer, with matching OBJ/MTL assets, VICE captures and validation reports.

## Archived Marbles concept

The [early concept tryout](old/cart_marbles/early-test-v0.6.5/README.md) preserves
the earlier looping carts and baked Blender scene under the existing `old/` tree.
