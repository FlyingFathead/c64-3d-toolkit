# v0.7.9: The Golden Dragon & SAKU 2026

HORS-V3 is now the default for `build`, `cart-stream` and their `build.sh`
shortcuts, covering objects and authored Blender wireframe animations.
Filled material, image-texture and metallic surfaces remain selectable modes.

## Changes

- **Exhibition and paged help.** Shared HORS-V3 interactive help has left/right pages; 5 toggles exhibition, 6 selects sequential/random, 7/8 changes the 5–60 second interval. Entry hides HUD/stars; manual star choices survive scene changes. CLI startup/order/interval switches are documented in [EXHIBITION.md](EXHIBITION.md).

- **SVG paint by default.** Proportional fit, mapped fills and strokes, preserved
  holes and painted canvas. `--fill-style gradient` adds the Dragon-style hue
  ramps. `--svg-outlines-only`, `--svg-no-colors`, and
  `--svg-override-with-color COLOR` provide explicit reductions and overrides. `--include-svg-background-color true|false` controls exported canvas rectangles.
- **SAKU 2026.** Original PDF vectors, a cropped transparent SVG, solid and
  gradient carts, original white-card and transparent white-outline SVG references, plus eight spin/crawl presentations on one interactive cart,
  a RAM-resident forward starfield, and a complete keyboard map.
- **Interactive tempo.** `+`, `-`, and `0` skip orientations, add slower holds,
  and reset speed. Brief `SPD.*` feedback includes `WOW!` and white/red maximum
  feedback. These controls are shared by future HORS-V3 interactive builds.
- **Interactive help and optional stars.** The original intro waits for SPACE and includes a separate Shift+H help hint;
  RUN/STOP (Esc in VICE) or Shift+H help pauses playback without altering the buffered pictures. Ordinary
  interactive carts include stars disabled; `--starfield-default enabled`
  overrides that default. `--no-starfield` / `--no-include-starfield` omits
  the starfield routine and data. SAKU explicitly starts with stars enabled.
- **HUD visibility.** `--show-hud` / `--hide-hud` reuse the text-overlay options.
  `--hud-default enabled|disabled` (alias `--default-info-text-mode`) sets startup
  visibility. Shift+I, Shift+F and Shift+U toggle name/counts, FPS/speed feedback,
  or all HUD text including INTERACTIVE. Runtime toggles are included in V3 interactive carts;
  `--no-hud-toggle` omits them.
- **Star density.** `1` / `2` / `3` resets, increases or decreases 2/4/8/16/24/32 star
  points. SAKU starts with the light eight-point field; key 4 selects the full field (16-point default). Ordinary carts still start with the
  effect disabled. SVG red gradients now keep red shadows instead of brown.
- **Cartridge capacity summary.** Every EasyFlash conversion prints the created
  path, allocated/free ROM and ROML/ROMH free slots at terminal width.
- **The Golden Dragon.** The golden Stanford Dragon cart and timed GIF join
  the original five looks. Main-page GIFs pair it with SAKU; the earlier
  Stanford Dragon and Sande's Pretzel announcements remain.

- **All colour families and custom gradients.** Add cyan, purple, yellow,
  orange, brown, light shades and neutral ramps. `--surface-ramp` accepts
  2..16 ordered colour stops. The original grey/red/green/blue ramps retain
  their exact output.
- **Consistent nearest-colour reduction.** Materials and texture pixels use
  the existing perceptual C64 palette mapper. The final two-colour-per-8x8-cell
  reduction now uses that same metric; `--surface-color-metric rgb` retains
  the previous cell reduction. Builds report source material mappings and
  texture colour histograms.
- **Authored-scene V3 integration.** The shared colour plan works with paced,
  paged scene playback. Fragmented clear/address metadata can be compacted
  without discarding pixels, geometry or animation samples.
- **Actionable metadata errors.** V2 failures identify the sample and actual
  clear/colour span counts. The one-byte span limit is per frame, independent
  of animation duration.
