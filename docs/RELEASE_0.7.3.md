# c64-3d-toolkit 0.7.3

Final release: 2026-09-10, following user acceptance of the delivered build.
The final archive retains the tested renderer implementation and cartridge bytes.
Windows setup r25 additionally requires consent before installing VICE and
explains how to select an existing copy or install it later. This installer
update does not change cartridge startup or drawing code.

## Changes

- Independent foreground, background and border selection for object and scene
  builds. `--color` remains compatible; `--foreground-color` is its clearer alias.
- Shared colour parsing accepts C64 names, decimal/hex/binary palette indices,
  RGB hex and `rgb(...)`. RGB values map to the nearest fixed C64 palette entry
  during compilation. Optional configuration defaults use the same formats.
- Selected backgrounds persist through source-colour updates and all three
  screen buffers. Monochrome inversion works, including black foreground.
- Runtime colour keys in both Demo Cart 1 preferences and Demo Cart 2.0.
- A separate **COLOR COMBO TEST** cartridge automatically loops four classic
  animations, ten seconds per entry, with matching background and border.

See [output colours](OUTPUT_COLORS.md) for the complete syntax and examples.
The default renderer remains `hors-render-v2`.

## Playback controls

| Key | Demo Cart 1 and Demo Cart 2.0 | COLOR COMBO TEST |
| --- | --- | --- |
| F3 | Cycle monochrome foreground | Cycle foreground |
| F4 (Shift+F3) | Cycle monochrome background | Cycle background and border together |
| F7 | Cycle border independently on every entry | No colour binding |
| F8 (Shift+F7) | Restore the entry's colour preset | No colour binding |
| SPACE | Next entry in PLAY ALL | Next entry |
| F1 | Return to menu | Return to menu |

Multicolour entries preserve their authored graphics palette and support border
cycling/reset. The menu's F4 HiFi shortcut and F5 exhibition mode remain available.
Each colour key acts once until released; either shift key works.

| Test animation | Foreground | Background and border |
| --- | --- | --- |
| TORUS | Black | White |
| TORUS DENSE | Cyan | Blue |
| SPHERE | Light green | Black |
| CUBE | White | Purple |

## Install the supplied release

Download `c64-3d-toolkit-v0.7.3-final.zip` and its `.sha256` file into
`~/c64-work/`, then run:

```bash
cd ~/c64-work/
sha256sum -c c64-3d-toolkit-v0.7.3-final.zip.sha256
unzip -o c64-3d-toolkit-v0.7.3-final.zip
cd c64-3d-toolkit/
cat VERSION
```

`VERSION` should print `0.7.3`. The archive includes the top-level
`c64-3d-toolkit/` directory, so extract it from its parent as shown. This updates
the existing checkout. No rebuild or cleanup is required to use these carts.

Current outputs:

- `examples/cart_demos/c643d-demo-v0.7.3-hors-render-v2-all.crt`
- `examples/cart_demos/c643d-demo-v0.7.3-hors-render-v2-all-ram.crt`
- `examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt`
- `examples/color_combo_test/color-combo-test.crt`

Other examples retain their tested 0.7.2 bytes and build identities. The two
0.7.2 Demo Cart 1 cartridges are also retained as regression references; launch
the 0.7.3 filenames above for the new controls. The cartridge inventory and
hashes are recorded in [examples/release-index.json](../examples/release-index.json).

## Validation

No idle playback slowdown was measured in PAL VICE 3.10. Across both Demo Cart 1
preferences and Demo Cart 2.0, all 93 old/new ten-second observation windows
have identical raw timing records, including render cycles and display intervals.
The idle IRQ keyboard scan remains **82 cycles**. An actual colour keypress
performs a one-time update; the idle comparison excludes keypresses.

- 2,897 completed pictures per build matched the old/new references; all three
  menu styles passed.
- 416 demo colour-key/hold checks passed. COLOR COMBO TEST passed 260 picture
  checks, two automatic rounds and 96 keyboard checks.
- Independent foreground/background/border builds passed, including source
  colours across all three screen buffers.
- 199 Python tests ran: 196 passed and three optional historical-archive tests
  were skipped because their external archives were absent.
- All 26 canonical renderer comparison jobs passed; the source fingerprint
  matches the packaged implementation.

See [detailed validation](COLORS_0.7.3_VALIDATION.md) and
[raw evidence](benchmarks/colors/). These timing measurements cover PAL emulation;
they do not establish physical-hardware or NTSC timing.

## Rebuild and validate

The shipped package is ready to run. For a fresh, isolated full rebuild:

```bash
cd ~/c64-work/c64-3d-toolkit/
JOBS=3 VICE_DATA=/usr/local/share/vice bash COMPILE-RELEASE.sh \
  --workspace ../c64-073-release-build
```

Choose a new workspace for each run. The pipeline builds the examples, verifies
pictures, menus, endings, colour controls and version labels, runs the full
comparison matrix, and packages the result. Logs and evidence stay in that
workspace. `--install` copies the validated result into the checkout after the
checks pass. `--baseline-zip PATH` additionally produces an overlay.

The compiler's generated `c64-3d-toolkit-0.7.3-hors-v2-complete.zip` and optional
overlay use repository-relative paths. To manually install that generated ZIP,
use `unzip -o PATH_TO_GENERATED_ZIP -d ~/c64-work/c64-3d-toolkit/`.
The supplied `c64-3d-toolkit-v0.7.3-final.zip` uses the parent-directory extraction
command in the installation section above.

Root `VERSION` supplies Python, Windows setup and generated cartridge identity.
The build commands do not commit, tag or push Git.
