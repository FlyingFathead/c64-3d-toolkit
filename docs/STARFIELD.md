# Forward starfield and interactive controls

HORS-V4 / GMod3 retains these V3 controls. The [All-in-One collection](../examples/gmod3_cart_demos/README.md) starts with stars off and adds F1 menu, N/P entry selection and C Dragon shading. Older EasyFlash cartridges retain their original keymaps.


```bash
python c643d.py build --svg logo.svg --fill-style gradient \
  --background-effect starfield-forward --interactive-cart
```

`starfield` is an alias for `starfield-forward`. Interactive builds include the
routine but start with stars disabled, unless `--starfield-default enabled`
selects the opposite startup state. `--starfield-default disabled` forces them
off initially; `true` and `false` are accepted aliases. This explicit default
overrides the startup state selected by `--background-effect`.
`--no-starfield` (alias `--no-include-starfield`) removes the routine, IRQ call,
trajectories, sprite setup and Shift+S binding entirely. Combining exclusion
with an enabled default is an error. Noninteractive builds include stars only
when explicitly enabled. Help and speed controls remain available when excluded.
The [SAKU 2026 interactive example](../examples/saku_2026/README.md)
starts with stars and source-colour gradients, and has eight presentations on one
cartridge. **Shift+S** toggles stars. Their motion stays independent of logo
rotation, direction, speed and perspective crawl. **4** switches the original
light field and the fuller field. SAKU starts with the light field enabled.
`--starfield-profile light|full` selects the initial and F2-reset profile;
ordinary interactive builds use full when no profile is selected, with stars
still disabled unless enabled explicitly. Profile selection requires an interactive
build with included stars. Each field remembers its density.
Switching preserves the on/off state, so it does not turn disabled stars back on.

## Runtime implementation

Eight hardware sprites follow precomputed perspective trajectories. Their
outward acceleration and increasing brightness simulate travel toward the
viewer. Tables advance from the raster IRQ, once per PAL refresh, and use unequal 43–64-refresh lifetimes in interactive builds.
Irregularly spaced directions and staggered lifetimes soften the eight-spoke
formation; stars become two pixels wide during the final quarter of each flight.
The wider pattern uses 64 extra bytes per VIC bank (192 bytes total), changed only
on density key events. Pointer selection happens once per star in the existing IRQ.
Both pixels are checked for occlusion. Automatic builds retain their 64-sample paths. The runtime performs no division or 3D star projection.
The full field defaults to **16 star points**. **`1` / `2` / `3`**
resets, increases or decreases density through **2, 4, 8, 16, 24, 32** points.
Plain `+` / `-` / `0` still controls rotation speed. Below eight points, fewer
sprites are active; above eight, each sprite contains two to four spaced dots.
These are small groups sharing eight trajectories, not independent particle
paths or a sprite multiplexer. Occlusion can reduce the visible count.
The light field uses the original 64-sample trajectories and one-pixel stars,
with **2, 4, 8** points and **8** as its reset/default. It skips the extra-dot
and near-width checks. Both fields retain foreground/opaque-logo protection.
Noninteractive starfields keep eight single-point sprites.

Changing density rewrites the two 63-byte sprite patterns in all three VIC banks
only on a key event. Every extra point gets the same cell/opaque-mask checks;
if any point is unsafe, the whole group is suppressed. More points therefore
cost additional IRQ work, even though eight hardware sprites remain the limit.
The density scanner reads two keyboard rows inside the existing speed poll,
without requiring Shift, adding 68 CPU cycles per idle input poll versus the original speed-only scan,
including the new RUN/STOP check (9 cycles, using the same row7 read).
The new 4 key accounts for 13 of those cycles and shares the row already read for 3. It shares the held-key latch and remains responsive
during slow playback. Disabled stars bypass all density drawing work in the IRQ;
the number keys still select the density to use when stars are enabled. `--no-starfield` omits density code and bindings too.

VIC-II sprite priority puts stars behind bitmap-set foreground pixels. Before
enabling each star, the IRQ also checks the displayed colour cell: if its low
nibble is not the displayed background colour, the entire cell is filled and
the star is suppressed. This protects both colours of a filled hires cell.
For SAKU white-card and solid outlined modes, black paint additionally needs an explicit mask: black ink and black empty space otherwise look identical to sprite priority. An optional per-picture painted bounding box suppresses stars throughout the logo region, including holes and interior whitespace. Gradient modes bypass this conservative box check. The mask follows the displayed frame and its motion.

The effect never writes the logo bitmap or its colour cells. Disabling it turns
off sprite DMA immediately and takes the short IRQ return path. Light/full switches, Shift+O outline/gradient changes, Shift+B card changes,
and help preserve the disabled state. Shift+G explicitly enables stars;
Shift+T/W explicitly disables them. A separate border-dot problem was reproduced
with sprites already disabled: repeated writes of unchanged border/background
colours. The display routine now caches those two values and writes only changes.
The idle comparisons add six CPU cycles per PAL refresh; the regression checks
both `$d015 = 0` and clean rendered border pixels after off/mode/help transitions.

