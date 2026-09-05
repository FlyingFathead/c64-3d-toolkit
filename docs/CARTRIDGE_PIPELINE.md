# Cartridge pipeline (experimental)

**New: independent [`yunroll-cart-v2` frame streaming](CARTRIDGE_STREAM_V2.md) is implemented alongside the earlier milestones below.** `cart-stream` builds real frame-streamed CRTs; `cart-demos` continues to package existing PRGs. The original `yunroll-cart` scaffold is preserved.

`c64-3d-toolkit` is adding a cartridge-oriented rendering/data path alongside
its existing `.prg` pipeline. The first target is **EasyFlash** and the first
renderer consumer will be **`yunroll-cart`**, a separate derivative of the
stable `yunroll` renderer.

The ordinary `yunroll` source and PRG build path remain independent. Cartridge
work must not require `cartconv`, change table fitting, or alter output for users
who continue to build `.prg` files.

## Stage 1: stupid and measurable

The first executable milestone is intentionally small. It proves that the host
can assemble a native EasyFlash bootstrap, select multiple ROM banks, generate a
valid `.crt`, and attach that CRT directly in VICE before any animation streamer
is added.

Build it with:

```bash
./build.sh cartridge-smoke
```

Build and attach it directly in VICE:

```bash
./build.sh cartridge-smoke --run
```

An explicit `cartconv` location can be supplied when it is not in `PATH`:

```bash
./build.sh cartridge-smoke --cartconv /path/to/cartconv --run
```

The command emits:

```text
build/easyflash-smoke.crt
build/easyflash-smoke.bin
build/easyflash-smoke-romh0.bin
build/easyflash-smoke.lbl
build/easyflash-smoke.lst
build/easyflash-smoke-cart-map.txt
build/easyflash-smoke-cart-manifest.json
```

The raw `.bin` is a complete 1 MiB EasyFlash image. The CRT container may be
smaller because `cartconv` can omit empty `$FF` banks/chips.

The diagnostic places the native reset/bootstrap in bank 0 ROMH and markers in
ROML banks 1, 2, and 3. Each data bank also carries a bank-number sentinel at
`$8100`, so the C64 code verifies the mapper selection before displaying that
bank's marker. A successful visible run prints:

```text
C643D EASYFLASH BANK 1 OK
C643D EASYFLASH BANK 2 OK
C643D EASYFLASH BANK 3 OK
```

This is not yet the long-form 3D streamer. It is the deliberately boring base
that the streamer will be measured against. For automated emulator validation,
the same bootstrap can be assembled with a VICE-debug-cart test hook; success is
reported only after all three bank sentinels have been read correctly. Normal
CRT builds assemble that VICE-only hook out. This validation path has been
exercised successfully against VICE 3.10 using the project's preserved Linux
toolchain.

## EasyFlash model used by the backend

The implementation follows the EasyFlash Programmer's Reference. Important
properties for the current backend are:

- 64 banks;
- 8 KiB ROML and 8 KiB ROMH per bank, for 1 MiB total flash;
- write-only bank register at `$DE00`;
- write-only control register at `$DE02`;
- native reset from bank 0 in Ultimax mode, with ROMH visible at `$E000-$FFFF`;
- 8 KiB mode (`$06`) exposes ROML at `$8000-$9FFF`;
- cartridge-off mode (`$04`) removes the EasyFlash ROM mapping;
- 256 bytes of cartridge RAM at `$DF00-$DFFF`, always visible even when the
  cartridge ROM is hidden.

Code that changes a mapping which contains its own instructions must first move
somewhere that will remain visible. The smoke test uses the EasyFlash cartridge
RAM at `$DF00` as its tiny mapper trampoline. This is particularly convenient
during the native Ultimax reset state, where much of ordinary C64 RAM is not
visible. The later renderer/streamer itself will have a separate C64-RAM memory
map; the `$DF00` trampoline is only the bootstrap/diagnostic mechanism.

The raw host image is bank-major/interleaved:

```text
bank 00 ROML (8 KiB)
bank 00 ROMH (8 KiB)
bank 01 ROML (8 KiB)
bank 01 ROMH (8 KiB)
...
bank 63 ROML (8 KiB)
bank 63 ROMH (8 KiB)
```

`cartconv` is responsible for producing the CRT container and CHIP packets from
that image.

## Tool configuration

`cartconv` comes from the VICE tool set and is optional unless `.crt` output is
requested. Resolution follows the same general model as the existing tools:

1. command-line `--cartconv` override;
2. platform-specific/local `config/c643d.ini` setting;
3. generic `[toolchain]` setting;
4. executable in `PATH` / common VICE installation layouts;
5. built-in name `cartconv`.

