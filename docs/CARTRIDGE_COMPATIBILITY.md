# C64 Cartridge Compatibility

**Project:** `c64-3d-toolkit`  
**Research snapshot:** 2026-09-14  
**Scope:** C64 cartridge images and cartridge-like devices relevant to distributing and testing toolkit-generated `.crt` files, with special attention to **EasyFlash**, **GMod3**, and **GMod4**.

> [!IMPORTANT]
> This document separates **virtual `.crt` emulation** from **physical cartridge-port compatibility**.
>
> A machine may have a highly compatible physical cartridge port while still being unable to load the same cartridge type from a `.crt` file. For `c64-3d-toolkit`, virtual `.crt` support is especially important because the toolkit generates cartridge images.

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Documented support for the stated version/target |
| ⚠️ | Supported only with an important limitation, patch, experimental build, or partial implementation |
| ❌ | Not implemented / not listed as supported in the checked version |
| ? | Not sufficiently documented or independently verified |

## Executive compatibility matrix

This is the short version.

| Target checked | Version / date checked | EasyFlash | GMod3 | GMod4 | Scope / important notes |
|---|---|:---:|:---:|:---:|---|
| **VICE** | **stock 3.10**, released 2025-12-24 | ✅ | ✅ | ❌ | GMod3 is standard CRT **type 62** in stock VICE 3.10. GMod4 is not merged into stock 3.10. |
| **VICE experimental GMod4 build** | **3.10 r45942**, 2026-01-05 | ✅ | ✅ | ⚠️ | Separate GMod4 patch / Win64 experimental build. See the production-GMod4 warning below. |
| **Ultimate 64 / Ultimate 64-II** | **firmware 3.15a**, 2026-09-11 | ✅ | ❌ | ❌ | Built-in `.crt` emulation. Firmware 3.15 adds larger cart-image handling and Megabyter/TwoMegabyter, but not GMod3/GMod4. |
| **Ultimate-II+ / Ultimate-II+L** | **firmware 3.15a**, 2026-09-11 | ✅ | ❌ | ❌ | Built-in `.crt` emulation. |
| **1541 Ultimate-II** | **firmware 3.15a**, 2026-09-11 | ✅ | ❌ | ❌ | Built-in `.crt` emulation. A special historical U2 hardware variant supported GMod2, not GMod3. |
| **Commodore 64 Ultimate** | **firmware 1.1.0**, 2026-03-16 | ✅ | ❌ | ❌ | Built-in/virtual cartridge support documented by the Oct 2025 user guide; firmware 1.1.0 does not announce GMod3/GMod4 support. Physical cartridge port is a separate question. |
| **Kung Fu Flash** | **v1.53**, 2025-03-23, last GitHub release before upstream migration | ✅ | ❌ | ❌ | Current upstream moved to Codeberg; this row is pinned to the last verifiable GitHub release/docs snapshot. |
| **Kung Fu Flash 2** | **v2.04**, 2025-11-30 | ✅ | ❌ | ❌ | Experimental software-defined cartridge. |
| **C64 for MEGA65** | **core 5.2** | ✅* | ❌ | ❌ | Virtual EasyFlash works, but is **read-only from the image/persistence point of view**: writes are not saved back to SD. |
| **Turbo Chameleon 64** | **Beta-9r**, 2025-11-24 | ✅ | ❌ | ❌ | Current documented emulated-cartridge list includes EasyFlash, not GMod3/GMod4. |
| **Sidekick64** | **v0.51d / current documented feature set** | ✅** | ❌ | ❌ | EasyFlash uses **simplified EAPI support**. Current cartridge list does not include GMod3/GMod4. |
| **MiSTer C64 core** | current master checked 2026-09-14 | ✅ | ? | ? | Documentation says “almost all cartridge formats” and explicitly exposes EasyFlash behavior, but no current authoritative per-type list was found for GMod3/GMod4. Do not advertise them as supported without a targeted test/source audit. |
| **Magic Desk 2 hardware in GMod3 mode** | current project docs checked 2026-09-14 | — | ⚠️ | — | Implements a **2 MiB read-only subset of GMod3**. No GMod3 BitBang/write capability. |

