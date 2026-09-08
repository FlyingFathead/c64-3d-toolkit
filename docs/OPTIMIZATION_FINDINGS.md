# Optimization findings and process

Working name: **hors-optimizer-v1**. hors-render-v1 now promotes the tested byte-first policy into a separate build target. Automatic multi-renderer selection remains future work. Historical implementations and shipped cartridges remain intact.

## Controlled experiment

The supplied byte-policy-01 bundle passed SHA-256 verification. All four policies report completed with both preferences, pixel checks and stage profiles. Normal PLAY ALL uses three loops of ten seconds per demo, PAL clock 985248 Hz, seed 1, and no FPS locking. The eight candidate CRT hashes match our initial local builds.

Baseline chooses byte spans only when their complete encoded block is smaller than vectors. bytes125 and bytes150 permit blocks up to 125% and 150% of vector size. force-bytes selects byte spans subject to existing capacity constraints. Each policy is built in an isolated copy.

## Confirmed FPS preference results

| Demo | Baseline avg FPS | bytes125 | bytes150 | force-bytes | Best average policy |
| --- | ---: | ---: | ---: | ---: | --- |
| CUBE | 26.820 | 26.820 | 26.820 | 27.423 | force-bytes |
| FALLING CUBES | 13.862 | 13.862 | 14.562 | 19.688 | force-bytes |
| HORSE HEAD | 13.862 | 13.963 | 16.474 | 27.422 | force-bytes |
| HORSE HEAD HIFI | 10.246 | 11.049 | 13.158 | 20.693 | force-bytes |
| SPACE HORSE CRAWL | 23.505 | 28.829 | 35.058 | 35.559 | force-bytes |
| SPACE HORSE SPIN | 10.748 | 10.748 | 11.853 | 17.579 | force-bytes |
| SPHERE | 14.671 | 14.671 | 14.671 | 15.871 | force-bytes |
| SUNFLOWER COLOR | 10.547 | 11.451 | 13.460 | 19.991 | force-bytes |
| SUNFLOWER TORUS | 12.154 | 13.259 | 15.268 | 27.122 | force-bytes |
| SUNFLOWER TORUS HIFI | 14.465 | 19.889 | 19.889 | 19.889 | bytes125 |
| TORUS | 13.460 | 13.460 | 13.460 | 16.072 | force-bytes |
| TORUS DENSE | 12.154 | 12.154 | 12.154 | 15.771 | force-bytes |

## Capacity tradeoff

| Policy | Whole-menu CRT bytes | Represented 8 KiB regions | Unrepresented flash bytes |
| --- | ---: | ---: | ---: |
| baseline | 771,616 | 94 | 278,528 |
| bytes125 | 779,824 | 95 | 270,336 |
| bytes150 | 796,240 | 97 | 253,952 |
| force-bytes | 985,024 | 120 | 65,536 |

These are complete twelve-demo cart sizes. Each policy fits the current EasyFlash target. Unrepresented regions are not an allocator guarantee: reserved locations and fragmentation still matter. Internal padding is separate. No additional free runtime RAM or music budget is claimed. See [capacity accounting](CARTRIDGE_CAPACITY.md).

## Interpretation and next decisions

The size-only encoder rule leaves substantial performance available on several demos. More ROM can buy faster rendering without reducing geometry, colours or samples. The best policy still depends on the workload; comparable rounded FPS can make the smaller candidate preferable. Low FPS and per-frame costs must accompany average-FPS decisions.

Earlier resident comparisons identified five yunroll wins over V9 in the pilot: Torus, Torus Dense, Cube, Sphere and Falling Cubes. Resident storage and streaming have different overheads; fitting in RAM is a feasibility condition, not by itself a proven explanation of the timing difference.

The stage-profile correlation that motivated this experiment was that vector-encoded HiFi frames were much slower on average than byte-encoded frames. Those were different orientations, so that correlation was not a same-frame causal result. Candidate profiles now include per-frame encodings and byte sizes for paired analysis.

