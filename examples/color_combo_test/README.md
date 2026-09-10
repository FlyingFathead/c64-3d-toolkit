# COLOR COMBO TEST

[Run the prebuilt cartridge](color-combo-test.crt), built with hors-render-v2.
A short title screen leads into automatic playback: ten PAL seconds per entry,
then repeat without a closing-screen intermission. SPACE can skip the title.

| Animation | Foreground | Background | Border |
| --- | --- | --- | --- |
| torus | black | white | white |
| dense torus | cyan | blue | blue |
| sphere | light_green | black | black |
| cube | white | purple | purple |

These use the preserved classic geometry, orientations and sample counts.

VICE framebuffer previews: [inverted torus](previews/combo-1.png),
[dense torus](previews/combo-2.png), [sphere](previews/combo-3.png),
[cube](previews/combo-4.png).

| Key during animation | Action |
| --- | --- |
| F3 | Cycle foreground through all 16 colours |
| F4 (SHIFT+F3 on C64) | Cycle background and matching border through all 16 colours |
| SPACE | Next animation |
| F1 | Return to the menu |

Holding a colour key does not repeat; release it before the next press.
Both shift keys work. Each new animation restores its preset. Foreground and
background may become identical while experimenting, making the object disappear;
press a colour key again to make it visible.

Only this test cartridge couples the border to the background. Ordinary builds
accept an independent `--border-color`; see [Output colours](../../docs/OUTPUT_COLORS.md).

```bash
x64sc +VICIIfull +easyflashcrtwrite -cartcrt examples/color_combo_test/color-combo-test.crt
```

Rebuild from the repository root:

```bash
python c643d.py color-combo-test
# Optional duration, 1..255 PAL seconds per entry:
python c643d.py color-combo-test --play-all-seconds 10
```

The builder also accepts `--output`, `--output-dir`, `--prefer fps|ram`, toolchain
options and `--run`. Defaults use `examples/color_combo_test/` and FPS preference.

After rebuilding, verify every animation's bitmap, colours and border, two
automatic rounds, wrapping, both shift keys, key-release handling, three screen
buffers, preset restoration, SPACE skip and F1 exit:

```bash
python tools/verify_color_combos.py examples/color_combo_test/color-combo-test.crt \
  --vice x64sc --vice-data /usr/local/share/vice \
  --report build/color-combo-validation.json
```

The verifier uses real PAL VICE emulation. Keyboard tests inject sampled keyboard
row values at the scanner, so they verify C64 handling rather than host keymap
configuration. Recorded verification is in `docs/benchmarks/colors/`.