\* MEGA65 virtual EasyFlash persistence caveat described below.  
\** Sidekick64 EasyFlash support is not a claim of perfect hardware-equivalent EAPI behavior.

## The important VICE distinction

### Stock VICE 3.10

For the toolkit's emulator/reference path, the clean facts are:

- **EasyFlash:** supported.
- **GMod3:** supported as **CRT hardware type 62**.
- **GMod3 capacities documented by VICE:** 2, 4, 8, and 16 MiB.
- **GMod3 normal window:** `$8000-$9FFF`, 8 KiB at a time.
- **GMod4:** **not part of stock VICE 3.10**.

This makes stock **VICE 3.10** a practical reference target for both EasyFlash and GMod3.

### VICE 3.10 + experimental GMod4 patch

VICE patch ticket **#368, “GMod4 support,”** is still `open-wip`. The latest published patch at the time of this research is:

```text
gmod4-r45942.diff
```

and VICE also publishes a separate Win64 experimental build:

```text
GTK3VICE-3.10-win64-r45942-gmod4.zip
```

Therefore a correct compatibility label is:

```text
VICE 3.10 stock                GMod4: NO
VICE 3.10 + r45942 patch/build GMod4: EXPERIMENTAL
```

It is misleading to say simply “VICE 3.10 supports GMod4.”

### Critical 2026 GMod4 hardware-revision warning

There is an additional 2026 complication.

Individual Computers changed the GMod4 production design in **August 2026**. The current production version is API-compatible with the earlier prototypes, but **not binary-compatible** with them without register-definition changes. In particular, the bank-register addresses were shuffled, and the current control register requires an activation bit.

The latest published VICE GMod4 patch/build is from **January 2026**, before that production-hardware change.

For that reason, this document does **not** currently claim that the January `r45942` VICE patch exactly emulates the final August-2026 production GMod4 register semantics. Until the patch is updated or a direct compatibility test establishes otherwise, treat it as:

> **experimental GMod4 emulation based on the pre-production-era specification**

This matters for a future `c64-3d-toolkit` GMod4 backend. Emulator tests alone should not be presented as production-hardware validation yet.

## The three “Ultimate” families

The names are easy to mix up, so this document uses them as follows.

### Ultimate 64 / Ultimate 64-II

These are Gideon Zweijtzer's FPGA C64 replacement systems.

Current firmware checked here:

```text
3.15a
2026-09-11
```

The same firmware family also covers Ultimate-II, Ultimate-II+, and Ultimate-II+L.

### Ultimate-II / Ultimate-II+ / Ultimate-II+L

These are the 1541 Ultimate cartridge/peripheral family. This is the family often meant informally by “1541 Ultimate.”

They can load `.crt` images, but their cartridge emulation implements only selected CRT hardware types.

### Commodore 64 Ultimate

This is the 2026 Commodore-branded FPGA machine. It includes integrated Ultimate-II+-style functionality, but its firmware/documentation versioning is separate.

Current firmware checked here:

```text
1.1.0
2026-03-16
```

Do not silently assume that a feature in Gideon's standalone Ultimate firmware 3.15a is already present in Commodore 64 Ultimate firmware 1.1.0.

## Gideon Ultimate `.crt` support

The official Ultimate cartridge-emulation table explicitly leaves **CRT type 62 / GMod3 blank** on:

- 1541 Ultimate-II
- Ultimate-II+
- Ultimate 64

and does not list GMod4 as an implemented virtual-cartridge type.

EasyFlash is supported on all three columns.

### Documented supported C64 cartridge types

The following are marked as supported in the official Ultimate cartridge table, with firmware 3.15 adding two more cartridge formats afterward.

