# CLI options and defaults

CLI startup automatically archives a stale root `monitor.log` into ignored
`logs/` using a unique timestamp. Run `python3 tools/maintenance.py` manually,
or add `--untrack-monitor-logs` to archive and untrack old generated monitor
logs before releasing. See [monitor log maintenance](MAINTENANCE.md).

`python c643d.py --help` prints the command list **and every build option**.
`python c643d.py build --help` prints build options alone.
`python c643d.py --help-all` prints every command's options. For one command,
use `python c643d.py COMMAND --help`. Help is generated from the actual parser
and remains available without NumPy, Pillow or the external toolchain.

| Choice | Default | Explicit selection |
| --- | --- | --- |
| Renderer | HORS-V4 | `--renderer hors-v4` (long aliases still work) |
| Cartridge | GMod3 for HORS-V4, unless overridden by config | `--cart-type gmod3` or `--cart-type easyflash` |
| Playback | Non-interactive automatic playback | `--interactive-cart` for supported object/SVG spins |
| Stars in interactive builds | Disabled | `--starfield-default enabled`; `--no-starfield` excludes them |
| HUD | Visible | `--hide-hud`; interactive Shift+I/F/U toggles it |
| Object surfaces | Wireframe | `--surface-fill metallic`, material or texture options listed in help |
| Blender material interpretation | `linear` | `--blender-color-space srgb` for raw sRGB imports |
| Scene/export warnings | One clipping summary plus exporter diagnostics | `--ignore-warnings` |
| Blender drawing width | 320 pixels | `--viewport-width 256` for legacy framing |

Authored `--blend` and `--scene` animations play their exported timeline
and do not support `--interactive-cart`. The supplied All-in-One collection
explicitly adds its shared interactive player to frozen example pictures.
[Its baseline and full keys](INTERACTIVE_CART_BASELINE.md) are separate from
normal automatic Blender builds.

```sh
python c643d.py build --blend scene.blend --frame-start 1 --frame-end 120 --sample-step 1
python c643d.py build --shape torus --interactive-cart --starfield-default disabled
python c643d.py build --object horse_head --renderer hors-v4-ef
python c643d.py dependencies
python c643d.py --configure-blender-color-space srgb
python c643d.py --configure-blender-color-space
```

The build help covers input sources, topology, frame sampling, cameras,
framing/flips, visibility, surfaces/textures/gradients, palette overrides,
HUD/stars/exhibition, pacing, rendering, cartridge capacity, profiling and
external tool configuration. Flags can also be passed without the `build`
word for compatibility. `cart-stream` is a build alias; `cartridge-demo` is a
`cart-demos` alias. The legacy `cart-demos` command still builds its historical
EasyFlash comparison collection; use `examples/gmod3_cart_demos/build.py`
for Demo Cart v3.1.

[Installation and repair](INSTALLATION.md) · [Configuration](CONFIGURATION.md) ·
[Blender](BLENDER_PIPELINE.md) · [SVG](SVG_PIPELINE.md) · [Colours](../examples/blender_color_calibration/README.md)

Help includes the toolkit version and author. Configuration commands do not
require Blender or Python build dependencies. See [the colour chooser and
INI precedence](CONFIGURATION.md#blender-material-colour-interpretation).
