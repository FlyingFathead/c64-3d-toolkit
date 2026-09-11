# 0.7.5: optional legacy cartridge generation

Standard EasyFlash generation remains the default. This release adds the
explicit `--legacy-cart` compatibility method with a visible deprecation warning,
original boot code and original scene packing. It preserves the pre-0.7.4 use of
ROMH metadata space without the 1 KiB relocation. Physical capacity and reset
vectors remain protected. See [cartridge loading](CARTRIDGE_LOADING.md#legacy-compatibility-mode)
for commands, exact differences and limits.

Automatically named legacy files end in `-legacy.crt`. Manifests identify the
method, and legacy output is excluded from the current prebuilt release index.
All official prebuilt cartridges use standard generation. Default object/scene
boot programs now initialize `$01` before `$00` in the guide's documented order.

## Checksum-exact legacy verification

**Confirmed: 20 matching before/after SHA-256 pairs and zero differing bytes in
every legacy control CRT, including its header**, compared with files downloaded
from the actual v0.7.3 GitHub release. No bytes were masked or patched after
building. The controls use each published cart's recorded identity: 0.7.3 for
most carts, 0.7.2 for the inherited Marbles and HiFi carts. Actual 0.7.5 builds
retain their new version text and therefore are not promised to have old hashes.

The [per-file checksum report](benchmarks/legacy-0.7.5/checksums.json) contains
both hashes, file paths and the zero-byte-difference result for each comparison.
[Validation details](LEGACY_CART_VALIDATION.md) document the baseline downloads,
identity overrides, execution tests and the A/B reproduction command.

## Install

Save the release ZIP in the parent directory of the existing checkout, then:

```sh
unzip -o c64-3d-toolkit-v0.7.5.zip
cd c64-3d-toolkit
python tools/compare_renderers.py --check
python -m unittest discover -s tests -q
```

The ZIP root is `c64-3d-toolkit/`. Old versioned examples remain available as
historical references. Use the current links in the root README for this release.

## Rebuild

```sh
bash COMPILE-RELEASE.sh --workspace ../c64-075-release-build
```

The release pipeline rebuilds current examples and runs picture, menu, colour,
ending, alternate-version and renderer comparison gates. Tool paths can be passed
with `--tass`, `--cartconv`, `--vice` and `--vice-data`.

For the separate compatibility example set:

```sh
python tools/build_hors_v2_examples.py --legacy-cart
python tools/build_demo_cart_v2.py --legacy-cart
python tools/verify_hors_v2_release.py --legacy-cart --out ../c64-075-legacy-checks --vice-data /path/to/vice-data
```

[Validation results](LEGACY_CART_VALIDATION.md) record the tests performed for
this release. Linux PAL VICE tests do not establish physical hardware support or
reproduce the specific Windows GUI Warp/settings report. Frame kernels and
playback pacing have not been changed by the cartridge compatibility option.

## Full A/B reproduction against GitHub

```sh
python tools/verify_cart_methods.py --workspace ../c64-075-method-comparison --jobs 4 --vice-data /path/to/vice-data
```

Choose a new workspace outside the checkout. This downloads the published
v0.7.3/v0.7.4 release ZIPs, verifies GitHub asset digests, checks the separate
checksum file where supplied, and verifies every indexed file. All generated
cartridges, downloaded baselines, intermediate assembly and monitor reports
remain under the external workspace. Nothing is committed, tagged or pushed.

It builds all 20 current carts using both methods, plus a legacy control with
the published identities and original cartridge titles. The 0.7.3 release
carried forward Marbles and HiFi built as 0.7.2; their control builds use 0.7.2,
while the other control builds use 0.7.3. That control must match every
published v0.7.3 CRT SHA-256 exactly. This test identity is confined to the
external control tree; the distributed release retains VERSION 0.7.5.

Both current-version sets execute in VICE: complete-picture checks, menu and
HiFi transitions, native Marbles ending and colour controls. Each cart and the
bank-switch smoke test also cold-boot with Warp off/on. Production PLAY ALL
runs compare three ten-second visits per entry for Demo Cart 1 FPS/RAM and
Demo Cart 2 against each other and the published v0.7.4 benchmark records.
Raw checksum changes and timing differences are retained, not normalized away.
Only the old-identity control is expected to have the old release's whole-file
hashes. Runtime/frame-byte comparisons permit only the documented boot and
scene-relocation differences between the two current methods.

`--build-only` performs downloads, builds and byte comparisons without claiming
emulator verification. The default runs all checks. The tool uses the installed
64tass and VICE; differences in tool versions can affect exact reproduction.
