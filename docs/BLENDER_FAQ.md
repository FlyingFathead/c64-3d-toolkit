# Blender FAQ and troubleshooting

[Colour calibration and nearest-palette diagnostics](../examples/blender_color_calibration/README.md) · [Installation and dependency repair](INSTALLATION.md).

Practical notes from the Blender-to-C64 pipeline. Start with the
[Blender guide](BLENDER_PIPELINE.md) for setup and build commands. The current
default renderer is **HORS-V4 / GMod3**.

## Why did the picture stop before the right edge?

Older exports used a **256×192 artwork viewport** inside the C64's **320×200
bitmap**. Camera projection and host-side clipping both used the smaller
width: artwork ended at x=255, leaving x=256 through x=319 unused. The HUD
could still draw in that right-hand area because it was drawn separately.
This made a model appear cut off while the FPS counter remained visible
farther to the right.

That was a toolkit viewport limitation. Blender's output resolution or camera
framing could change the composition inside the 256-pixel area, but could not
extend the clipping boundary. Changing the model's horizontal scale or using
a flip switch does not fix this boundary either.

New v0.7.9 `.blend` exports use **320×192 by default**, with matching camera
projection and clipping through x=319. The bitmap already had storage for
those columns. The fix also splits wide clear spans into at most 32 cells:
the native clear loop uses an 8-bit index, so a single 40-cell span would wrap
before clearing the complete row. Correct drawing and correct clearing are
both necessary when animation buffers are reused.

The new [zoom and tracking test cards](../examples/blender_viewport_test/README.md)
verify upright labels, a centred target, drawing across x=255 into the last
column, all four artwork boundaries and clean loop wrap. Their screenshots
come from VICE; physical hardware testing is not claimed. A screenshot of
another old cart alone cannot prove its exact build settings, but a cutoff at
the same 256-pixel boundary is consistent with this limitation.

## What resolution should I use in Blender?

Use the active perspective camera and match the selected artwork aspect
ratio with square pixels:

| Export | Convenient Blender preview | Artwork coordinates |
| --- | --- | --- |
| New default, `--viewport-width 320` | 320×192 or 960×576 | x=0–319, y=0–191 |
| Legacy, `--viewport-width 256` | 256×192 or 768×576 | x=0–255, y=0–191 |

The full bitmap is 320×200; its bottom eight pixels are reserved for the HUD
in this scene path. Hiding the HUD does not automatically turn those rows into
additional artwork space. The old 4:3 preview advice applied to 256×192;
320×192 uses a 5:3 pixel grid. Do not stretch an old 256-pixel render to make
it appear full width: re-export the camera projection instead.

## How do I update an old scene or cart?

Rebuild from the original `.blend` so the exporter evaluates the camera for
the new width:

```bash
python c643d.py build --blend shot.blend --viewport-width 320
```

New `.c643dscene` files record their viewport width. A `--scene` build uses
that recorded width; older interchange files without it default to 256 for
compatibility. An explicit width override on an existing interchange file
changes clipping only, because its camera projection is already stored.
Re-exporting the `.blend` recalculates both together.

Existing `.crt` binaries do not change when the toolkit is upgraded. The
historical example carts and benchmark inputs retain their old framing until
rebuilt. Use `--viewport-width 256` when reproducing an old result.

## Why does the composition look off-centre?

The exporter uses Blender's evaluated active camera, including its animation
and constraints. It does not auto-fit or recenter an authored Blender scene.
Check the shot through that camera at the matching output aspect ratio,
rather than through an unrelated viewport view. An intentional camera shift
or an off-centre target remains off-centre after export.

The calibration card's centre target projects to (160,96) in the default
viewport. Its cross is an outline, so the exact centre pixel is intentionally
black; the surrounding cross pixels are symmetric. The tracking variant
moves the camera while aiming at that target and preserving the card's up
direction.

## Is the toolkit mirroring my model?