- **Blender cache and colour fixes.** Diagnose missing external caches,
  disabled cache modifiers and Blender builds without Alembic. Unlinked
  Principled Base Color and scene-linear RGB are handled before palette mapping.

The comparison/menu builder retains V2. Earlier explicit renderer choices
remain available. Filled/textured Blender scenes are not implemented; the
surface rasterizer supports standalone spin/recede/crawl animations. Hires output still permits
only two colours per 8x8 cell.

## CLI

```bash
python c643d.py build --svg artwork.svg
python c643d.py build --svg artwork.svg --fill-style gradient
python c643d.py build --svg artwork.svg --svg-outlines-only
python c643d.py build --svg artwork.svg --svg-no-colors
python c643d.py build --svg artwork.svg --svg-override-with-color cyan
python c643d.py build --svg artwork.svg --fill-style gradient --interactive-cart \
  --background-effect starfield-forward
python c643d.py build --obj model.obj --surface-fill textured
python c643d.py build --obj model.obj --surface-fill metallic --surface-palette purple
python c643d.py build --obj model.obj --surface-fill metallic \
  --surface-ramp brown,orange,yellow,white --frames 128 --run
python c643d.py build --blend animation.blend --frame-ticks 2 --run
```

Native names, palette indices and quoted RGB hex values work as custom stops.
`--surface-fill material` uses plain MTL Kd colours. The detailed
[guide and palette chart](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.9/docs/HORS_V3_DEFAULTS_CHECKPOINT.md) explain the modes,
cache requirements and the investigation of the reported conversion error.

[SAKU official home page](https://suomenamigakayttajat.fi/) ·
[Saku magazine](https://sakulehti.fi/)

## Validation

The release process rebuilds the version-labelled examples and runs the unit
suite, PAL VICE bitmap/colour checks, the complete historical renderer
comparison, the 11 HORS-V3 workloads, the six Stanford Dragon looks (including golden), and the SAKU SVG presentations.
The new V3 regression gate covers a 180-frame deforming scene, texture and
custom/indexed gradients, 384-span fragmentation and interactive controls.

[Release validation](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.9/docs/benchmarks/release-0.7.9/validation.json) records the
completed gates; [performance comparison](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.7.9/docs/PERFORMANCE_COMPARISON.md) includes
fresh evidence. Native MDD was additionally tested with Blender 4.0.2 in the
preceding checkpoint. Its Alembic round trip was skipped because the supplied
Blender binary was compiled without Alembic support. Sande's original project,
physical C64 hardware and NTSC were not tested.

## Install

The incremental ZIP includes all changes since the supplied 0.7.8 snapshot,
including the earlier V3 checkpoint. Extract it from the parent of the checkout.
The full release ZIP also extracts into `c64-3d-toolkit/`.

```bash
unzip -o c64-3d-toolkit-v0.7.9-incremental-release_final_v5.zip
cd c64-3d-toolkit
python c643d.py --version
python examples/stanford_dragon/verify.py --check
python tools/run_hors_v3_perfs.py --check
python tools/compare_renderers.py --check
```

[Final revision: restored intro, density and red-shadow correction](RELEASE_FINAL_V1.md).

[Latest correction: light startup, RUN/STOP help and persistent star-off state](RELEASE_FINAL_V4.md).

## Final v5 additions

The [final v5 notes](RELEASE_FINAL_V5.md) include paged interactive help and exhibition controls, full-width 320×192 Blender export, editable zoom/tracking calibration scenes, and optional horizontal/vertical artwork flips. See the [Blender FAQ](BLENDER_FAQ.md) for the old right-edge cutoff and rebuilding instructions.

[Release-check correction](RELEASE_MEDIA_FIX.md): promotional videos stay in
`assets/` and no longer invalidate renderer benchmark provenance. Keep the
README-linked showreel in the committed release.
