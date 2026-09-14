# GMod3: implementation, capacity and measured behavior

GMod3 has an independent, read-only cartridge backend and a complete collection:
[Demo Cart v3.0: GMod3 All-in-One](../examples/gmod3_cart_demos/README.md).
It contains 58 entries and 6,474 stored pictures drawn from 48 released source
cartridges. Equivalent sequences with the same pacing share an entry; different
sample counts, colours and presentations remain distinct. No samples were
dropped to fit the flash.

| Image | Entries | Flash capacity | Allocated | Free |
| --- | ---: | ---: | ---: | ---: |
| Interactive collection | 58 | 16,384 KiB | 13,448 KiB | 2,936 KiB |
| Automatic benchmark collection | 65 | 16,384 KiB | 13,416 KiB | 2,968 KiB |

The automatic version exposes SAKU's eight presentations separately, producing
65 entries. Both versions contain the complete 640-picture Marbles sequence.
Allocation includes the boot bank, three runtime banks per entry, page
directories and all padding within allocated 8 KiB banks. Free means whole
unallocated banks, not unused bytes inside occupied banks. Each build prints
the current entry allocation and cumulative used/free space. The SPACE menu
centres the same total figures at rows 22 and 23. KiB fits the standard
40-column screen even at maximum capacity; no custom narrow font is needed.

## Renderer and cartridge are separate choices

Version 0.8.0 defaults to HORS-V4 (`hors-v4`, also `hors-renderer-v4` and
`hors-render-v4`) and GMod3. HORS-V4 retains the V3 picture core and adds the
independent GMod3 cartridge architecture. Explicit older renderer selections
retain EasyFlash defaults. The historical `cart-demos` comparison builder
retains its preserved V2 EasyFlash path. Select hardware with `--cart-type`,
or set a universal `[cartridge_defaults]` preference. See [configuration](CONFIGURATION.md)
and [the example config](../config/gmod3.ini.example).

```sh
python c643d.py build --cart-type gmod3 --shape torus --surface-fill metallic --interactive-cart
python examples/gmod3_cart_demos/build.py --tass 64tass --cartconv cartconv
python c643d.py run-cart --cart-type gmod3 examples/gmod3_cart_demos/demo-cart-v3.0-gmod3-all-in-one.crt
```

The GMod3 CLI accepts procedural objects, OBJ, painted/gradient SVG, Blender
exports and authored `.c643dscene` files. Objects use 1–255 pictures, with the
V3 surface encodings and optional interactive controls. Authored scenes use
automatic playback and retain all samples: up to 255 directly, or up to 1,024
in complete 128-picture pages. Unsupported partial long pages fail explicitly.
The collection also supports the full SAKU presentation set. Native EasyFlash
intro/ending programs and custom scene HUD programs require an explicit older
renderer/cartridge selection; they are not interpreted by GMod3. It never falls
back to another cartridge type or silently removes pictures. New GMod3
hardware code does not modify or temporarily patch an EasyFlash builder.

## Names and aliases

HORS stands for **Hyper Optimized Rendering Setup**. Short names are used on
screens and in charts; established long CLI spellings remain supported.

| CLI selector | Equivalent long selector | Default cartridge |
| --- | --- | --- |
| `hors-v1` | `hors-render-v1`, `hors-renderer-v1` | EasyFlash |
| `hors-v2` | `hors-render-v2`, `hors-renderer-v2` | EasyFlash |
| `hors-v3` | `hors-renderer-v3`, `hors-render-v3` | EasyFlash |
| `hors-v4` | `hors-renderer-v4`, `hors-render-v4` | GMod3 |
| `hors-v4-gmod3` | `hors-v4 --cart-type gmod3` | Explicit GMod3 |
| `hors-v4-ef` | `hors-v4 --cart-type easyflash` | Explicit EasyFlash |

V1/V2 `-scene` aliases remain available. A cartridge suffix overrides the
universal config preference. A conflicting explicit `--cart-type` is rejected.
HORS-V4/EasyFlash runs the preserved V3 implementation through a separate
facade. Only its newly generated startup renderer text and manifest identity
are relabelled; its mapper, drawing code, picture data and addresses stay the
same. Existing EasyFlash backend files and released CRTs are untouched.
Raw benchmark IDs remain stable provenance; chart labels use the short names.

## Compatibility