Example:

```ini
[toolchain]
tass = 64tass
vice = x64sc
cartconv = cartconv

[windows]
# cartconv = C:\Tools\VICE\bin\cartconv.exe

[macos]
# cartconv = /Applications/vice-arm64-gtk3-3.8/bin/cartconv
```

Run:

```bash
./build.sh doctor
```

A missing `cartconv` is reported as optional there. It becomes a hard error only
when a cartridge command is requested, with instructions for setting its path.

## Stage 2: multi-animation demo cartridge

The first useful integration cartridge is built with:

```bash
./build.sh cart-demos
./build.sh cart-demos --run
```

By default the final example artifacts are written to `examples/cart_demos/` (`c643d-demo.crt`, bank map, and manifest), while temporary assembler/generated files and the raw 1 MiB image remain under `build/`.

It packs the ten canonical example PRGs into EasyFlash ROML banks and boots a
small cartridge menu. All four cursor directions are accepted naturally
(up/left = previous, down/right = next), and RETURN launches the chosen
animation. The packer redirects only the cartridge copy of each generated
yunroll PRG through a tiny `$0200` IRQ shim: F1 or RUN/STOP aborts back to the
menu, while SPACE launches the next animation. The ordinary PRG files remain
byte-for-byte untouched. This is intentionally a bridge
while the true frame/table stream format is developed: the animations are still
the known-good production PRGs, merely stored and launched from cartridge ROM.

The loader runtime lives at `$C800-$CFFF`, above the current canonical PRG
payloads. Native EasyFlash initially boots in Ultimax, where that high RAM is not
a safe bootstrap destination, so bank-0 ROMH first copies a tiny mapper
trampoline to the always-visible EasyFlash RAM at `$DF00`. The trampoline enters
8K mode, copies the menu/loader image from bank-0 ROML to `$C800`, hides the
cartridge, and enters the menu.

PRG payload copies also use `$DF00-$DFFF` as a 256-byte staging page. The source
page is read from ROML, cartridge ROM is hidden, then the staging page is copied
to C64 RAM. This deliberately handles payload destinations inside
`$8000-$9FFF` without depending on write-under-cartridge-ROM behaviour.

The host emits per-entry bank, load address, length, entry point, and 16-bit
checksum metadata. A VICE debug-cart validation build loads and checksums all ten
payloads through the same staging path before reporting success.

Menu presentation is a separate cartridge concern. Every demo CRT carries three
separately assembled 2 KiB runtimes: `default`, `decorative`, and `demoscene`.
`default` retains the plain utility menu, `decorative` adds a static frame/colour
layout and a menu-only compact 5x7 charset derived from the existing HUD font,
and `demoscene` adds a small private raster IRQ for animated colour gradients.
`--menu-style default|decorative|demoscene` chooses only the startup runtime.
While the menu is active, F1 cycles live through all three styles. A low-RAM
control trampoline selects EasyFlash bank 1 ROMH, copies the chosen 2 KiB runtime
back into `$C800-$CFFF`, hides the cartridge again, and resumes the menu. The
highlighted entry is preserved across the swap, and the selected style is kept
when returning from an animation.

All styles show `by FlyingFathead, 2026` and
`github: flyingfathead/c64-3d-toolkit`. The custom lowercase glyphs and raster
effect exist only in the cartridge menu; launched PRGs and the production HUD
font are unchanged.

Use `--output` when keeping differently configured/startup-style cartridges side
by side, for example:

```bash
./build.sh cart-demos --menu-style decorative --output c643d-demo-decorative
./build.sh cart-demos --menu-style demoscene --output c643d-demo-demoscene
```

This demo shell is useful on its own, but it does **not** remove the old PRG
table-RAM limit. That is the job of the next `yunroll-cart` streaming phase.

## `yunroll-cart`

`c64/renderer-yunroll-cart.asm` is intentionally separate from
`c64/renderer-yunroll.asm`. During this stage it is a reference/scaffold derived
from the known-good v0.6.2 `yunroll` source; it is **not** routed through the
normal PRG renderer selector yet.

The next implementation step is to define a simple cartridge stream/segment
format and make `yunroll-cart` consume frame/table working sets from EasyFlash
without requiring every authored frame table to coexist in C64 RAM.

See [`CARTRIDGE_ROADMAP.md`](CARTRIDGE_ROADMAP.md) for the progression from raw
bank switching through measured streaming, direct/hybrid access, compression,
long-form animation, and possible SID/demo use. See
[`CARTRIDGE_REFERENCES.md`](CARTRIDGE_REFERENCES.md) for the documentation and
community material used during the work.
