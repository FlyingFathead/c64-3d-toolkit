# Input artwork flips

Flipping is optional and off by default. The `build` and `cart-stream` commands accept these aliases:

| Direction | Primary spelling | Aliases |
| --- | --- | --- |
| Horizontal | `--flip-input-horizontal` | `--flip-horizontal`, `--mirror-horizontal` |
| Vertical | `--flip-input-vertical` | `--flip-vertical`, `--mirror-vertical` |

Use both directions for a 180-degree screen-space rotation. Repeating aliases for one direction enables it once; it does not cancel the flip.

These switches apply to OBJ, SVG, named objects, procedural shapes, `.blend` and `.c643dscene` conversion. They reflect the rendered artwork inside its viewport after projection/clipping and colour selection, before cartridge packing. They do not edit the source file or reflect the 3-D model's world axes. Artwork outside the clipped viewport is not recovered by flipping.

For a width W and height H, horizontal maps `x` to `W-1-x`; vertical maps `y` to `H-1-y`. Native DDA pixels are reflected exactly, including tie decisions, and fill/line cell colours follow them. SVG card occlusion bounds follow the reflected artwork. HUD labels, the intro, help, FPS/speed feedback and starfield positions/controls retain their normal orientation.

```bash
python c643d.py build --obj model.obj --flip-input-horizontal
python c643d.py build --svg logo.svg --mirror-vertical
python c643d.py build --blend shot.blend --flip-horizontal --flip-vertical
```

All reflection work occurs on the host during conversion. It adds no C64 reflection routine, runtime branches or fixed RAM buffers. Different reflected byte locations can affect compression, clearing costs and resulting throughput; identical FPS is not promised.

The native release checks cover OBJ, SVG, named preset, procedural, Blender, direct interchange and interactive builds. Each flipped geometry oracle matches the exact reflected baseline; VICE bitmap, cell-colour and HUD checks pass. Default builds remain unflipped. Sande's reported model mirroring happened in Blender before toolkit export and is not claimed as a toolkit bug fixed by these options.
