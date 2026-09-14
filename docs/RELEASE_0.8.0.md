# v0.8.0: GMod3 cartridge support added, switch to HORS-V4

HORS-V4 (`hors-v4`, also `hors-renderer-v4` and `hors-render-v4`) is the default conversion
renderer and uses GMod3 by default. It keeps the V3 picture core while adding
separate GMod3 processing, image packing, ROM access, paging and collection code.
Explicit older renderers retain their EasyFlash defaults. Existing EasyFlash
backend modules, assembly and released CRTs are preserved byte-for-byte.

## What fits

[Demo Cart v3.0: GMod3 All-in-One](../examples/gmod3_cart_demos/README.md) contains
all distinct released picture sequences: 58 entries, 6,474 pictures, six Dragon
variants, eight SAKU presentations and every one of Marbles' 640 pictures.
Equivalent source cartridges share an entry; differing sample counts remain.
There are exactly two new demo CRTs in `examples/gmod3_cart_demos/`:

| Edition | Entries | Capacity | Used | Free |
| --- | ---: | ---: | ---: | ---: |
| Interactive | 58 | 16,384 KiB | 13,448 KiB | 2,936 KiB |
| Automatic benchmark | 65 | 16,384 KiB | 13,416 KiB | 2,968 KiB |

The SPACE menu and each build report show cartridge type and allocated/free
KiB, including bank padding. Stars start off. RUN/STOP (Esc in VICE) or F1 returns to the menu, N/P selects
entries and C cycles Dragon shades. Shared SAKU controls cover colours,
direction, speed, HUD, help, star density/profile and exhibition. The benchmark
edition has no runtime input polling and advances after displaying every picture.
Original custom cartridge title/ending executables are not embedded; Marbles
uses the unified controls and loops its full picture sequence.

## Measured improvement

The new label in [the performance tables](PERFORMANCE_COMPARISON.md) is
`hors-v4-gmod3`. In 69 matched automatic workloads, it has **65 higher
averages, four ties and zero lower averages** than `hors-v3` on EasyFlash.
The increase ranges from 0 to **0.396819 FPS**. Mean active rendering cycles
also never increase. The four SAKU crawl variants tie; solid crawl reaches the PAL display limit.
This is a modest improvement, not a universal extra FPS.

Both backends receive identical encoded pictures, colours, sample order and
HUD settings, with stars and authored pacing disabled. Each test checks two
picture loops and then measures actual display flips over 4,800 PAL refreshes
(95.761 seconds), excluding warm-up. Marbles is compared in five equal
128-picture segments; its uninterrupted paged playback is verified separately.
The 192-picture metallic Pretzel uses its released indexed4 policy on both
backends to fit EasyFlash's preserved ROML allocator.

High, average and low FPS remain listed. Only winning averages are bold;
ties are marked at the displayed precision. Sande's models have separate
tables. The generator and a separate cell-by-cell winner audit validate the
current page. Historical comparison protocols and measured cartridge versions
remain identified rather than being relabelled as HORS-V4 results.

## Verification

[Release audit and original-file preservation](benchmarks/gmod3-release.json)
checks the final image hashes against the measured cartridges.
The [283-test Python suite](benchmarks/gmod3-unit-tests.txt) completed with
280 passes and three optional checks skipped.

- All 58 final interactive entries: complete picture loops, colours and all
  three buffers, then individually measured display FPS.
- All 65 automatic entries: final-picture drain, correct handoff, full wrap,
  soft and hard reset.
- SAKU: all 240 mode pictures, 48 colour combinations, HUD/speed keys, help
  pause/restore, light/full stars and exhibition; collection navigation and
  centered capacity text.
- Marbles: all five pages forward and reverse, full wrap and standalone paced
  640-picture scene playback.
- Default CLI: object, painted SVG and authored scene builds; standalone SPACE
  wait, help return and capacity layout. Short V4 GMod3/EasyFlash labels pass
  cold-boot UI and picture checks; the EasyFlash authored-scene fallback also
  passes. [Short-selector evidence and commands](benchmarks/gmod3-cli/short-labels/builds.json).
- Image validation: type 62, 64-byte v1.0 header, EXROM/GAME 0/1, normal 8 KiB
  startup, CBM80 vectors, complete bank sequence and raw-image round trip.