| CRT type | Cartridge | 1541U2 | U2+ | U64 |
|---:|---|:---:|:---:|:---:|
| 0 | Normal 8K / 16K / Ultimax | ✅ | ✅ | ✅ |
| 1 | Action Replay | ✅ | ✅ | ✅ |
| 2 | KCS Power Cartridge | ✅ | ✅ | ✅ |
| 3 | Final Cartridge III | ✅ | ✅ | ✅ |
| 4 | Simons' BASIC | ✅ | ✅ | ✅ |
| 5 | Ocean type 1 | ✅ | ✅ | ✅ |
| 8 | Super Games | ✅ | ✅ | ✅ |
| 9 | Atomic Power | ✅ | ✅ | ✅ |
| 10 | Epyx Fastload | ✅ | ✅ | ✅ |
| 11 | Westermann | ✅ | ✅ | ✅ |
| 13 | Final Cartridge I | ✅ | ✅ | ✅ |
| 15 | C64 Game System | ✅ | ✅ | ✅ |
| 18 | Zaxxon | ✅ | ✅ | ✅ |
| 19 | Magic Desk / Domark / HES Australia | ✅ | ✅ | ✅ |
| 20 | Super Snapshot 5 | ✅ | ✅ | ✅ |
| 21 | COMAL 80 | ✅ | ✅ | ✅ |
| 32 | **EasyFlash** | ✅ | ✅ | ✅ |
| 36 | Retro Replay | ✅ | ✅ | ✅ |
| 44 | EXOS | ✅ | ✅ | ✅ |
| 53 | Pagefox | ✅ | ✅ | ✅ |
| 54 | Kingsoft Business BASIC | ✅ | ✅ | ✅ |
| 60 | GMod2 | ⚠️* | ✅ | ✅ |
| 62 | **GMod3** | ❌ | ❌ | ❌ |
| 64 | Blackbox V8 | ✅ | ✅ | ✅ |
| 65 | Blackbox V3 | ✅ | ✅ | ✅ |
| 66 | Blackbox V4 | ✅ | ✅ | ✅ |
| 71 | Blackbox V9 | ✅ | ✅ | ✅ |

\* The original 1541U2 had a special hardware variant that could support GMod2 at the cost of other features.

Firmware **3.15** additionally adds:

- CRT type **86**, Protovision **Megabyter**
- CRT type **87**, Protovision **TwoMegabyter**

The 3.15 release also expands the cartridge ROM area on **Ultimate 64 / Ultimate 64-II** from 1 MiB to 4 MiB. That is additional image capacity; it does **not** add GMod3 mapper emulation by itself.

### EasyFlash write support on Ultimate

Ultimate emulates EasyFlash writes by patching the cartridge's EAPI area with its own driver. Modified cartridge state must then be explicitly saved back to storage.

There is also an I/O-resource caveat: ordinary EasyFlash uses `$DF00-$DFFF`, so Ultimate may disable conflicting facilities such as REU/UCI/Audio Sampler while the cartridge is active.

## Commodore 64 Ultimate virtual cartridge support

For the **Commodore 64 Ultimate**, the checked public documentation is:

- User Guide, 1st Edition, October 2025
- firmware 1.1.0, March 16 2026

The documented built-in virtual cartridge formats include:

- Generic 8K / 16K / Ultimax
- Action Replay
- KCS Power Cartridge
- Final Cartridge III
- Simons' BASIC
- Ocean type 1
- Super Games
- Atomic Power
- Epyx Fastload
- Westermann
- Final Cartridge I
- Magic Formel
- C64 Game System
- Zaxxon
- Magic Desk / Domark / HES
- Super Snapshot 5
- COMAL 80
- **EasyFlash**
- Retro Replay
- EXOS
- Pagefox
- Kingsoft Business BASIC
- GMod2
- Blackbox V8
- Blackbox V3
- Blackbox V4

**GMod3 and GMod4 are not in that documented virtual-cartridge list.** Firmware 1.1.0's published changes do not announce either format.

This is why the matrix marks:

