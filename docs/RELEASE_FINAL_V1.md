# v0.7.9 release_final_v1: restore the original intro

The startup screen retains the v0.7.8 layout: toolkit name, version, renderer,
project URL and `SPACE to start`. It waits indefinitely for SPACE.
Interactive cartridges add exactly one row immediately above the start prompt:

`press SHIFT+H for help`

The keymap opens only when requested. Closing help from the intro returns to
the intro and continues waiting for SPACE. During playback, help still pauses
and restores the current presentation.

The correction applies to the shared HORS-V3 standalone builder and all 18
shipped HORS-V3 cartridges, including the SAKU, Dragon and Pretzel variants.
Historical renderers and their startup layouts remain unchanged.

The startup routine borrows bitmap RAM before video initialization clears it.
It adds no instructions to playback, drawing or the starfield IRQ and reserves
no additional RAM during playback. The intro-only rebuild was checked against the preceding v0.7.9 package
before the separately requested density and source-red adjustments below.

Native PAL VICE regression checks cold-boot every affected cartridge without
keys, wait beyond the old timeout, then exercise explicit SPACE start. The
interactive checks also open help and close it with both Shift+H and SPACE,
verifying that neither close action starts playback. Builds with stars
excluded, a hidden/fixed HUD and legacy cartridge packaging are checked too.

The version remains **v0.7.9: The Golden Dragon & SAKU 2026**.

## Additional requested refinements

- Interactive stars: 2/4/8/16/24/32 points, default 16. Shift + `+`, `-`, `0`
  changes/resets density; plain keys retain rotation speed. Eight trajectories
  carry small groups at higher settings. Extra points are occlusion-checked.
- SVG source-red gradients no longer use brown shadows. Red repeats in the
  darkest levels, followed by light red and white. Historical metallic overlays
  and the golden Dragon retain their established ramps.
- Successful EasyFlash conversion prints a terminal-width summary with the
  absolute CRT path, occupied ROM, free ROM and ROML/ROMH free-slot breakdown.
  Figures count allocated 8 KiB ROM slots, excluding CRT container headers;
  they are not a count of nonzero bytes or an estimate from the ZIP size.

See the current [performance comparison](PERFORMANCE_COMPARISON.md) for measured
density, starfield on/off, HUD and speed results. `--no-starfield` excludes
the density module as well as the effect; help and speed remain available.

After cartridge creation, the build prints:

```text
--------------------------------------------------------------------------------
Created: /path/to/example.crt
ROM used: <allocated bytes> (<KiB>)
Free ROM available on cart: <unallocated bytes> (<KiB>)
Free slots: ROML <KiB>; ROMH <KiB>
Allocation: 8 KiB ROM slots; free slots may be on either ROML or ROMH.
--------------------------------------------------------------------------------
```

Separator width follows the terminal (80 columns when unavailable). Free ROMH
is not interchangeable with ROML frame-stream capacity.

Validation: 262 unit tests, three expected skips; all 18 shipped V3 carts
cold-boot checked for indefinite SPACE wait and original layout. SAKU's full
240-picture, keyboard, help, HUD, speed, density, occlusion and GIF checks pass.
Density costs on the default SAKU rotation: 18.25 FPS off, 15.71 at eight points,
14.77 at sixteen and 13.57 at thirty-two. These are stock PAL VICE results.
