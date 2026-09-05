# Cartridge / streaming roadmap

This roadmap covers the cartridge-specific path beginning with the experimental
`yunroll-cart` renderer.  The cartridge backend is intentionally separate from
the stable PRG `yunroll` pipeline: cartridge work must not change the normal PRG
memory map, generated output, or regression binaries unless a change is made
explicitly for both backends.

## Design rule: start stupid and measurable

The first implementation should favour simple, inspectable data movement over
compression or clever encoding.  Establish correct EasyFlash booting, bank
selection, streaming, and renderer integration first; then measure real costs
before optimizing.

Every optimization should answer at least one measured question:

- How many cartridge bytes are consumed per rendered frame?
- How many 6510 cycles are spent fetching/copying/decompressing a frame?
- How many cycles are spent rendering that frame?
- Is a scene limited by cartridge storage, transfer/decode time, or renderer
  time?
- How much deterministic raster-time headroom remains for SID playback and
  other demo work?

## Phase 0 - preserve the v0.6.2 PRG baseline

- Keep `yunroll` and all existing PRG renderers unchanged.
- Keep v0.6.2 PRG golden-output regression checks in place.
- Add cartridge support only through new files and narrowly scoped host-tool
  hooks.
- Keep `cartconv` optional for ordinary PRG builds.

Success criterion: normal PRG builds continue to behave and hash exactly like the v0.6.2 baseline.

## Phase 1 - minimum EasyFlash proof of concept

- Add a dedicated `yunroll-cart` assembly source.
- Add a minimal EasyFlash bootstrap and mapper include.
- Build a known-data cartridge with several banks.
- Switch banks from mapper-safe code and read a recognizable byte/string
  pattern plus a bank-specific sentinel from each bank. The initial EasyFlash
  smoke test uses the always-visible 256-byte cartridge RAM at `$DF00`.
- Produce a valid EasyFlash `.crt` using `cartconv`.
- Launch the CRT directly in VICE for a near-instant edit/build/run cycle.

Success criterion: bank 0 boots reliably, later banks can be selected and read,
and the result works repeatedly under VICE without PRG autoload.

## Phase 2 - tooling and failure handling

- Auto-discover `cartconv` in PATH and common VICE installation locations.
- Add a persistent `cartconv` path in the normal toolchain config.
- Add a CLI override for an explicit `cartconv` executable.
- Teach `doctor` to report `cartconv` as optional unless cartridge output is
  requested.
- Fail cartridge builds with a useful installation/configuration message when
  `cartconv` is unavailable.
- Keep Linux, macOS, and Windows setup/documentation in sync.
- Emit a human-readable cartridge bank map and a machine-readable manifest.

Success criterion: a new user can diagnose a missing `cartconv` without reading
source code, while a PRG-only user never needs it.

## Phase 2.5 - useful demo shell before true streaming

Build a menu-driven EasyFlash cartridge from the canonical existing PRGs and keep the
shippable example under `examples/cart_demos/`. This
is deliberately an integration bridge rather than a claim that PRG payloads are
"streamed" render data.

- Pack each canonical animation into banked ROML storage.
- Boot a small RAM-resident menu/loader from EasyFlash.
- Select entries with cursor keys and launch with RETURN.
- Patch only cartridge copies through a low-RAM IRQ shim so F1/RUN-STOP returns
  to the menu and SPACE advances to the next animation; keep ordinary PRGs
  untouched.
- Make menu presentation selectable (`default`, `decorative`, `demoscene`) while
  keeping navigation/loader behaviour identical. Carry all three runtimes in one
  CRT, use `--menu-style` only for the startup choice, and let F1 cycle styles
  live without losing the highlighted entry. Include the project byline/repo
  footer in every style; reserve animated raster colour work for `demoscene` so
  the default path stays deliberately boring and easy to debug.
- Copy PRGs through the always-visible `$DF00` EasyFlash RAM staging page so
  destinations hidden by the ROML window are handled explicitly.
- Generate bank/load/length/checksum metadata on the host.
- Validate every payload through the real C64-side copy path with VICE's debug
  cartridge before treating the launcher as sound.

Success criterion: multiple existing toolkit animations boot instantly from one
CRT, and at least one production animation is verified rendering after the
cartridge loader hands control to it.

## Phase 3 - simple frame-segment streaming

Use the cartridge as a read-only backing store, not as extra CPU or RAM.
Initially keep the format intentionally simple:

1. pack generated frame/table data into EasyFlash banks;
2. keep only the active segment/working set in C64 RAM;
3. render the segment using `yunroll-cart`;
4. load the next segment and continue.

Do not introduce compression yet.  Prefer fixed/obvious headers, whole-frame
boundaries where practical, explicit bank/offset descriptors, and strong host
validation.

Success criterion: animation length is no longer constrained by fitting all
sampled frame tables in C64 RAM at once.

## Phase 4 - measure the real bottleneck

Add benchmark builds or instrumentation for:

- sequential cartridge-ROM read throughput;
- cartridge-ROM -> RAM copy throughput;
- bank-switch overhead;
- per-frame streamed bytes;
- per-frame streaming cycles;
- per-frame renderer cycles;
- worst-case frame time, not just the average;
- cartridge capacity used and estimated duration at the requested FPS.

VICE cycle/raster measurements should be preferred over assumptions.  Real
hardware validation should be performed whenever practical because cartridge
mapping mistakes can be hidden by an emulator or by an emulator configuration.

Success criterion: every later optimization is driven by numbers from a real
scene rather than folklore about cartridge speed.

## Phase 5 - direct and hybrid cartridge streaming

After the simple copier is characterized, compare two alternatives:

### Direct ROM consumption

Keep frame/run/table records in cartridge ROM and have the renderer read them
through the active cartridge aperture where this saves more cycles/RAM than a
copy-to-RAM path costs.

### Hybrid/cache consumption

Maintain a small current/next working set in RAM.  Fetch or decode upcoming
records while the renderer/display pipeline has spare time, then switch working
sets without a visible interruption.

The goal is constant or near-constant RAM usage as animation duration grows.

Success criterion: longer animation increases ROM use rather than active table
RAM use, with no visible bank-load pauses.

## Phase 6 - cartridge-specific compression and reuse

Only after raw streaming is measured, investigate encodings that are cheap for
the 6510 to consume:

- shared/static topology data;
- per-frame deltas;
- repeated run/table dictionaries;
- delta-coded addresses or coordinates;
- lightweight RLE/packbits-style structures;
- cartridge layouts chosen for sequential access and minimal mapper churn.

Compression ratio alone is not the objective.  A smaller stream that costs too
many CPU cycles to decode can reduce animation frame rate and is therefore a
loss.

Success criterion: better seconds-per-cartridge without breaking the chosen
frame-rate target.

## Phase 7 - long-form animation targets

Treat duration as a progressive test rather than a promise:

- 10 seconds continuous playback;
- 30 seconds continuous playback;
- 60 seconds continuous playback;
- multi-minute playback if scene complexity, frame rate, and packed size allow
  it.

Build reports should expose enough information to explain why a particular
scene reaches or misses a duration target, for example:

```text
renderer:             yunroll-cart
cartridge:            EasyFlash
target fps:           20
rendered frames:      1200
duration:             60.0 s
banks used:           58 / 64
ROM payload:          912 KiB / 1024 KiB
average bytes/frame:  778
stream/decode budget: 12%
render budget:        72%
headroom:             16%
```

The exact fields and estimates should be based on measured implementation data.

## Phase 8 - demo features / SID headroom

Once uninterrupted streaming is stable, measure whether a small SID player can
run from the raster IRQ without compromising the renderer or stream scheduler.
The desired structure is approximately:

```text
raster IRQ
  -> SID play tick
  -> display-buffer scheduling
  -> return quickly

main loop
  -> consume cartridge data
  -> render next frame
  -> prepare next chunk
  -> synchronize/publish
```

Possible later cartridge assets include music, fonts, sprites, bitmap/title
screens, scene metadata, and scripted demo sections.  These should reuse the
same generic cartridge-stream layer where possible instead of teaching every
renderer its own mapper protocol.

## Longer-term backend design

`yunroll-cart` is the first consumer, but the cartridge work should evolve into
a small generic read-only asset/stream subsystem.  A logical stream API should
hide bank arithmetic from renderers so a future mapper or larger cartridge type
can be added without rewriting the rendering core.

Conceptually:

```text
logical asset / stream offset
        -> mapper bank + window offset
        -> cartridge aperture
        -> direct read or RAM working set
        -> renderer / other consumer
```

EasyFlash is the initial target because it is documented, emulated by VICE, and
provides a practical 1 MiB banked ROM for stock-C64 development.  Supporting a
future cartridge type should be an additive backend decision, not a rewrite of
`yunroll-cart` geometry generation.
