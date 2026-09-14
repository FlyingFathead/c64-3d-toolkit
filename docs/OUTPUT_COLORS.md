> Current HORS-V3 conversion, gradient and texture mapping details: [checkpoint guide](HORS_V3_DEFAULTS_CHECKPOINT.md).

HORS-V4 / GMod3 retains these V3 controls. The [All-in-One collection](../examples/gmod3_cart_demos/README.md) starts with stars off and adds F1 menu, N/P entry selection and C Dragon shading. Older EasyFlash cartridges retain their original keymaps.


# Output colours (0.7.3)

Foreground, bitmap background and border can be selected independently when
building procedural shapes, OBJ/SVG objects or authored Blender scenes. The
default remains source/preset foreground colours with black background and border.

| Option | Aliases | Meaning |
| --- | --- | --- |
| `--foreground-color` | `--color`, `--foreground-colour`, `--fg-color` | Force one foreground colour, replacing source colours |
| `--background-color` | `--background-colour`, `--bg-color` | Bitmap background, including all per-frame colour updates |
| `--border-color` | `--border-colour` | Independent VIC-II border colour |

These options work with `build` and `cart-stream`, including the resident PRG,
streamed object and authored-scene paths. `--no-color` ignores source colours;
an explicit foreground still wins. A black foreground is a valid selection.
Demo carts start with their authored presets and support the runtime controls
described below. Use `color-combo-test` for the dedicated palette showcase.

## Accepted formats

| Input kind | Examples |
| --- | --- |
| Native C64 names, case insensitive | `black`, `white`, `cyan`, `light-blue`, `"light blue"`, `light_blue` |
| Decimal palette index | `0` through `15` |
| Hex palette index | `0x0f`, `'$0f'` |
| Binary palette index | `0b1111`, `'%1111'` |
| RGB hex | `'#fff'`, `'#aaffee'` |
| RGB channels | `'rgb(170,255,238)'`, `'rgb(100%,100%,100%)'` |

The 16 native names are black, white, red, cyan, purple, green, blue, yellow,
orange, brown, light_red, dark_gray, gray, light_green, light_blue and light_gray.
`grey` spellings and compact forms such as `lightblue` are accepted.
Basic CSS names supported by the source importer are also accepted; native C64
names take precedence.

The C64 still outputs its fixed 16-colour palette. RGB values select the nearest
entry in the toolkit's palette; the build prints the resolved name and index.
`0x01` means palette index 1 (white); `'#000001'` means RGB, which maps to black.
Invalid indices, malformed RGB and transparent output colours are rejected.
Quote `#...`, `$...` and `rgb(...)` values in the shell as shown above.

The same foreground formats are accepted by `import-svg --color`, the autotuner's
`--color-index` and Blender material/object `c643d_color` properties.

## Examples

Black torus on white, with white borders:

```bash
python c643d.py build --shape torus \
  --foreground-color black --background-color white --border-color white
```

A separately selected red border around a black-on-white torus:

```bash
python c643d.py build --shape torus \
  --color '#000' --background-color '#fff' --border-color red
```

Keep an object's source colours but change its background and border:

```bash
python c643d.py build --object sunflower_torus \
  --background-color blue --border-color black
```

Resident PRG output with the same options:

```bash
python c643d.py build --renderer yunroll --shape cube \
  --fg-color yellow --bg-color blue --border-color purple
```

Optional defaults in `config/c643d.ini`:

```ini
[render_defaults]
foreground_color = auto
background_color = black
border_color = black
```

Set `foreground_color` to a colour to force monochrome by default; `auto`
preserves source/preset selection. Command-line options override these settings.

## Runtime behaviour

Hi-res bitmap screen RAM stores foreground in its high nibble and background
in its low nibble. Both the initial buffers and per-frame source-colour spans
carry the selected background, including buffers recycled by the renderer.
Monochrome inversion keeps the same vectors and bitmap bits.

`--border-color` initializes `$d020` separately; `$d021` is initialized to the
background. Authored intro colours remain part of the presentation, with the
chosen colours restored when rendering starts. The optional raster-time
profiler intentionally uses the border as a timing indicator during its work.

## Colour tester

See [COLOR COMBO TEST](../examples/color_combo_test/README.md) for the prebuilt
cartridge, four presets, controls, rebuild command and VICE verification.

## Demo Cart 1 and Demo Cart 2.0 playback controls

| Key while an animation runs | Monochrome entry | Multicolour entry |
| --- | --- | --- |
| F3 | Cycle foreground | Preserve authored palette |
| F4 / SHIFT+F3 | Cycle background | Preserve authored palette |
| F7 | Cycle independent border | Cycle independent border |
| F8 / SHIFT+F7 | Restore foreground, background and border preset | Restore border preset |

Release a key before pressing it again. Each animation restores its own preset
on entry. The border remains independent when changing a normal demo's
background. Only COLOR COMBO TEST couples those two colours.

In the menu, F1 still changes style, F4 still opens the HiFi reel and F5 still
starts exhibition mode. During playback, F1/RUN-STOP returns to the menu and
SPACE advances to the next animation.

The controls share the existing raster-IRQ keyboard scan. An added two-cycle
comparison is offset by removing a redundant two-cycle mask from the RUN/STOP
check. VICE measures 82 cycles from scanner entry through its idle/manual timer
path both before and after. No per-frame renderer hook or source-palette
remapping is added. Applying a colour after a keypress takes a one-time screen
update; the no-input playback comparisons are recorded in
`docs/benchmarks/colors/`. Source-colour foreground/background remapping is
intentionally unavailable, avoiding ongoing drawing costs.

These controls are enabled in the stable hors-render-v2 demo integrations.
Older explicit renderer implementations retain their original behaviour.
For a control-free build, use `python c643d.py cart-demos --no-color-controls`
or `python tools/build_demo_cart_v2.py --no-color-controls`.

Run the dedicated key/idle scanner verifier after rebuilding:

```bash
python tools/verify_demo_colors.py examples/cart_demos/c643d-demo-v0.7.3-hors-render-v2-all.crt \
  --vice x64sc --vice-data /usr/local/share/vice --report build/demo-colors.json
```

## Standalone interactive Sande controls (0.7.6)

The separately built `--interactive-cart` spin path uses its own controls:
F2 flashes white then resets; F3 changes foreground; F4 changes background;
F5 toggles alternating palette cycling; F6/F7 slow/speed the cycle; F8
toggles a persistent black border or background-follow mode. Ctrl+F7 cycles
a custom border. The border
follows by default. These bindings apply to the interactive standalone
carts. See [Sande controls](../examples/demos_sande/README.md#interactive-controls).
