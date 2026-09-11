# Cartridge loading: 0.7.4 validation

The delivered source snapshot matched 0.7.3 commit
`78b197d38b3ffd6adf06f92d007a9487dd0050d5` byte for byte. All current release
cartridges were rebuilt for 0.7.4 and checked using PAL Linux VICE 3.10.

## FPS comparison with the supplied 0.7.3 carts

These measurements use normal PLAY ALL, three ten-second visits per entry.
F5 exhibition mode is excluded. The baseline report hashes were checked against
the actual cartridges in the supplied snapshot, and the new report hashes
against the delivered 0.7.4 cartridges. All picture-oracle hashes match.

| Workload | Windows | Displayed-frame counts | Timing |
| --- | ---: | --- | --- |
| Demo Cart 1, FPS | 36 | Identical in every window | Raw timing records identical |
| Demo Cart 1, RAM | 36 | Identical in every window | Raw timing records identical |
| Demo Cart 2.0 | 21 | Identical in every window | Largest average-FPS difference below 0.0003% |

No displayed-frame loss was measured across the 93 windows. Demo Cart 2's tiny
cycle differences are consistent with a changed initial raster/IRQ phase after
boot; they are not exactly identical timings. This is an interpretation of the
measurements, not proof of every possible emulator configuration.

The complete 26-job historical renderer matrix also passed. The regenerated
[performance chart](PERFORMANCE_COMPARISON.md) matches the delivered source
fingerprint. Raw production-cart comparisons are in
[fps-regression.json](benchmarks/loading-0.7.4/fps-regression.json).

## Loading and correctness

- All 20 current CRTs passed both Warp-off and Warp-on cold starts: 40 cases,
  two million cycles per case, identical startup pixels per cartridge and no
  CPU JAM. Every cart reported real EAPI and EasyFlash ID 32. Its file hash
  remained unchanged. The final HiFi filename/title was retested after fixing
  its name override.
- 49 playback checks verified 8,429 completed pictures across 19 regular,
  scene, menu and HiFi carts. The separately checked COLOR COMBO TEST brings
  the current release total to 20 carts.
- All menu styles, HiFi transitions, native Marbles ending and colour-control
  gates passed. An alternate-version build verified startup, menu and thanks
  labels for both renderer generations.
- Marbles' scene duration remained exactly 41.50340421903927 seconds. Eight
  ending-stage images and their storyboard match the snapshot cart pixel for
  pixel under the same VICE setup. Its startup includes the updated loader and
  version label; startup duration is not asserted identical.
- 208 Python tests ran with no failures; three optional historical-archive
  tests were skipped. The ROMH/frame-255 boundary test verified 531 frames,
  including the blank-frame case and rejection of an oversized payload.

The initial loading patch also passed monitor Warp off/on/off transitions with
soft resets and saved-settings/write-back preservation checks, as documented
in the earlier patch bundle.

The ending preview helper selects a chargen file from the installed VICE data.
For the image comparison, both cartridges were rendered in this same test
environment; previews from different ROM selections are not interchangeable.

[Validation summary](benchmarks/loading-0.7.4/validation.json) ·
[Cold-start checks](benchmarks/loading-0.7.4/cold-boot.json) ·
[Marbles comparison](benchmarks/loading-0.7.4/marbles-regression.json) ·
[Current cartridge hashes](../examples/release-index.json)

## Limits

The tester's VICE 3.10 Win64 GUI Warp sequence that produced a JAM at $F800 has
not been reproduced here. This release fixes confirmed loading gaps and does
not establish that sequence's cause. Physical EasyFlash hardware and NTSC
timing were not validated.