```text
Commodore 64 Ultimate 1.1.0
EasyFlash  YES
GMod3      NO (virtual image support not documented)
GMod4      NO (virtual image support not documented)
```

### Physical cartridge port is a different matter

Commodore advertises the machine's physical cartridge port as greater than 99% compatible with classic C64 cartridges/peripherals.

That does **not** automatically prove every feature of modern programmable cartridges.

Most importantly, the current GMod4 manufacturer documentation explicitly says that **AGR (“All Graphics RAM”) does not currently work on the 2026 Commodore 64 Ultimate**.

So for a *physical* GMod4:

```text
ordinary GMod4 functions: potentially usable, needs direct validation
AGR:                      documented incompatible at present
full GMod4 compatibility: DO NOT claim
```

The same AGR warning applies to Gideon's Ultimate-64.

No equally explicit current manufacturer test statement was found for a physical GMod3 on these FPGA cartridge ports. Because GMod3 was never mass-produced, the honest label is **unverified**, not automatically “yes.”

## EasyFlash, GMod3, and GMod4 hardware context

### EasyFlash

EasyFlash is a 1 MiB flash cartridge:

- 512 KiB logical ROML
- 512 KiB logical ROMH
- 64 banks
- 8 KiB or 16 KiB cartridge mapping depending on mode
- 256 bytes of cartridge RAM at `$DF00`
- mature EAPI mechanism for writing flash

For public distribution, its main advantage is not capacity. It is **ecosystem support**.

### GMod3

GMod3 was designed with:

- 2, 4, 8, or 16 MiB flash
- one normal 8 KiB window at `$8000-$9FFF`
- up to 2048 banks
- bank registers at `$DE00-$DE07`
- special IRQ/NMI-vector support
- direct SPI-flash BitBang mode for programming

But Individual Computers states that **GMod3 was not mass-produced and was superseded by GMod4**.

That explains the compatibility pattern:

```text
VICE:       excellent development target
real carts: very uncommon
multi-cart / FPGA ecosystem: poor support
```

A useful exception is the open-hardware **Magic Desk 2**, which can implement a **2 MiB read-only GMod3-compatible subset**.

### GMod4

Current GMod4 provides an 8 MiB flash architecture with substantially more flexible mapping than GMod3, including independent cartridge regions and two banking contexts.

It is potentially much more interesting for demanding combined graphics/audio runtimes, but the software ecosystem is currently less mature:

- stock VICE 3.10: no
- experimental VICE 3.10 GMod4 patch/build: yes, with the production-revision warning
- current Ultimate virtual `.crt`: no documented support
- current KFF/KFF2: no documented support
- current MEGA65 C64 virtual cart: no
- current Chameleon emulated cart list: no
- current Sidekick64 cart list: no

## Other cartridge emulators / FPGA targets

### Kung Fu Flash v1.53

The original GitHub repository was archived in December 2025 and points to a new Codeberg upstream. The last GitHub release that could be independently checked here is **v1.53**.

Its supported cartridge family includes the usual generic, freezer, Ocean/Magic Desk-style formats and **EasyFlash**, but not GMod3 or GMod4.

For reproducible compatibility claims, pin the tested firmware version instead of saying only “Kung Fu Flash.”

### Kung Fu Flash 2 v2.04

Current checked release:

```text
v2.04
2025-11-30
```

Documented supported cartridges include:

- Generic 8K / 16K / Ultimax
- Action Replay 4.x / 5 / 6
- KCS Power
- Final Cartridge III(+)
- Simons' BASIC
- Fun Play / Power Play
- Super Games
- Ocean type 1
- Epyx Fastload
- C64 Game System / System 3
- WarpSpeed
- Dinamic
- Zaxxon / Super Zaxxon
- Magic Desk / Domark / HES
- Super Snapshot 5
- COMAL-80
- Ross
- **EasyFlash**
- Prophet64
- Freeze Frame
- Freeze Machine
- MACH 5
- Pagefox
- RGCD / Hucky
- Drean
- C128 generic external-function ROM
- WarpSpeed 128

