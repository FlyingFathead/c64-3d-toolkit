# Dense Marbles recovery

The supplied marbles-blender-01 logs show that the 25 FPS export and all 1,000 geometry samples compiled, then EasyFlash packing exhausted capacity at sample 750. The 20 FPS export succeeded but its fractional source sample 404.75 contained a vertex behind the camera; the compiler rejected it before packing. The log prints source_frame as integer 404.

`python perf/recover_marbles.py --id marbles-recovery-01 --from-run marbles-blender-01 --vice-data /path/to/vice-data` reuses the saved 25 FPS .c643dscene and compiled oracle. It never launches Blender. At 20 FPS it selects 800 nearest integer-source samples over the same 40-second source interval. This avoids interpolated subframes; it is nearest-sample temporal resampling, not interpolation or a near-plane clipping implementation.

Both rates test force-bytes, bytes150, bytes125 and baseline policies in an isolated source copy. Builds, carts and labels stay under ignored comparison-tests/marbles-recovery/. Reports go under logs/ and are bundled even on worker failure. Passing means pixel checks and a stage profile passed, not music compatibility or a guaranteed sustained target rate. Geometry and previous renderers remain unchanged.

The saved checkpoint is required. Do not delete comparison-tests/blender-targets/marbles-blender-01 before running recovery. Public name: hors-render-v1; `yunroll-cart-v10-scene` remains the implementation compatibility identifier.

The regular output-FPS export pipeline now applies the same nearest-integer policy and emits a warning. The recovery runner remains useful for reusing the already-compiled checkpoint without launching Blender.

After applying the patch, `python perf/migrate_hors_names.py` archives unchanged V10-named example artifacts under ignored `comparison-tests/compatibility-v10/`. Locally modified files and V9 or earlier artifacts are retained.

## Packing follow-up

Run `python perf/recover_marbles.py --id marbles-packing-01 --from-run marbles-blender-01 --vice-data /path/to/vice-data` after installing the packing patch. Only this tester activates `perf/scene_packing.py` during scene assembly. The release builders and existing carts are unchanged. It tries all eight candidates, verifies successful builds, and bundles results even when none passes. Zero passing candidates now returns a nonzero exit status and prints an explicit total. A capacity-only pass is not a performance result.

The packing follow-up defaults to 25, 20, 19, 18, 17, 16 and 15 FPS (use `--fps` to choose a subset). Each target preserves the 40-second source interval using nearest integer samples; 19 through 15 FPS contain 760, 720, 680, 640 and 600 samples respectively. All four encoding policies are tested at each rate. Capacity fit and verified render throughput are separate results. The earlier approximately 17 FPS diagnostic measured the old 200-sample workload; it is neither a theoretical maximum nor a capacity-derived ceiling.

Optional automatic search: `--fps 25 --attempt-cart-auto-fit-fps --min-fps 15` tests every integer rate from 25 down to 15. It checks all policies at each rate and stops at the first rate with a verified candidate. If no policy passes and a failure is unrelated to capacity, it stops rather than hiding the error by lowering FPS. This selects a tested fitting target, not a guarantee that measured playback achieves that rate. The option currently belongs to `perf/recover_marbles.py`; regular release builds remain unchanged.

## Normal-speed playback is required

The 800-sample 20 FPS baseline cart fit after packing and matched all pixels, but its measured scene interval was 64.3066 seconds (12.4404 FPS), versus the intended 40 seconds. Capacity and pixel correctness did not establish normal-speed playback. The earlier automatic selection accepted this incorrectly.

Recovery selection now rejects a candidate if the profiler interval differs from 40 seconds by more than 0.25 seconds, or any measured render exceeds the shortest scheduled PAL hold. This conservative per-render check also rejects local slowdowns hidden by averages. It can reject a schedule that buffering could accommodate; it is an admission test, not a proof of optimal sampling. Automatic search continues to lower sample rates on timing or capacity rejection; build/verification errors remain fatal to the search. `--min-fps` defaults to 1. Every rate samples the same full source interval, with fewer frames, rather than accelerating the animation. Music remains untested.

Only accepted carts are copied to the run's `selected/` directory and included as `selected-carts/` in its bundle. Rejected builds remain in the ignored experiment directory. Intro/outro and all release renderer implementations are unchanged. Run with a new ID: `python perf/recover_marbles.py --id marbles-realtime-01 --from-run marbles-blender-01 --fps 20 --attempt-cart-auto-fit-fps --min-fps 1 --vice-data /path/to/vice-data`. No Blender invocation is needed. The highest normal-speed rate is pending measurement; 20 FPS is not promised.