The complete collection is verified in **PAL VICE 3.10**. A physical C64/C128
needs a cartridge device implementing the GMod3 mapper and enough flash for
this 16 MiB image. A CRT file cannot run directly from an ordinary disk drive.
The manufacturer describes C64/C128 compatibility but also says GMod3 was
not mass-produced and was superseded by GMod4. This is not a claim of broad
availability or GMod4 compatibility. [iComp GMod3 specification](https://wiki.icomp.de/wiki/GMod3).

Do not assume every CRT loader supports type 62. The Ultimate documentation's
[supported cartridge list](https://1541u-documentation.readthedocs.io/en/latest/howto/cartridges.html)
does not list GMod3; its [3.15 release notes](https://1541u-documentation.readthedocs.io/en/latest/howto/release_3.15.html)
document a 4 MiB cartridge ROM area for U64/U64-II, smaller than this image.
Those devices were not tested here. Consult your device's mapper and size limits.

Choose `--renderer hors-v4-ef` or `--renderer hors-v4 --cart-type easyflash`
for EasyFlash builds, or use the existing individual EasyFlash demo downloads.
The combined 16 MiB collection cannot fit EasyFlash's 1 MiB capacity; changing
the selector does not convert this all-in-one CRT into an EasyFlash image.

## What the image validator checks

The [VICE CRT specification, GMod3 section](https://vice-emu.sourceforge.io/vice_17.html)
defines type 62, the four supported capacities and the normal 8 KiB startup
mapping. The [manufacturer's register specification](https://wiki.icomp.de/wiki/GMod3)
defines the hardware behavior. These are separate from the flash-chip data
sheet.

| Field | Generated value / check |
| --- | --- |
| CRT signature | `C64 CARTRIDGE   `, exactly 16 bytes |
| Header length / version | 64 bytes / `0x0100` |
| Hardware type | 62 (`0x003e`), GMod3 |
| EXROM / GAME | 0 / 1, normal 8 KiB game mapping |
| Reserved bytes 26–31 | All zero |
| CHIP packet | 16-byte header plus 8,192-byte payload |
| CHIP load address | `$8000` |
| CHIP bank numbers | Complete, unique, contiguous 0–2047 for 16 MiB |
| Bank-zero startup | Valid cold/warm vectors and CBM80 signature |
| Raw-image equivalence | SHA-256 of reconstructed CHIP payloads equals the full input image |

The writer uses VICE `cartconv -t gmod3`. Generated CHIP records use flash
type 2; the inspector also accepts ROM type 0, as allowed by the documented
format examples. No private CRT extension or nonstandard startup mode is
used. Every image contains the full selected flash capacity, including erased
`$ff` bytes in unused banks. A 16 MiB CRT is 16,810,048 bytes: 16,777,216 flash
bytes plus the 64-byte CRT header and 2,048 sixteen-byte CHIP headers. Container
overhead is not charged against cartridge flash capacity.

## Banking and RAM ownership

For bank `N`, write `N & 255` to `$de00 + (N >> 8)`. Address bits select the
upper three bank bits; these are not eight independently retained contexts.
Read `$de00` and `$de08` for low/high bank readback. Reset selects bank zero.
Supported capacities are 2, 4, 8 and 16 MiB, or 256, 512, 1,024 and 2,048 banks.

The renderer runs from RAM. Its stream reader selects a complete 11-bit bank
once per fetch, uses `$01=$37` while reading ROM and `$01=$35` for normal RAM
rendering. Masked sections are bounded. It retains the V3 literal bitmap spans,
shared colour plans, three VIC buffers and per-buffer clear metadata. There is
no ROM-to-VIC DMA: pictures still have to be read and drawn by the 6510.

| Module / region | Responsibility |
| --- | --- |
| `tools/c643d/gmod3_image.py` | Capacity, bank arithmetic, CRT validation and conversion |
| `gmod3_cli.py`, `gmod3_surface.py`, `gmod3_scene.py`, `gmod3_options.py` | GMod3-owned CLI processing and source conversion |
| `hors_v4.py`, `cartridge_defaults.py` | Versioned renderer entry point and explicit/config/default selection |
| `gmod3_stream.py`, `gmod3_v3.py` | Independent packer, directory and V3 runtime assembly |
| `gmod3_catalog.py`, `gmod3_collection.py` | Read-only released-picture inventory, collection layout and menu |
| `gmod3_paging.py` | 128-picture directory pages and authored PAL pacing |
| `c64/gmod3/` | Independent bootstrap, ROM reader, renderer, collection and diagnostic sources |
| RAM `$0334..$03ff` | Collection loader, safe while ROM/CPU-port mapping changes |
| RAM `$a000..$a0ff` | High bank bytes of the active picture directory |
| RAM `$a100..$bfff` | Resident collection menu and navigation |
| RAM `$c000..$c3ff` | Interactive help |
| RAM `$c400..$c5ff` | Optional long-sequence pager and pacing state |
| RAM `$c600..$c6ff` | Automatic collection final-picture drain before entry reload |

Bank-zero code jumps to the low-RAM trampoline before hiding ROM. The loader
masks CIA/VIC interrupt sources, reloads the chosen runtime, installs directory
high bytes and enters the normal renderer startup. The 640-picture Marbles
sequence uses five complete 128-picture directory pages. Buffer clearing
uses cached metadata, so crossing a page does not invalidate an older buffer.

## Timing and bottlenecks

See [every scene's performance comparison](PERFORMANCE_COMPARISON.md) for
measured average display FPS, separate from active rendering cycles. All
reported timing is PAL VICE 3.10 emulated C64 time, not host execution speed.
The initial bank diagnostics are preserved in
[the raw probe report](benchmarks/gmod3-checkpoint1/results.json).

| Diagnostic | Measured cost |
| --- | ---: |
| Absolute `STA $de00` | 4 CPU cycles |
| Indexed `STA $de00,Y` | 5 CPU cycles |
| GMod3 map-in/map-out pair, including JSR/RTS | 40 cycles |
| Equivalent EasyFlash helper pair | 60 cycles |
| 256-byte copy, display disabled | 2,623 cycles for RAM, EasyFlash ROM and GMod3 ROM |

The improvement comes from simpler mapping work around a fetch. A larger
flash does not increase 6510 clock speed. Drawing spans, recycling bitmap
buffers and updating screen colours remain the main costs. VIC bad lines and
sprite DMA reduce the CPU time available; the copy test rises to roughly
2,880 cycles with the display active and roughly 3,320 with eight sprites.
These phase-dependent observations are not universal fixed copy costs.

The EN25QH128A(2T) PDF is the **128-Mbit SPI flash component data sheet**, not a
CRT header specification. 128 Mbit means 16 MiB. Its 256-byte programming
pages, 4 KiB erase sectors and SPI clock/program/erase timings concern flash
transactions. They do not imply a C64 bank-switch delay or a renderer FPS gain.
Normal playback never enables SPI bitbang mode, erases flash or programs it.

## Verification and limits

The diagnostic cartridge checks every bank at every supported capacity,
including 255/256, 511/512 and 1023/1024 boundaries. Separate tests cover bank
readback, `$35/$36/$37` RAM visibility, IRQ/NMI vector override and dirty soft
and hard reset. The demos leave vector override and SPI bitbang disabled.

The collection verifier checks complete picture loops against independent
source oracles in all three buffers, then measures actual display-slot
transitions. SAKU receives additional checks for all eight presentations,
foreground/background remapping, help pause/restore, HUD and speed controls,
light/full starfields and exhibition playback. The automatic collection is
checked through every entry transition, including the final displayed picture
before each reload and the final wrap back to SAKU.

The collection ports released pictures and timing into its interactive player.
Original cartridge-specific native title/ending programs are not embedded as
executable sub-cartridges. In particular, Marbles loops its entire authored
picture sequence under the new collection controls. `RUN/STOP` (Esc in VICE) or `F1` returns to the menu.
`Shift+H` opens help.

Physical GMod3 hardware and NTSC remain untested. The manufacturer's page says
GMod3 was not mass-produced and was superseded by GMod4. This implementation
does not claim GMod4 compatibility. Audio mixing/streaming is future work:
the supplied A/V findings motivate bounded bank ownership and RAM staging,
but no audio ISR or flash writer is introduced by this change.

## Sources

- [iComp GMod3 hardware/register specification](https://wiki.icomp.de/wiki/GMod3)
- [iComp OEM GMod3 repository](https://gitlab.icomp.de/icomp-oem/gmod3)
- [EN25QH128A(2T) flash data sheet in the repository](https://gitlab.icomp.de/icomp-oem/gmod3/-/blob/main/docs/EN25QH128A(2T).pdf?ref_type=heads)
- [VICE CRT file-format specification, section 17.14.3.63](https://vice-emu.sourceforge.io/vice_17.html)
- [Cartridge A/V findings supplied for this project](C64_CARTRIDGE_AV_FINDINGS.md)
- [GMod backend research and future GMod4 work](GMOD_BACKENDS.md)

Manufacturer example code has not been incorporated. The backend is written
from the register/format specification and the toolkit's own existing code.