Next: evaluate per-frame speed versus added bytes, then build and validate a combined candidate. Independently winning policies do not prove a combined renderer is correct or capacity-safe. Broader authored-scene coverage, music integration and GMod backends remain future work.

## Reproduction and documentation rules

Use the [experiment instructions](V10_TESTING.md). Keep raw builds and traces in ignored directories. For each iteration record the hypothesis, controlled inputs, correctness checks, measured outcome, resource tradeoff and decision. Keep workstation details out of tracked reports. Preserve old algorithms and references; distinguish emulator validation from physical-hardware testing.

## Authored Marbles: local one-repeat validation

All 16 combinations (four policies, clean/HUD, FPS/RAM) passed pixel verification, one full stage-profile pass, and separate full ending verification. These are one-repeat local measurements; the supplied runner defaults to three repeats for confirmation. Scene timing retains original pacing and all 200 samples. Render cost excludes the story introduction and ending.

| Policy | Clean/FPS CRT bytes | Mean render cycles | Worst render cycles |
| --- | ---: | ---: | ---: |
| baseline | 303,760 | 78,073 | 280,843 |
| bytes125 | 320,176 | 61,162 | 106,462 |
| bytes150 | 328,384 | 59,282 | 106,461 |
| force-bytes | 344,800 | 57,446 | 106,461 |

Marbles fits as a standalone EasyFlash cartridge with every tested policy. This does not establish that it fits alongside the full twelve-demo menu in one cartridge. The scene remains a separate artifact. Optional replication commands are in [hors-render-v1 testing](V10_TESTING.md).

## hors-render-v1 integration and confirmed Marbles repeats

The user-supplied `marbles-policy-01` checksum was verified. All 16 combinations completed three repeats. Clean FPS-preference mean render cycles were 78,073 baseline, 61,162 bytes125, 59,282 bytes150 and 57,446 force-bytes. Baseline exceeded its authored budget in 24/600 observations; each candidate had zero. These tests preserve the 200-picture export's playback pacing. They do not prove 20 or 25 FPS sustained.

hors-render-v1 selects direct byte spans whenever the encoded picture fits 8 KiB, with a vector fallback for larger pictures. Whole-cartridge overflow remains a hard error. The fixed policy was chosen for a clear, reproducible first implementation; a budget-aware per-demo selector is still future work.

Built hors-render-v1 carts passed pixel checks, menu PLAY ALL controls and native Marbles endings in PAL VICE. The 200-sample clean max-speed Marbles diagnostic measured about 16.98 profiler-interval FPS and 11.78 seconds from scene start to ending. This is accelerated playback of the old samples. The fresh Blender export target is a separate experiment: 25 FPS needs 1,000 samples over the original source's 40 seconds; 20 FPS needs 800. Fresh export builds and music coexistence remain unverified at this patch's delivery.

## Dense Blender export findings

In supplied run marbles-blender-01, 25 FPS successfully exported and compiled 1,000 integer samples, but force-byte packing exhausted EasyFlash at sample 750. The 20 FPS run exported 800 samples but the compiler rejected a negative-depth vertex at source time 404.75 (logged as frame 404). These are separate capacity and fractional-geometry issues, not evidence of Blender crashing. The opt-in exporter now snaps to nearest integer source frames with explicit warnings. Recovery reuses the 25 FPS compilation and tests smaller encoding policies; fit and sustained rates remain to be measured.

## Dense Marbles: capacity and packing

The marbles-recovery-01 run failed to pack all eight 25/20 FPS candidates. At 25 FPS, force-bytes/bytes150/bytes125/baseline stopped at frame indices 750/792/807/833 of 1,000. At 20 FPS they stopped at 717/728/733/754 of 800. No candidate reached pixel or performance measurement, so these are capacity results only.