The implementation avoids software star erasure and colour restoration across
three buffers. Hardware sprites still cost CPU setup **and VIC-II DMA**; this
must not be described as free. The saved PAL measurements compare the same
interactive cart with stars enabled/disabled. They establish its cost on these
pictures, not a universal claim that sprites beat every software starfield.

| Allocation | Use |
| --- | --- |
| `$1700..$1fff` | Effects code, state and 1,024 bytes of trajectory coordinates; reuses otherwise unused vector LUT space |
| `$3f80`, `$7f80`, `$ff80`, 64 bytes each | Distant-star pattern in each VIC bank |
| `$3f40`, `$7f40`, `$ff40`, 64 bytes each (interactive stars) | Two-pixel near-star pattern, immediately after the 8,000-byte bitmap |
| `$07f8`, `$47f8`, `$cbf8`, 8 bytes each | Existing screen sprite-pointer slots, refreshed after buffer flips |
| `$f8..$f9` | Private IRQ pointer, separate from renderer scratch |
| `$8800..$8bff` (only opaque variants with stars) | Four 256-byte tables of per-picture painted bounds |
| `$8c00..$8fff` (only opaque variants with stars) | Relocated trajectories; frees space for masking/control code at `$1700` |
| `$9c00..$9fff` (interactive stars only) | Density code/state and light kernel; copied from temporary `$2400..$27ff` at boot |
| `$8000..$83ff` (interactive stars only) | Original light trajectories, copied from temporary `$4400..$47ff` at boot |
| ROM frame data | Unchanged by toggling the starfield |

Both kernels and both coordinate sets are loaded into RAM during startup.
Pressing 4 patches the existing IRQ call operand with interrupts masked and
changes the sprite pattern on that key event; it does not reload ROM or branch
on a mode flag every refresh. This adds **1 KiB RAM** for light coordinates;
the light code fits the existing density reservation. The SAKU cart still uses
440 KiB of allocated ROM slots, leaving 584 KiB free. Excluding stars removes
both fields and their number-key handlers.

The packer must prove that every frame uses literal byte spans before reclaiming
vector LUT memory. Presentation modes require literal V3 colour encoding;
the standalone starfield also supports `indexed4`. Authored scenes and earlier
renderer generations are unsupported.
Source-colour presentations use a 256-byte colour lookup at `$0200`, rebuilt
only when hue/background/style changes. The generated labels and manifest record
the actual code extent; assembly rejects overlap with bitmap RAM. The optional mask/path pages are copied from bootstrap staging at `$2800..$2fff` before the bitmap is cleared. They add 2 KiB of reserved RAM only when those variants and stars are both included. Excluded stars have neither these tables nor mask work.

## Shared interactive speed controls

All newly built HORS-V3 interactive carts have **+**, **-** and **0** controls.
The default advances one precomputed orientation per produced sample. Faster
levels advance several indices before the next render, so skipped pictures do
not incur bitmap rendering or ROM-transfer work. Direction controls persist.
The maximum step is below half a turn to avoid the full-turn stationary alias;
the exact limits depend on the number of orientations in the selected mode.

Slower levels add waits proportional to the just-completed production time:
nominal factors 2, 4 and 8. Raster interrupts and star motion continue during the
wait, and speed keys remain responsive. This changes animation tempo; displayed
FPS and perceived angular speed are separate measurements. The maximum speed
can still look stroboscopic because only discrete orientations exist.

A brief message appears at `(256,184)`, immediately above the FPS counter:
`SPD.INC`, `SPD.DEC`, or `SPD.RST`. At minimum, `SPD.MIN` is red. Reaching maximum
shows `WOW!` followed by white/red `SPD.MAX`; further increases show `SPD.MAX`.
Messages expire after 50 PAL ticks. Only this small message flashes.

The shared speed/HUD reservation occupies at most `$9000..$97ff`, between otherwise idle
ROML transfers; it is copied there from bootstrap staging at `$3000..$37ff` (with its copy routine at `$2200`)
before that staging area becomes bitmap RAM. ROM transfers disable interrupts
while the cartridge is mapped, and call no speed code until RAM is restored.
Message glyphs are precomputed. Inactive feedback takes a short revision check;
no full-screen redraw or additional frame-stream data is required.

## Shared interactive help