GMod3 and GMod4 are not listed.

### C64 for MEGA65 core 5.2

The core documentation is unusually explicit:

> Any cartridge type not in its implemented list is not supported.

Virtual cartridge types listed by core 5.2 are:

- generic Ultimax
- generic 8 KiB
- generic 16 KiB
- generic CRT wrapper
- Action Replay V5
- Final Cartridge III
- Simons' BASIC
- Ocean
- Fun Play
- Super Games
- C64 Games System
- Dinamic
- Magic Desk
- COMAL 80
- Structured BASIC
- Mikro Assembler
- **EasyFlash**
- GMod2
- BMP Data Turbo 2000

EasyFlash and GMod2 virtual images are effectively read-only with respect to persistence: cartridge-side changes are not written back to the SD-card `.crt`.

GMod3 and GMod4 are not on the list.

### Turbo Chameleon 64 Beta-9r

Current checked core:

```text
Beta-9r
2025-11-24
```

Documented emulated game/utility cartridges include:

- generic 8/16 KiB
- Simons' BASIC
- Ocean type 1
- FunPlay
- Super Games
- Epyx Fastload
- Westermann
- C64 Game System / System 3
- WarpSpeed
- Dinamic
- Zaxxon
- Magic Desk
- COMAL-80
- Ross
- Mikro Assembler
- StarDos
- **EasyFlash**
- Prophet-64
- Mach-5
- PageFox
- Business BASIC

Documented freezer cartridges include:

- Action Replay
- Retro Replay
- Final Cartridge III
- Expert Cartridge
- KCS Power
- Super Snapshot 5
- Capture

GMod3 and GMod4 are not listed.

### Sidekick64 v0.51d

Current checked feature list includes:

- plain CBM80 / generic cartridges
- **EasyFlash**, with simplified EAPI support
- GMod2, including EEPROM save-game support
- Magic Desk / Domark / HES
- Ocean Type A / B
- Dinamic
- C64 Game System
- Funplay / Powerplay
- COMAL-80
- Epyx Fastload
- Warp Speed
- Megabit ROM for C128
- Zaxxon / Super Zaxxon
- Prophet64
- Simons' BASIC
- RGCD / Hucky
- multiple freezer cartridges

GMod3 and GMod4 are not listed.

### MiSTer C64 core

Current public documentation says **“Almost all cartridge formats (`*.CRT`)”**, and the core has explicit EasyFlash functionality.

That wording is too broad to infer GMod3 or GMod4 support safely. A targeted source/test audit is still needed before putting a green check beside either one.

For the toolkit, the correct status is therefore:

```text
EasyFlash: supported
GMod3:     not yet verified for this document
GMod4:     not yet verified for this document
```

## VICE 3.10 C64 CRT type registry

VICE is the broadest software reference in this document. Its 3.10 manual currently defines the following C64 CRT IDs.

> [!NOTE]
> Being present in the CRT registry is not always equivalent to being a normal loadable emulated cartridge. For example, type 33 “EasyFlash Xbank” is a container format and VICE explicitly says it cannot load it as cartridge hardware.

