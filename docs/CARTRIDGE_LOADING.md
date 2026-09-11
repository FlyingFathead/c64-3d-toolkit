# Cartridge loading patch

Introduced in 0.7.4. The supplied release includes rebuilt current cartridges.
Older versioned cartridges remain unchanged as historical references; rebuilding
an old output is necessary to incorporate the new loader and metadata.

## Launching on Linux or Windows

From the toolkit directory:

```sh
python c643d.py run-cart path/to/demo.crt
```

Use `python3` on Linux if that is the installed command. VICE is discovered with
the normal toolkit configuration; `--vice PATH` accepts an explicit executable.
This command needs Python and VICE, but no assembler or cartconv.

For a cartridge that works after restoring VICE defaults, use:

```sh
python c643d.py run-cart path/to/demo.crt --vice-clean-settings
```

This resets VICE resources for the launched process and disables automatic
saving on exit. It does not edit or delete your VICE settings file. Ordinary
launches retain your settings, with consistent PAL, windowed and Warp-off
defaults. Explicit `--vice-arg=-warp`, `--vice-arg=-ntsc`, etc. override those
defaults for testing. These options are not claims that Warp or NTSC caused
the reported crash.

All cartridge build commands with `--run` now use the same launcher. The
launcher disables CRT write-back before detaching the configured default
cartridge, attaches the requested CRT, and leaves automatic settings saving off.
The toolkit's demos do not save game state to flash. PRG launching is unchanged.

The portable command for a prebuilt CRT, when Python is not installed, is:

```sh
x64sc -default +saveres -pal +VICIIfull +warp +easyflashcrtwrite +cart -cartcrt demo.crt
```

In PowerShell, use the normal `&` invocation for a quoted executable path.

## Image layout

| Bank/chip/offset | Content |
|---|---|
| 0 ROMH `$0000` | Native Ultimax bootstrap, CPU address `$e000` |
| 0 ROMH `$1800-$1aff` | Real AM/M29F040 V1.4 EasyAPI, 768 bytes |
| 0 ROMH `$1b00-$1b07` | PETSCII magic bytes `65 66 2d 6e 41 4d 45 3a` |
| 0 ROMH `$1b08-$1b17` | Up to 16 PETSCII name bytes, zero-padded |
| 0 ROMH `$1b18-$1bff` | Reserved, `$ff` |
| 0 ROMH `$1ffa-$1fff` | NMI/RESET/IRQ vectors |
| 2 ROML `$1800-$1bff`, scene carts only | Displaced scene content for RAM `$9400-$97ff` |

The normal scene RAM loader uses 88 pages from three ROML banks, leaving the
last bank's final eight pages unused. Four of those pages now hold the scene
content displaced by metadata. After copying the ROMH extension, the loader
restores these four pages to their original RAM addresses. Frame banks,
rendering instructions, graphics and pacing are preserved.

The metadata installer rejects occupied space instead of overwriting it, even
if it contains zeroes. Scene extension bounds also protect the reset vectors.
The boot assembler checks the space needed for its code and EF-RAM trampoline.
Fresh builds verify the CRT bytes as well as running `cartconv -c` and `-f`.
Older valid toolkit CRTs without EAPI remain accepted by `run-cart`.

EasyAPI is a flash driver. It is not needed to identify a read-only EasyFlash
demo, and its absence was not proof of a boot failure. Including the genuine
driver removes VICE's warning and supports the standard replacement convention.
The demos do not initialize or call it to write flash. Attribution, original
source and rebuild instructions are in
[`tools/c643d/data/easyapi`](../tools/c643d/data/easyapi/README.md).

## Legacy compatibility mode

Added in **0.7.5**. The older write method was discontinued as the default in
**0.7.4**. Select it explicitly when reproducing an older layout or investigating
compatibility problems:

```sh
python c643d.py build --shape cube --legacy-cart
python c643d.py build --scene examples/autotune/colour-cube.c643dscene --legacy-cart
python c643d.py cart-demos --legacy-cart
python c643d.py color-combo-test --legacy-cart
python c643d.py cartridge-smoke --legacy-cart
python tools/build_demo_cart_v2.py --legacy-cart
python tools/build_hifi_cart.py --legacy-cart
```