Every new HORS-V3 cart retains the v0.7.8 introduction layout and waits
indefinitely for SPACE. Interactive carts add `press SHIFT+H for help` on its
own row directly above `SPACE to start`. **RUN/STOP** or **Shift+H** opens the
keymap from the intro or during playback. **Esc** maps to RUN/STOP in both
bundled VICE symbolic and positional keymaps; custom keymaps can differ.
RUN/STOP, Shift+H or Space closes help. Held keys must be released before
another action. Closing startup help returns to the intro without
starting playback. The help text reflects the compiled features. The intro
uses temporary bitmap RAM at `$2000..$23ff`, reclaimed during video setup,
and adds no playback instructions or persistent RAM reservation.
The producer and raster IRQ pause while help is open. Its two header rows are full-width light-blue/cyan stripes with black text,
using reverse ROM characters and colour RAM written only when help opens.
Its separate text screen
at `$8400..$87ff` leaves all three bitmap/colour buffers intact. Help code and exhibition notification data share `$9800..$9bff`; packed two-page text occupies another 1 KiB at `$c000..$c3ff`. The startup copy routine at `$2200` is reclaimed as bitmap RAM after copying. Text expands into `$8400..$87ff` only when help opens or changes page. The VIC reads its built-in character ROM for the text. Closing help
restores the VIC bank, bitmap mode, border, background and sprite-enable state.

H is tested after the existing Shift test when effects are included. RUN/STOP
shares the star-density row7 read, adding 9 CPU cycles per idle input poll.
With stars excluded, it uses a separate short row7 scan costing 34 CPU cycles,
including saving/restoring A; Shift+H remains available. The HUD release latch
is separate. Help adds no raster-refresh work and never redraws while closed.
Native checks cover all three exit keys, version/keymap, pause and buffer
preservation; host-key tests also cover Esc translation through both VICE keymaps.

## Shared HUD controls

HUD means the name/geometry information, FPS counter, temporary speed messages,
and the top-right INTERACTIVE label.
“Presentation mode” describes hiding this information while displaying the artwork.

| CLI option | Behaviour |
| --- | --- |
| `--show-hud` | Start with all HUD text visible; the normal default |
| `--hide-hud` | Start with all HUD text hidden |
| `--hud-default enabled\|disabled` | Explicit startup state; overrides show/hide aliases |
| `--default-info-text-mode enabled\|disabled` | Alias for `--hud-default` |
| `--allow-hud-toggle` | Include keyboard switches; default in HORS-V3 interactive builds |
| `--no-hud-toggle` / `--no-allow-hud-toggle` | Omit the switches and their code |

`--show-hud` and `--hide-hud` are aliases for the existing `--text-overlay`
and `--no-text-overlay` switches. HORS-V3 retains its 192-line artwork viewport
when hiding the HUD, so fitting does not change. Older PRG renderers retain
their existing full-height no-overlay behaviour. Runtime toggles require a
standalone HORS-V3 interactive cart; an explicit request elsewhere is an error.

| Key | Action |
| --- | --- |
| Shift+I | Toggle lower-left name and V:/E: counts |
| Shift+F | Toggle FPS and speed messages together |
| Shift+U | Hide all HUD text if any is visible; otherwise show all |

Keys are debounced. Each change clears or restores the affected region in all
three buffers once. Hiding FPS replaces the FPS/message drawing entry opcodes
with `RTS`; showing it restores them. No visibility branch is added to the
per-frame drawing routine, and hidden glyphs cannot reappear on buffer flips.
The INTERACTIVE drawing entry uses the same event-only RTS patch, with no new
per-frame visibility branch. Shift+I and Shift+F still operate independently on
their bottom groups. FPS accounting and speed controls continue.
Help preserves all three visibility settings when closed.

The switch module shares the already reserved speed block at `$9400..$97ff`:
no additional RAM reservation, bootstrap copy or frame-stream data. Assembly
checks its boundary and the speed module's end. With stars included, clearing
the key latch adds six CPU cycles to each ordinary unshifted input poll;
without the effects scanner it adds three. Shift-held scans do more work.
There is no HUD work in the raster IRQ. `--no-hud-toggle` omits the latch and
switch module, and a fixed hidden HUD skips glyph drawing from startup.

```bash
python c643d.py build --svg logo.svg --interactive-cart --hide-hud
python c643d.py build --svg logo.svg --interactive-cart --show-hud --no-hud-toggle
python c643d.py build --svg logo.svg --hide-hud
```

See [SAKU measured results](../examples/saku_2026/evidence/results.json) and the
[current and historical performance comparison](PERFORMANCE_COMPARISON.md).
Measurements are from stock PAL timing in VICE; physical C64 testing is not
claimed. Earlier renderer versions remain available unchanged.

## Exhibition and paged help

Cursor left/right selects help page 1/2. `5` toggles exhibition, `6` selects sequential/random, and `7`/`8` changes its interval by five seconds (5–60, default 5). Entry hides HUD and stars; manual star/HUD choices persist across automatic style switches. Ordinary startup star defaults stay unchanged. The inactive timer adds no IRQ work; scanning 5–8 adds 67 CPU cycles per idle input poll. [Shared behavior, memory, CLI and limits](EXHIBITION.md).