| ID | Type | ID | Type |
|---:|---|---:|---|
| 0 | Generic cartridge | 44 | EXOS |
| 1 | Action Replay | 45 | Freeze Frame |
| 2 | KCS Power Cartridge | 46 | Freeze Machine |
| 3 | Final Cartridge III | 47 | Snapshot64 |
| 4 | Simons' BASIC | 48 | Super Explode V5.0 |
| 5 | Ocean type 1 | 49 | Magic Voice |
| 6 | Expert Cartridge | 50 | Action Replay 2 |
| 7 | Fun Play / Power Play | 51 | MACH 5 |
| 8 | Super Games | 52 | Diashow-Maker |
| 9 | Atomic Power | 53 | Pagefox |
| 10 | Epyx Fastload | 54 | Kingsoft |
| 11 | Westermann Learning | 55 | Silverrock 128K Cartridge |
| 12 | Rex Utility | 56 | Formel 64 |
| 13 | Final Cartridge I | 57 | RGCD / Hucky subtype |
| 14 | Magic Formel | 58 | RR-Net MK3 |
| 15 | C64 Game System / System 3 | 59 | EasyCalc |
| 16 | Warp Speed | 60 | GMod2 |
| 17 | Dinamic | 61 | MAX Basic |
| 18 | Zaxxon / Super Zaxxon | **62** | **GMod3** |
| 19 | Magic Desk / Domark / HES | 63 | ZIPP-CODE 48 |
| 20 | Super Snapshot V5 | 64 | Blackbox V8 |
| 21 | COMAL-80 | 65 | Blackbox V3 |
| 22 | Structured BASIC | 66 | Blackbox V4 |
| 23 | Ross | 67 | REX RAM-Floppy |
| 24 | Dela EP64 | 68 | BIS-Plus |
| 25 | Dela EP7x8 | 69 | SD-BOX |
| 26 | Dela EP256 | 70 | MultiMAX |
| 27 | Rex EP256 | 71 | Blackbox V9 |
| 28 | Mikro Assembler | 72 | Lt. Kernal Host Adaptor |
| 29 | Final Cartridge Plus | 73 | RAMLink |
| 30 | Action Replay 4 | 74 | H.E.R.O. |
| 31 | StarDOS | 75 | IEEE Flash! 64 |
| **32** | **EasyFlash** | 76 | Turtle Graphics II |
| 33 | EasyFlash Xbank container | 77 | Freeze Frame MK2 |
| 34 | Capture | 78 | Partner 64 |
| 35 | Action Replay 3 | 79 | Hyper-BASIC |
| 36 | Retro Replay / Nordic Replay subtype | 80 | Universal Cartridge 1 |
| 37 | MMC64 | 81 | Universal Cartridge 1.5 |
| 38 | MMC Replay | 82 | Universal Cartridge 2 |
| 39 | IDE64 | 83 | BMP Data Turbo 2000 |
| 40 | Super Snapshot V4 | 84 | Profi-DOS |
| 41 | IEEE-488 | 85 | Magic Desk 16 |
| 42 | Game Killer | 86 | Protovision Megabyter |
| 43 | Prophet64 |  |  |

The official VICE 3.10 manual checked here does **not** contain GMod4 in this stock registry.

## Physical-cartridge summary

This table deliberately does not pretend that virtual-image emulation and electrical cartridge-port support are the same thing.

| Host | EasyFlash physical cart | GMod3 physical cart | GMod4 physical cart |
|---|:---:|:---:|:---:|
| Original C64/C64C | ✅ | ✅* | ✅ |
| Ultimate 64 / U64-II cartridge port | ✅ / expected normal use | ? | ⚠️ |
| Commodore 64 Ultimate cartridge port | ✅ / expected normal use | ? | ⚠️ |
| MEGA65 C64 core expansion port | ✅ with core/hardware caveats | ? | ? |

\* GMod3 is a valid cartridge design, but the original iComp GMod3 was never mass-produced.

For both Ultimate-64 and Commodore 64 Ultimate, **GMod4 AGR is currently documented as incompatible**. That is sufficient reason not to mark physical GMod4 as full green-check compatibility.

## What this means for `c64-3d-toolkit`

### EasyFlash should remain the compatibility/default backend

EasyFlash currently has the strongest distribution story:

- stock VICE 3.10
- Ultimate 64
- Ultimate-II / II+
- Commodore 64 Ultimate virtual cartridge loader
- Kung Fu Flash
- Kung Fu Flash 2
- C64 for MEGA65
- Turbo Chameleon
- Sidekick64
- MiSTer
- real EasyFlash-compatible hardware

That is a huge practical advantage.

### GMod3 is a useful high-capacity experimental backend

GMod3 remains technically attractive because of its 2–16 MiB capacity and because **stock VICE 3.10 supports it directly**.