Default exports are not mirrored. The calibration card uses readable LEFT,
RIGHT, TOP and BOTTOM labels plus an arrow pointing right, so an unintended
reflection is visible immediately.

In the reported older Blender case, the model was already reversed inside
Blender before toolkit export. Once its orientation was corrected there, it
exported correctly. That report is not evidence of a toolkit mirroring bug.
Check the imported model and the active camera view first.

Optional conversion switches are available when a reflected output is wanted:

| Direction | Main option | Equivalent aliases |
| --- | --- | --- |
| Horizontal | `--flip-input-horizontal` | `--flip-horizontal`, `--mirror-horizontal` |
| Vertical | `--flip-input-vertical` | `--flip-vertical`, `--mirror-vertical` |

They reflect the projected artwork and its colours within the viewport, after
clipping. They leave HUD, intro, help and starfield orientation alone, and do
not modify the `.blend` file. Both can be enabled together. See
[input flips](INPUT_FLIPS.md) for exact semantics and examples.

## What should happen when I zoom in?

Visible geometry can cross all four artwork edges and is clipped there. The
new viewport ends at x=319 and y=191, not at the outer emulator window or
physical border. A test grid with crossing lines is useful: a rectangle's
outline alone can disappear once all its edges lie outside the camera view.

Near-plane crossings are supported in the recovery update. Edges and occluding
triangles clip before projection; geometry behind the camera disappears. Fully
invisible samples retain their position and duration, so geometry can reappear
without skipped frames. The [camera-crossing road](../examples/camera_crossing/README.md)
exercises this, including consecutive invisible samples. A single clipping
summary can be suppressed with `--ignore-warnings`.

## Does full width cost more FPS or RAM?

It can cost more rendering time because more of the scene becomes drawable.
In the uncapped 16-frame calibration zoom, PAL VICE measured **8.74 FPS at
256 pixels** and **8.09 FPS at 320 pixels**. This compares two output widths
and their resulting workloads, not an isolated fixed overhead.

No extra framebuffer or per-pixel runtime branch was added for full width.
The existing bitmap and screen memory already span 320 pixels. More visible
geometry may enlarge frame streams and increase drawing, clearing and colour
work. [The dataset README](../examples/blender_viewport_test/README.md#performance)
includes timing conditions and raw evidence.

## Where are the reproducible checks?

The [Blender viewport dataset](../examples/blender_viewport_test/README.md)
contains two editable `.blend` scenes, their generator, `.c643dscene` exports,
HORS-V3 carts, native screenshots/GIFs and verification reports. The zoom
tests width and orientation; the constrained camera shot tests tracking.
Each cart passed 51 completed-frame bitmap/colour checks across three loops
and all three buffers, including HUD preservation.

For missing animation caches, unchanged frames or material-colour problems,
see [Blender cache and colour troubleshooting](HORS_V3_DEFAULTS_CHECKPOINT.md).

## Why can red become orange?

Material numbers and their colour-space interpretation are separate inputs.
The exact diagnostic value illustrates the difference:

| Interpretation of `(152, 53, 45) / 255` | RGB passed to palette matching | C64 result |
| --- | --- | --- |
| Already sRGB, `--blender-color-space srgb` | `(152, 53, 45)` / `#98352D` | red |
| Scene-linear, default `--blender-color-space linear` | `(203, 126, 117)` / `#CB7E75` | orange |

Standard Blender materials normally need `linear`. Use `srgb` when an import
stored sRGB numbers directly in the material fields. This is explicit;
the exporter cannot reliably infer the convention from the numbers alone.
The palette and perceptual matching algorithm have not changed.

```sh
python c643d.py build --blend scene.blend --blender-color-space srgb
python c643d.py --configure-blender-color-space srgb
python c643d.py --configure-blender-color-space
```

The last command opens the chooser. `--configure`/`configure` opens the same
configuration flow. `--configure-blender-color` is a short alias. A per-build
CLI choice overrides `[render_defaults] blender_color_space` in the INI.
Explicit `c643d_color` indices override automatic material mapping in both modes.
