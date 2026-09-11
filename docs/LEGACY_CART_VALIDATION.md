# Cartridge methods: 0.7.5 validation

All 20 current logical demo cartridges were built with both methods in separate
external trees. A third control tree reproduced the published legacy identities.
Downloaded baseline archives, assembly, CRTs and monitor traces stayed outside
the Git checkout. The external source copier excludes Git directories and linked
worktree pointer files; a regression test covers the latter.

## Published baselines and exact legacy reproduction

The test downloaded the actual release assets from GitHub:

| Baseline | Release ZIP SHA-256 | Integrity checks |
|---|---|---|
| [v0.7.3](https://github.com/FlyingFathead/c64-3d-toolkit/releases/tag/v0.7.3) | `69089302c440f2a82128939aaf2e6710c0f8b0543d08945038584f18f535f3f2` | GitHub asset digest and all 66 indexed files |
| [v0.7.4](https://github.com/FlyingFathead/c64-3d-toolkit/releases/tag/v0.7.4) | `abdb0c9f9e48c685f5d6039ec22f0c0d6c02e0b8ed4fff312980842156c64705` | GitHub asset digest, published checksum file and all 60 indexed files |

**20/20 legacy control CRTs match their published v0.7.3 counterparts byte for
byte, including the CRT header.** No output bytes were masked, patched or
normalized to obtain these matches. The generator uses the original boot code,
ROMH packing and title conventions. The control builds use the recorded release
identities; production builds retain VERSION 0.7.5.

The v0.7.3 index contains 22 CRTs because it also retained two superseded menu
copies. For each of the 20 logical demo cases, the comparison selects its newest
available copy in that release. Two cases were inherited from 0.7.2:

| Published v0.7.3 artifact | Recorded build identity used by control |
|---|---|
| HiFi reel, `c643d-hifi-v0.7.2-hors-render-v2.crt` | 0.7.2 |
| Marbles, `marbles-hors-render-v2-16fps-force-bytes.crt` | 0.7.2 |

The initial all-0.7.3 control exposed Marbles' single version-digit difference.
Reassembling with the identity in the published manifest resolved it. These
per-cart VERSION overrides occur only in the external control tree and are
recorded in the JSON proof. They do not change the release version or executable
rendering code. See [per-file hashes and byte differences](benchmarks/legacy-0.7.5/checksums.json).

## Execution of actual 0.7.5 outputs

Tests used **PAL Linux VICE 3.10** and 64tass from the supplied tool bundle.

| Check | Standard | Legacy |
|---|---:|---:|
| Current demo CRTs built and executed | 20 | 20 |
| Completed picture checks, excluding separate colour tester | 49 | 49 |
| Completed pictures compared with exact pixel/colour oracles | 8,429 | 8,429 |
| Cold boots, Warp off/on, including bank-switch smoke cart | 42 | 42 |
| Colour tester keyboard checks | 96 | 96 |
| Normal PLAY ALL measurement windows | 93 | 93 |

Menu styles, HiFi transitions, the complete Marbles scene/ending and colour-test
looping passed with both methods. Each cold boot ran for two million emulated
cycles. All **84 cold boots** reached the limit without a JAM; Warp-off/on
startup pictures matched within each cartridge, and CRT hashes were unchanged.
Standard carts logged EAPI found. Legacy carts logged the expected missing-EAPI
warning while attaching as EasyFlash ID 32.

The eight preserved historical menu/HiFi CRTs also matched their bytes in the
v0.7.4 Git tree and passed 16 additional Warp-off/on cold boots. Together with
the current-method cases, this gives **100 cold boots without a JAM**.
[Historical checks](benchmarks/legacy-0.7.5/historical-cold.json) retain their hashes.

Four additional direct `c643d.py build` tests covered procedural object and
`.c643dscene` input with each method, followed by actual VICE picture checks.
The Python unit suite passed **212 tests**, with three optional historical tests
skipped and no failures. The complete release pipeline also passed alternate
VERSION, colour-control, directory-boundary and historical renderer gates.
The final source fingerprint is in the [performance chart](PERFORMANCE_COMPARISON.md).

## FPS and payload comparison

Measurements use normal PLAY ALL, three ten-second visits per entry, with seed 1
and VICE defaults. F5 exhibition mode is excluded. Baseline benchmark SHA-256s
were checked against the downloaded v0.7.4 cartridge bytes before comparison.

| Comparison with published v0.7.4 | Measured windows | Displayed-frame counts | Timing samples |
|---|---:|---|---|
| Standard Demo Cart 1 FPS/RAM and Demo Cart 2 | 93 | Identical in every window | All identical |
| Legacy Demo Cart 1 FPS/RAM | 72 | Identical in every window | All identical |
| Legacy Demo Cart 2 | 21 | Identical in every window | Tiny timing variation; maximum average-FPS difference 0.000279% |

There is **no detected FPS regression** in these tests. The small legacy Demo
Cart 2 timing variation is retained in the reports; it is not described as an
exact timing match. Both modes have identical renderer and frame bytes outside
bank 0 ROMH and the four relocated scene pages. For scenes, those four pages
match the original ROMH content byte for byte, and surrounding extension bytes
also match. All 20 packaged standard CRTs match the independently built A/B
standard set exactly.

[Complete A/B results](benchmarks/legacy-0.7.5/validation.json) ·
[Cold boots](benchmarks/legacy-0.7.5/cold-boots.json) ·
[Direct CLI tests](benchmarks/legacy-0.7.5/cli.json) ·
[Standard playback](benchmarks/legacy-0.7.5/standard-playback.json) ·
[Legacy playback](benchmarks/legacy-0.7.5/legacy-playback.json)

## Reproduction and limits

Run `python tools/verify_cart_methods.py --workspace ../c64-075-ab --vice-data /path/to/vice-data`
from the toolkit directory. Use a new external workspace and the documented
tool overrides. The default performs downloads, builds, exact legacy checks,
playback, cold boots and FPS comparisons. `--build-only` explicitly omits
emulator tests. The standalone [release guide](RELEASE_0.7.5.md) explains both
reproduction workflows.

These checks do not reproduce the reported Windows GUI Warp/settings sequence
or validate physical EasyFlash hardware or NTSC timing. Legacy mode remains an
explicit compatibility option with a warning; it does not silently replace a
failed standard build or disable physical-capacity and reset-vector checks.
