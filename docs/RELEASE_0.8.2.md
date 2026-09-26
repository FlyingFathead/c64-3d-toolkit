# v0.8.2: Renderer contests and V5 candidates

This release makes EasyFlash the default for new HORS-V4 builds and adds a
measured way to choose a renderer. GMod3 stays available explicitly; GMod4
remains on the roadmap. All existing cartridge binaries are preserved.

## Choose by measurement

`--renderer-contest` builds and verifies multiple pipelines against fixed complete
pictures, then ranks average displayed FPS with P95/worst holds and cart size.
Native paced scenes and uncapped original cores have separate rankings. Capacity
limits are N/A with reasons; errors remain FAIL. Winning CRTs are labelled in
their filenames. The command does not change your global renderer preference.

```sh
python3 c643d.py build --scene scene.c643dscene \
  --renderer-contest --contest-out ../scene-contest \
  --contest-vice-data /usr/local/share/vice --contest-capture
```

[Contest/configuration guide](OPTIMIZER_PROFILER.md) ·
[Public corpus](PUBLIC_BENCHMARKS.md) · [Performance chart](PERFORMANCE_COMPARISON.md)

## V5 candidates

- `hors-v5-c1` names the existing experimental V5. `hors-v5` and `hors-v5-ef` keep selecting c1.
- `hors-v5-c2` combines V5 clearing with host-selected run/shared colour transport.
- HORS-V4/EasyFlash remains the default; every prior renderer remains available.

C2 improves the two SAKU logo-only benchmarks and ties c1 on the other fourteen
public inputs, with both FPS/RAM preferences. V2 still narrowly leads solid SAKU.
The selector is a useful heuristic, not a claim that the newest renderer always
wins. C2 currently targets standalone object/scene builds with literal colours;
interactive/background-effects and unsupported colour encodings are rejected.

Palette conversion, `linear|srgb` interpretation and default overlap policy are
unchanged. No conflicting road fragments are suppressed by default. Pixel checks
confirm reproduction of encoded pictures; they do not certify the original
material mapping or remove the hardware's colour-cell limitations.

## Release validation

The fresh public family matrix covers HORS-V1/V2/V3/V4 EF/V5-c1/V5-c2, each with
FPS/RAM preference, on 16 fixed inputs: **190 passes, two capacity N/As, zero
failures**, with **21,322 completed-picture checks**. HORS-V1 Dragon wireframe
requires a 10,492-byte frame block, exceeding its 8,192-byte staging buffer.
The original full-history chart remains available alongside these measurements.

The source audit protects 153 files from the supplied v0.8.1 baseline, including
73 CRTs, 77 assembly files, the geometry/palette pipeline and Blender exporter.
The camera-crossing regression explicitly checks GMod3, EasyFlash and resident
output. Fresh default/c1/c2 object playback and V5 build-screen checks accompany
**346 unit tests (eight skipped)**. The native checks verify 243 completed
pictures across all three buffers, plus 300 GMod3 display refreshes.
[Validation record](benchmarks/release-0.8.2/validation.json).

All timings here are PAL VICE results. Physical C64 and NTSC performance remain
unmeasured. Private artwork and raw private results are excluded from the source
and public release assets.

## Reproduce

```sh
bash RUN-CHECKS.sh ../c64-082-checks
```

Set `VICE`, `TASS`, `CARTCONV` and `VICE_DATA` if needed. Use a new output directory.
This checks saved full-matrix provenance, runs the unit suite and rebuilds native
smoke cases. It does not overwrite historical examples or the performance chart.
For a fresh full matrix:

```sh
python3 tools/benchmark_repo_examples.py --out ../c64-082-family \
  --methods yunroll-cart-v10 hors-render-v2 hors-renderer-v3 hors-v4-ef hors-v5-c1 hors-v5-c2 \
  --workers 3 --vice-data /usr/local/share/vice
```

`tools/compile_release.py --workspace ../c64-082-release` validates and packages
an isolated source copy. Existing archives are never overwritten. For this
release, `--install` has nothing to copy because historical examples are retained.
The external release helper performs publishing from an explicitly reviewed file
list; it refuses a changed source snapshot or an existing release tag.

[Full family results](RELEASE_0.8.2_PERFORMANCE.md) · [Changelog](../CHANGELOG.md)
