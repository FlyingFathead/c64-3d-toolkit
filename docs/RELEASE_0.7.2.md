# Compile, validate and install 0.7.2

Linux checkout: `~/NeuralNetwork/c64-3d-toolkit`. Downloads and external results:
`~/NeuralNetwork/`. Stable renderer name: `hors-render-v2`.

## Apply the supplied complete or overlay ZIP

Both archives have repository-relative paths. Choose one; the overlay contains
only added/changed files. ZIP extraction cannot remove old files, so run cleanup
after extraction. Cleanup checks all replacement hashes first and preserves
local old files outside the checkout.

```bash
cd ~/NeuralNetwork
unzip -o c64-3d-toolkit-0.7.2-hors-v2-overlay.zip -d c64-3d-toolkit
cd c64-3d-toolkit
python3 tools/cleanup_examples.py --apply
```

Use `c64-3d-toolkit-0.7.2-hors-v2-complete.zip` in the same command for the complete
source and prebuilt release. No additional VICE launch-fix ZIP is required.

The archive directory is `../c64-3d-toolkit-history/pre-hors-v2/`. Known v1/beta
CRTs and their companions, plus old resident PRG previews, move there. Unknown
custom files are not selected. Differing local copies get distinct hash-based
paths. Compact regression fixtures remain under assets; runnable copies needed
by legacy tests are reconstructed only in ignored build storage. Source models,
Blender files and all historical renderer implementations remain in the repo.

## One-command release build

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
JOBS=3 VICE_DATA=/usr/local/share/vice bash COMPILE-RELEASE.sh \
  --workspace ../c64-072-release-build
```

The new workspace contains an isolated source snapshot, logs, built cartridges,
verification reports, the full regenerated chart and a complete ZIP. Nothing is
installed into your checkout by default. Add `--install` to copy the validated
release back and archive old examples after all checks pass. Use a new workspace
name for each run; failures preserve logs and stop packaging/installation.

Optional: `--baseline-zip ../c64-3d-toolkit-2026-09-10_024143.zip` also produces an
overlay relative to that exact source snapshot. `PYTHON`, `TASS`, `CARTCONV`,
`VICE`, `VICE_DATA` and `JOBS` can override the local tool commands/settings.

The build reads VERSION rather than requiring a fixed output version filename.
A future renderer needs explicit integration and tests; changing a version string
alone never substitutes an untested drawing implementation.

## Build or test individual parts

```bash
python3 tools/build_hors_v2_examples.py --tass 64tass --cartconv cartconv
python3 tools/build_demo_cart_v2.py --renderer hors-render-v2
python3 tools/index_release_examples.py
JOBS=3 VICE_DATA=/usr/local/share/vice bash RUN-0.7.2-CHECKS.sh \
  ../c64-072-local-tests-stable
```

The complete release pipeline additionally checks every shipped stable example,
all samples of Marbles plus its complete native ending, and HiFi reel transitions.
The test launcher supplies clean VICE defaults and retains individual emulator
logs. The ending verifier shares the SPACE-start helper used by picture tests.

Performance charts come from normal PLAY ALL using the frozen inputs. All older released rows remain; the unreleased beta is excluded. Stable v2
has FPS/RAM rows, and Demo Cart 2.0 has a separate seven-scene section. The chart fingerprint must
match the packaged source. No release command commits, tags or pushes Git.

Optional tests against external historical binary archives report skips when
those archives are absent from the isolated workspace. They do not skip the
canonical renderer matrix or the current v2 picture checks. Check `unit.log`
for the exact test/skip totals.

## One version source

Edit root `VERSION` for a toolkit version bump. Python imports it at startup;
Windows setup reads the same file. New menu/build/thanks text and versioned
cartridge filenames use that value. Assembly templates stay preserved: the
builder stamps a generated copy of any old title text before assembly.

`RUN-CHECKS.sh` is the generic check entry point. `RUN-0.7.2-CHECKS.sh` remains
a compatibility wrapper for the earlier instructions.

The release gate builds small v1 and v2 carts with an alternate VERSION (normally
9.8.7) in a temporary checkout. VICE checks their build screens, all three menu
styles and thanks screens against the cartridge manifests. Stable headers alone
are insufficient: their actual version must match. The alternate carts never
enter the shipped examples.