The option also works through `build.sh`, `cart-stream`, the `cartridge-demo`
alias and `tools/build_hors_v2_examples.py`. Python object/scene assemblers accept
`legacy_cart=True`. PRG-only renderers reject this option.

Every legacy conversion prints a warning to stderr identifying the discontinued
method and its limitations. This mode may fall outside the recommended EasyFlash
image conventions. VICE's **EAPI not found** warning is expected. Missing EAPI
alone does not make the CRT container invalid or prove a boot failure.

| Property | Standard, default | `--legacy-cart` |
|---|---|---|
| CRT writer / hardware type | cartconv / EasyFlash 32 | cartconv / EasyFlash 32 |
| Boot code | Updated shared loaders | Preserved pre-0.7.4 loaders |
| EAPI and internal EF-Name | Installed and verified | Not installed or required |
| Scene ROMH `$1800-$1bff` | Reserved for metadata | Original scene content may occupy it |
| Displaced 1 KiB | Bank 2 ROML, restored to RAM `$9400-$97ff` | No relocation; original ROMH copy |
| Packet, bank and reset-vector checks | Required | Required |
| Manifest `cart_write_method` | `standard` | `legacy` |

Legacy object and menu carts also retain their old CRT title convention
(`C643D STREAM ...` / `C643D <version> ALL ...`); colour tests keep their title.
This allows exact checksum reproduction when the old VERSION identity is used.

The two scene loaders must stay paired with their respective packing methods.
Legacy mode restores both parts, rather than removing metadata from an image
already packed for the standard loader. It permits use of the conventional
metadata area; it does **not** allow writes beyond the 1 MiB flash capacity,
out-of-range banks, damaged packets or extension data overwriting reset vectors.
The renderers, frame encoding and pacing remain selected by their normal options.
This is the old packing and startup method with current rendering code and release
identity, not a claim that every byte of a new build equals an old release.

Automatically chosen output names append `-legacy`; an explicit `--output NAME`
is used as supplied and follows the ordinary overwrite policy. Existing CRTs are
not converted by `run-cart`. `--run` and `run-cart` retain protected write-back
and settings handling for both formats. No automatic fallback occurs if standard
packing or validation fails. Omit `--legacy-cart` to return to the standard path.
Official prebuilt release cartridges use the standard path.

The default object/scene loaders in 0.7.5 also initialize `$01` before `$00`, as
specified by the [EasyFlash Programmer's Guide](https://skoe.de/easyflash/files/devdocs/EasyFlash-ProgRef.pdf),
chapter 4. Legacy boot sources deliberately retain their historical sequence.
This does not establish that the reported Windows GUI JAM was caused by that order.

## Windows `$f800` report

A tester reported v0.7.2 failing in VICE 3.10 Win64 after toggling Warp, with
`Main CPU: JAM at $F800`. Restoring settings recovered it. This patch addresses
confirmed loading gaps; it does not claim that Windows-specific sequence is
reproduced or fixed. The same number can address different ROM/RAM depending on
the mapper, so `$f800` alone does not identify the offending byte or EAPI.

If it recurs, preserve the working and failing settings files before another
reset to defaults, the exact VICE build, the cartridge SHA-256, and a monitor
snapshot at the JAM. Compare the saved settings and inspect the actual memory
mapping at the failure. Do not infer corruption solely from the warning.

## Verification

Run the unit suite with:

```sh
python -m unittest discover -s tests -q
```

The patch's tests cover PETSCII reference bytes, collision rejection, complete
scene-extension restoration, corrupt CRT packets/reset vectors, authentic EAPI
bytes, launch option ordering and CLI recovery handling.

Emulator checks use PAL Linux VICE 3.10 from the supplied tool bundle. Startup
with Warp on/off, monitor Warp transitions and soft resets are distinct from
the untested Windows GUI interaction and from physical-hardware validation.
Existing pixel/menu/ending verifiers remain the playback correctness gates.
