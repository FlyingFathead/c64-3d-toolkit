# Recovery checkpoint 004: complete

Date: 2026-09-14. Cumulative recovery update for the supplied v0.8.1 source tree.
VERSION remains 0.8.1. This records the verified recovery state incorporated
into v0.8.1; publication status is owned by the Git tag and GitHub release.

## Completed

- [x] Authored near-plane clipping for edges and occluding triangles.
- [x] Viewport clipping, source colours and original topology retained.
- [x] Fully invisible samples preserved, including consecutive blank frames and reappearance.
- [x] One clipping summary; `--ignore-warnings` reaches every scene/export backend.
- [x] Blender `linear`/`srgb` material interpretation; default `linear` retained.
- [x] INI default, interactive chooser, `configure` command and direct configuration argument.
- [x] `--configure-blender-color-space srgb` and `linear` save without prompting/building.
- [x] Explicit material indices and shared palette/perceptual mapper preserved.
- [x] Scene export files honour `--output-dir`.
- [x] CLI version/author banner, grouped build help and full `--help-all`.
- [x] Existing dependency checks and Linux/Windows installers retained.
- [x] Existing Demo Cart v3.1 controls, debounce, wraparound and stars-off defaults retained.
- [x] README, changelog, Blender pipeline/FAQ, configuration, CLI and release notes updated.
- [x] Numbered cumulative/full checkpoint workflow, checklists and SHA-256 records.
- [x] Public source/documentation exclusion scan and original-file preservation audit.

## Verification

| Check | Observed result |
| --- | --- |
| Baseline unit suite | 291 tests run: 288 passed; 3 optional historical-archive tests skipped |
| Final unit suite | 313 tests run: 310 passed; same 3 optional historical-archive tests skipped |
| Added tests | 9 camera, 11 colour/configuration, 2 checkpoint tests |
| Native Blender | 4.0.2; camera transforms/material IDs pass |
| Existing colour calibration | All 96 material indices match the supplied baseline in default linear mode |
| Existing scene records | Four scenes, first/middle/last samples, monochrome and source colours: byte-identical frame records |
| Camera-crossing GMod3 | 54 completed-frame checks; bitmap, colour and border match |
| Camera-crossing EasyFlash | 54 completed-frame checks; bitmap, colour, border and HUD match |
| Resident yunroll PRG, 256-pixel viewport | 54 completed-frame checks; bitmap/colour match across all three buffers |
| GMod3 displayed pictures | 300 PAL refreshes; all 17 samples, all three buffers, correct order, two-refresh holds |
| Invisible frames | Nine consecutive blank samples preserved in the original road diagnostic |
| Shipped release evidence audit | Existing GMod3 images, performance tables and recorded keyboard evidence pass |
| Original artifacts | All 71 original CRTs and all C64 assembly sources unchanged: 148 protected files |
| Original source-tree coverage | No original files missing |
| Updated documentation | Relative links checked; obsolete near-plane limitation removed |

The native tests used VICE 3.10 PAL and 64tass 1.59.3120. Existing release evidence
was checked for consistency; the full historical release/performance suite was
not rerun. Physical hardware, NTSC and Windows execution were not tested here.

[Native scene results](../examples/camera_crossing/evidence/validation.json),
[unit log](../examples/camera_crossing/evidence/unit-tests.txt),
[original binary/source hashes](../examples/camera_crossing/evidence/baseline-binaries.json),
[previous-scene record comparison](../examples/camera_crossing/evidence/baseline-preservation.json),
[Blender camera check](../examples/camera_crossing/camera-validation.json).

## Apply

Use the latest cumulative incremental directly over the supplied v0.8.1 tree.
Earlier checkpoints are superseded. From the checkout's parent directory:

```sh
unzip -o c64-3d-toolkit-v0.8.1-recovery-cp004-incremental.zip
cd c64-3d-toolkit
python3 -m unittest discover -s tests
```

The full recovery ZIP includes the complete restored tree, retaining original
build artifacts while omitting newly generated temporary build work. It can
reconstruct the source workspace in a fresh directory. The supplied archive
contains no `.git` directory, so these packages do not restore Git staging or
history. No commit, push, tag or release was performed.

## Pending

No requested recovery implementation remains pending. Optional hardware, NTSC
and Windows validation remain outside the checks performed in this environment.
See [checkpoint workflow](CHECKPOINTING.md) for the reusable packaging command.
