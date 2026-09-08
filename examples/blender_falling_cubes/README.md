⚠️🐴 Attention! For best quality, please enjoy each animation with `hors-render-v1` or a newer variant.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

# Blender Falling Cubes — hors-render-v1

Start with the supplied hors-render-v1 cartridge:

```bash
x64sc +easyflashcrtwrite -cartcrt examples/blender_falling_cubes/falling_cubes_c64_color-hors-render-v1.crt
x64sc +easyflashcrtwrite -cartcrt examples/blender_falling_cubes/falling_cubes_c64-hors-render-v1.crt
```

The PRG variants remain available for comparison. Rebuild current cartridges with
`python tools/build_current_examples.py` from the repository root.

Falling cubes uses the 18 preserved vector samples from the menu reference.
This is the existing short loop, not a new Blender physics render.