The recovery tester now compares sequential placement against best-fit decreasing whole-frame placement and chooses the one requiring fewer banks. Playback directory order is preserved, aliases share the same stored block, and blocks never cross an 8 KiB bank boundary. The 122-bank data allocation is unchanged. Logs report total encoded payload, both bank counts, padding, and a payload-only lower bound on capacity failures. This experiment changes no released renderer or builder mechanics. The saved integer-frame compilation is reused without Blender. Actual dense-scene fit and emulator verification remain pending the next local run.

The packing follow-up defaults to 25, 20, 19, 18, 17, 16 and 15 FPS (use `--fps` to choose a subset). Each target preserves the 40-second source interval using nearest integer samples; 19 through 15 FPS contain 760, 720, 680, 640 and 600 samples respectively. All four encoding policies are tested at each rate. Capacity fit and verified render throughput are separate results. The earlier approximately 17 FPS diagnostic measured the old 200-sample workload; it is neither a theoretical maximum nor a capacity-derived ceiling.

Optional automatic search: `--fps 25 --attempt-cart-auto-fit-fps --min-fps 15` tests every integer rate from 25 down to 15. It checks all policies at each rate and stops at the first rate with a verified candidate. If no policy passes and a failure is unrelated to capacity, it stops rather than hiding the error by lowering FPS. This selects a tested fitting target, not a guarantee that measured playback achieves that rate. The option currently belongs to `perf/recover_marbles.py`; regular release builds remain unchanged.

## Normal-speed playback is required

The 800-sample 20 FPS baseline cart fit after packing and matched all pixels, but its measured scene interval was 64.3066 seconds (12.4404 FPS), versus the intended 40 seconds. Capacity and pixel correctness did not establish normal-speed playback. The earlier automatic selection accepted this incorrectly.

Recovery selection now rejects a candidate if the profiler interval differs from 40 seconds by more than 0.25 seconds, or any measured render exceeds the shortest scheduled PAL hold. This conservative per-render check also rejects local slowdowns hidden by averages. It can reject a schedule that buffering could accommodate; it is an admission test, not a proof of optimal sampling. Automatic search continues to lower sample rates on timing or capacity rejection; build/verification errors remain fatal to the search. `--min-fps` defaults to 1. Every rate samples the same full source interval, with fewer frames, rather than accelerating the animation. Music remains untested.

Only accepted carts are copied to the run's `selected/` directory and included as `selected-carts/` in its bundle. Rejected builds remain in the ignored experiment directory. Intro/outro and all release renderer implementations are unchanged. Run with a new ID: `python perf/recover_marbles.py --id marbles-realtime-01 --from-run marbles-blender-01 --fps 20 --attempt-cart-auto-fit-fps --min-fps 1 --vice-data /path/to/vice-data`. No Blender invocation is needed. The highest normal-speed rate is pending measurement; 20 FPS is not promised.

## Accepted Marbles presentation and example cleanup

The 16 FPS force-bytes candidate passed 640 bitmap/colour comparisons and was visually accepted. Scene duration is 41.8226 seconds versus the original 40 seconds; the first 35 source seconds occupy about 35.01 seconds and the final five about 6.82 seconds. Acceptance is specific to this cartridge. The shortest-hold admission rule was overly conservative; general timing selection remains unresolved. No additional FPS sweep is required for this release candidate. Historical generated outputs move to example history subdirectories with regression references retained.

### Startup and cleanup correction

Marbles now waits for SPACE before the intro. Two startup instruction bytes change (DEX/BNE to CLC/BCC); animation payload and addresses stay unchanged. Canonical reference cartridges are preserved in history; modified local copies are archived separately by content hash. Cleanup tested twice against the latest submitted workspace; all 172 tests pass.

### Obsolete output removal

Keeping generated V2–V9 carts in tracked history directories did not meet the cleanup requirement. These outputs and the HiFi V2/V3 showcase now leave the checkout entirely; historical reproduction resolves an external sibling archive. Current 0.7.0 cartridges and source meshes remain in the repository.