Its weakness is distribution compatibility. Most popular software-defined cartridges and FPGA virtual-cartridge loaders do not implement it.

A sensible toolkit role is therefore:

```text
EasyFlash
    default / broadly compatible release target

GMod3
    optional high-capacity / research / performance target
    stock VICE 3.10 as the reference emulator

GMod4
    future experimental target
    requires specially versioned emulator/hardware validation
```

### Do not use one generic “VICE compatible” badge

For release documentation, write the exact target.

Good:

```text
Tested: VICE 3.10 stock, GMod3 CRT type 62
```

Good:

```text
Experimental GMod4: VICE 3.10 r45942 GMod4 build
```

Bad:

```text
Works in VICE 3.10
```

for GMod4, because that incorrectly implies stock support.

### Suggested minimum backend test matrix

| Backend | Minimum emulator test | Wider-device tests worth keeping |
|---|---|---|
| EasyFlash | stock VICE 3.10 | Ultimate 3.15a; Commodore 64 Ultimate 1.1.0; optionally KFF/KFF2, MEGA65, Chameleon, Sidekick |
| GMod3 | stock VICE 3.10 | physical/read-only-compatible hardware when available |
| GMod4 | experimental VICE 3.10 r45942 **only as provisional emulator evidence** | final production GMod4 hardware; re-test after emulator patch is brought in line with Aug-2026 hardware |

## Sources

Primary/current sources used for this snapshot:

1. VICE 3.10 CRT format/manual:
   - https://vice-emu.sourceforge.io/vice_17.html
   - https://vice-emu.sourceforge.io/vice_7.html
2. VICE downloads and experimental GMod4 build:
   - https://sourceforge.net/projects/vice-emu/files/
   - https://sourceforge.net/projects/vice-emu/files/experimental%20binaries/
3. VICE GMod4 patch #368:
   - https://sourceforge.net/p/vice-emu/patches/368/
4. Individual Computers GMod3:
   - https://wiki.icomp.de/wiki/GMod3
5. Individual Computers GMod4:
   - https://wiki.icomp.de/wiki/GMod4
6. Ultimate cartridge-emulation documentation:
   - https://1541u-documentation.readthedocs.io/en/latest/howto/cartridges.html
7. Ultimate firmware 3.15 release notes:
   - https://1541u-documentation.readthedocs.io/en/latest/howto/release_3.15.html
8. Current Ultimate firmware downloads:
   - https://ultimate64.com/Firmware
9. Commodore 64 Ultimate downloads / firmware:
   - https://commodore.net/downloads/
   - https://commodore.net/commodore-64-ultimate-firmware-version-1-1-0/
10. Commodore 64 Ultimate product compatibility statement:
    - https://commodore.net/computer/
11. Kung Fu Flash:
    - https://github.com/KimJorgensen/KungFuFlash
    - https://github.com/KimJorgensen/KungFuFlash/releases
12. Kung Fu Flash 2:
    - https://github.com/KimJorgensen/KungFuFlash2
    - https://github.com/KimJorgensen/KungFuFlash2/releases
13. C64 for MEGA65 cartridge documentation:
    - https://kugelblitz360.github.io/C64MEGA65DOCS/c64-cartridges.html
14. Turbo Chameleon:
    - https://wiki.icomp.de/wiki/Chameleon
15. Sidekick64:
    - https://github.com/frntc/Sidekick64
16. MiSTer C64 core:
    - https://github.com/MiSTer-devel/C64_MiSTer
17. Magic Desk 2 / read-only GMod3-compatible mode:
    - https://github.com/crystalct/MagicDesk2

## Maintenance rule

Cartridge compatibility is version-sensitive. When this document is updated:

1. record the exact emulator/core/firmware version;
2. distinguish virtual `.crt` loading from a physical cartridge port;
3. do not infer support merely from cartridge-image capacity;
4. treat “not listed” as unsupported unless source code or a repeatable test proves otherwise;
5. retain the GMod4 production-revision caveat until current VICE and current production hardware have been cross-validated.
