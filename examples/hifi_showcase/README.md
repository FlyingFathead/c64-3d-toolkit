# HiFi horse and sunflower: streamed cartridge showcase

Two new title-art-inspired meshes, their OBJ/MTL/JSON presets, and independent
EasyFlash demos. The original horse and sunflower assets remain unchanged.

The optional `*-yunroll-cart-v3.crt` versions render these same models at about
8.03 FPS (horse) and 5.55 FPS (sunflower), versus the V2 measurements below.
See [the V3 guide](../../docs/CARTRIDGE_STREAM_V3.md) for commands, comparison
results and the separate V3 menu cartridge.

| Demo | Vertices | Edges | Faces | Orientations | PAL VICE FPS |
|---|---:|---:|---:|---:|---:|
| horse_head_hifi | 135 | 299 | 178 | 192 | 7.20 |
| sunflower_torus_hifi | 243 | 443 | 238 | 192 | 4.91 |

The horse has a broad faceted bust, sloping nose bridge, pointed ears, and small
raised eye/nostril details. Purple, blue, light-blue and cyan materials follow
the reference's colour direction. The sunflower has a torus centre, 16 cupped
petals with individual bends, a curved stem and two leaves. Petals are yellow
on both sides. The central torus has a brown front/inner rim and green backing;
the stem and leaves stay green.

These are interpretations of the title graphic, not traced flat silhouettes.
They rotate as actual 3D meshes. Both have closed manifold components with
surface-depth hidden-line removal: rear wires are hidden by solid surfaces.
Attachment components intentionally intersect; these are visual demo models,
not boolean-unioned fabrication meshes. The sunflower's cupped petals have
single polygon backs to avoid unnecessary backside wire detail.

MTL `Kd` values map to native C64 colours. `Ka`, `Ks`, `Ns`, and `illum` also make
the files usable in shaded desktop viewers. The C64 uses static wire colours,
not filled polygons or runtime lighting. Hires colour is resolved per 8x8 cell,
so mixed-colour edges in one cell take the dominant visible colour.

## Run

From the repository root:

```bash
x64sc -cartcrt examples/hifi_showcase/horse_head_hifi-yunroll-cart-v2.crt
x64sc -cartcrt examples/hifi_showcase/sunflower_torus_hifi-yunroll-cart-v2.crt
```

Each CRT starts its own animation directly. The current 0.6.5 menu cartridge
also includes both new demos at 128 orientations, alongside all ten originals.
Run `x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt`.

## Rebuild

```bash
./build.sh cart-stream --object horse_head_hifi --frames 192 \
  --output-dir examples/hifi_showcase
./build.sh cart-stream --object sunflower_torus_hifi --frames 192 \
  --output-dir examples/hifi_showcase
```

192 orientations means small angular steps, not 192 FPS. A complete rotation
lasts about 27 seconds for the horse and 39 seconds for the sunflower at the
measured throughput. The cartridge holds approximately 221 KB and 371 KB of
frame data respectively; each directory takes 1,344 RAM bytes. More detailed
visible geometry still costs rasterisation time.

Only regenerating the authored meshes requires NumPy/SciPy:

```bash
python3 tools/generate_hifi_assets.py
```

Normal OBJ import and cartridge builds use the existing standard-library host
pipeline. To make a quick host-rendered turntable preview (Pillow required):

```bash
python3 tools/preview_hifi.py
```

`*_preview.png`, `*_views.png` and `*_turntable.gif` are host compiler previews.
`*-vice.png` and `*-vice.gif` are captured from actual VICE bitmap/screen RAM,
including HUD; the GIF uses measured emulated frame timing. They are not
analogue-filtered emulator screenshots.

## Verification evidence

Both supplied cartridges passed 387 consecutive frame comparisons in VICE 3.10
(two rotations plus wraparound), all three slots, with exact bitmap and colour
matches: 2,972,160 bitmap bytes and 371,520 screen bytes checked per cartridge.
The sunflower reaches 351 visible runs in a frame, exercising V2's widened
counter. Timing and detailed results are in `*-validation.json`; frame layout,
bank locations and checksums are in `*-manifest.json`.

The bundled tool archive was SHA-256 verified. The build used its 64tass
1.59.3120, cartconv and VICE 3.10. VICE ran in console mode with the package's
shared libraries and ROM data. Physical hardware has not been tested.

See [the streaming design and limits](../../docs/CARTRIDGE_STREAM_V2.md).