- Bank diagnostics: every bank at 2/4/8/16 MiB, high-bit boundaries, mapping,
  IRQ/NMI and reset. Absolute/indexed bank stores cost 4/5 CPU cycles; the
  GMod3 helper pair costs 40 cycles versus 60 for the matched EasyFlash helper.

Evidence: [matched comparisons](benchmarks/hors-v4-matched/results.json),
[interactive entries](benchmarks/gmod3-collection/interactive/results.json),
[sequence transitions](benchmarks/gmod3-sequence.json),
[features](benchmarks/gmod3-features/results.json),
[paging](benchmarks/gmod3-paging/results.json),
[bank diagnostics](benchmarks/gmod3-checkpoint1/results.json).

These are PAL VICE 3.10 measurements. Physical GMod3 hardware and NTSC remain
untested; no audio engine or flash-programming support is claimed. The supplied
EN25QH128A(2T) PDF describes the SPI flash chip, not the CRT header or a C64
bank-switch latency. See [GMod3 documentation and primary sources](GMOD3.md).

## Install and select hardware

Apply the incremental ZIP over the supplied 0.7.9 toolkit. From its parent:

```sh
# Run from the directory containing c64-3d-toolkit/
unzip -o c64-3d-toolkit-v0.8.0-incremental.zip
cd c64-3d-toolkit
python c643d.py --version
python c643d.py run-cart examples/gmod3_cart_demos/demo-cart-v3.0-gmod3-all-in-one.crt
```

The archive includes the `c64-3d-toolkit/` prefix. It contains additions and
changed files, not another copy of the original assets or toolchain. Keep the
existing examples tree: the collection rebuild reads those source CRTs/oracles.

```sh
# New default: HORS-V4 / GMod3.
python c643d.py build --shape torus --surface-fill metallic --interactive-cart
# HORS-V4 with EasyFlash.
python c643d.py build --renderer hors-v4-ef --shape torus --surface-fill metallic
# Preserved HORS-V3 / EasyFlash.
python c643d.py build --renderer hors-v3 --shape torus --surface-fill metallic
# Explicit capacity and hardware.
python c643d.py build --cart-type gmod3 --gmod3-size-mib 16 --shape cube
```

Universal preference example (`config/c643d.ini` or `--config PATH`):

```ini
[cartridge_defaults]
cart_type = gmod3
```

Values are `auto`, `easyflash`, `gmod3`. CLI hardware choices (`--cart-type` or a `hors-v4-ef` / `hors-v4-gmod3` suffix) win, then config,
then renderer default. `auto` preserves per-renderer defaults. The historical
`cart-demos` command keeps its EasyFlash comparison path. See
[configuration](CONFIGURATION.md) and [supported source limits](GMOD3.md).

## Rebuild and check

```sh
python -m unittest discover -s tests
python examples/gmod3_cart_demos/build.py --tass 64tass --cartconv cartconv
python tools/compare_gmod3_catalog.py --tass 64tass --cartconv cartconv --vice x64sc --vice-data /path/to/vice/data
python tools/report_gmod3_performance.py
python tools/report_gmod3_performance.py --check
python tools/verify_gmod3_release.py
```

The comparison command always rebuilds and measures; old JSON files are not
accepted as a cache for changed code. The report command checks all 69 cases
and independently checks winning cells. See each `verify_gmod3_*.py --help`
for complete per-entry, feature, sequence, startup and paging checks. Historical
`compare_renderers.py --check` fingerprints belong to their original release;
they are not rewritten to claim a fresh run of older renderer matrices.

## Publish from your checkout

After applying the update, inspect and commit the release files, then tag and
create the full source archive from that commit:

```sh
git diff --stat
git add VERSION CHANGELOG.md README.md config/c643d.ini.example config/gmod3.ini.example c64/gmod3 tools tests docs examples/README.md examples/gmod3_cart_demos
git commit -m "Release 0.8.0: GMod3 cartridge support added, switch to HORS-V4"
git tag -a v0.8.0 -m "c64-3d-toolkit 0.8.0"
git push origin HEAD
git push origin v0.8.0
git archive --format=zip --prefix=c64-3d-toolkit/ -o ../c64-3d-toolkit-v0.8.0.zip v0.8.0
gh release create v0.8.0 ../c64-3d-toolkit-v0.8.0.zip --title "v0.8.0: GMod3 cartridge support added, switch to HORS-V4" --notes-file docs/RELEASE_0.8.0.md
```

The delivered incremental ZIP has not committed, pushed or tagged your repository.
