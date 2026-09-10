# Candidate experiments after V9

**0.7.2 update:** hors-render-v2 is the default. The measured scene search and full release compiler are available; see [stable v2](HORS_RENDER_V2.md) and [release automation](RELEASE_0.7.2.md). Older milestone descriptions below are retained as history.

Historical v0.7.0 status: hors-render-v1 was the production default; this runner remains an
independent comparison/experiment workflow. V9 IDs and the provenance notes
below describe its initial baseline, not the current release version. The full
profile follows the registered methods; production defaults and accepted
presentations are documented in [current builds](V10_TESTING.md).

This is an experimental host-side runner, not hors-render-v1 or an automatic production
renderer selector. It uses the existing verified comparison builders and normal
PLAY ALL harness. No previous renderer or shipped cartridge is modified.

The uploaded `c64-3d-toolkit-2026-09-08_195053.zip` matched all 453 tracked files
at GitHub commit `45806ccb851a81e894f04f6ece808b9be86437e0` exactly.

## Directory layout

- `perf/pipeline.py`: tracked orchestration and candidate ranking code.
- `logs/<run-id>/`: ignored run manifest, console log and JSON summary.
- `comparison-tests/runs/<run-id>/`: ignored isolated builds, raw measurements,
  cartridge files, correctness checks and detailed worker logs.
- `logs/<run-id>-results.zip`: compact bundle to send back for analysis.

Both output roots are automatically created. Logs are excluded from the underlying
builder's source snapshots, preventing recursive copies of past runs.

## Run locally

From the repository root, with 64tass, cartconv and x64sc on PATH:

```bash
python perf/pipeline.py plan --id v9-pilot-01
python perf/pipeline.py run --id v9-pilot-01 --profile pilot \
  --vice-data ~/NeuralNetwork/c64-tools/vice-data --workers 2
python perf/pipeline.py status --id v9-pilot-01
python perf/pipeline.py bundle --id v9-pilot-01
```

If executables are not on PATH, add these arguments to `run`:

```bash
--tass ~/NeuralNetwork/c64-tools/bin/64tass \
--cartconv ~/NeuralNetwork/c64-tools/bin/cartconv \
--vice ~/NeuralNetwork/c64-tools/bin/x64sc
```

Use your working VICE executable/data installation. The shared tool bundle may
require its library directory in LD_LIBRARY_PATH. The runner preserves your
process environment. It does not install tools or change machine configuration.

The pilot tests step, resident yunroll and V9 (both V9 preferences). It uses the
same frozen demo samples and three normal PLAY ALL loops as the full comparison.
The full profile tests every registered method/preference plus authored scenes:

```bash
python perf/pipeline.py run --id v9-full-01 --profile full \
  --vice-data ~/NeuralNetwork/c64-tools/vice-data --workers 2
python perf/pipeline.py bundle --id v9-full-01
```

Send `logs/v9-full-01-results.zip` and its `.sha256` file for analysis. The bundle
contains JSON evidence, provenance, summaries and logs, not compiled cartridges
or the source tree. Logs may contain your local file paths. Keep the generated
workspace locally if we need a failing cartridge later.

## Resume and new input

```bash
python perf/pipeline.py resume --id v9-full-01
```

Resume reuses completed measurements; it is NOT an independent repeat. For a
repeatability check, use a new ID with identical settings. Source/pipeline changes
require a fresh ID; the underlying tester also verifies tools and input provenance.
Do not run the same ID concurrently. A failed or interrupted run is not ranked.

`--current-demos` compiles the current demo registry once and tests all resulting
entries. Alternatively use `--reference-json <file>` with the existing
`c643d-vector-reference-v1` dataset format. All methods receive the same data.
Unsupported resident inputs remain N/A; frame/geometry reduction is forbidden.
A new renderer must first be integrated into the builders, adapters and `METHODS`
in `tools/compare_renderers.py`; it then participates in the full profile.
`--methods step yunroll-cart-v9` explicitly selects a subset.

## Recommendations and budgets

`summary.json` contains each animation/method/preference's high, average and low
FPS, frame count, observation time, source oracle hash, runtime/table/payload
sizes and whole comparison CRT size. It ranks normalized FPS (flips divided by measured seconds), reports numerical
ties and rejects mismatched source hashes or benchmark settings. Raw windows
must pass the original monitor cycle bounds; their durations need not be identical. The raw reports retain
picture validation, unsupported reasons and separate paced scene diagnostics.

`--stream-only` excludes resident backends from recommendations. It does not
remove their measurements, so the cost of choosing streaming remains visible.
`--max-cart-bytes N` filters recommendations by whole comparison cartridge size;
this is a ROM/container budget, NOT a per-demo size or free-RAM budget. Resident
reels may contain fewer supported demos; do not infer compression wins from that.

This first runner does not enforce a music RAM/IRQ budget, build hybrid frames,
or automatically select/ship a production cartridge. Its winners are candidates
for investigation. Equal quality and feasible memory layout come before FPS.

Optional `--max-fps N` and `--lock-to-min-fps` are forwarded to the comparison
builder. Both are off by default. Paced runs do not produce uncapped winner
recommendations. ONLY normal PLAY ALL supplies A/B throughput; F5 is excluded.

## Next experiments

1. Run the pilot, inspect correctness and repeatability, then collect the full
   baseline on the local toolchain. Host speed affects run duration; FPS is
   calculated from emulated C64 cycles, not host wall-clock speed. There is no
   assumed speed advantage for this hosted environment over your machine.
2. Add separate follow-up candidates beyond hors-render-v1 for direct-ROM vectors, execution-cost-based
   vector/byte selection and buffer-aware patches, one change at a time.
3. Record average and worst-frame behavior, payload sizes, allocated address
   ranges and interrupt/banking constraints. Reserve resources for music before
   considering resident data placement.
4. Validate a final combined cartridge against V9: isolated winners can lose
   after switching, placement and bank-boundary costs. Existing algorithms stay
   byte-exact; no default changes until the integrated candidate is verified.

## Historical framework baseline provenance

Adding this orchestration runner does not change benchmark kernels or workload.
The only fingerprinted edits are ignoring `/logs/` and excluding it from source
snapshot copying. The existing chart retains its measurements and records that
hygiene-only provenance transition. Pipeline code has an additional independent
hash in every run manifest. Future candidate or measurement changes require
fresh runs; this note does not authorize reusing stale performance numbers.

## Second-terminal live viewer

While a run is active, open another terminal in the same repository:

```bash
python perf/watch.py --id v9-pilot-01
```

The display refreshes every two seconds. It reads JSON and worker-log tails,
shows per-demo leaders with high/average/low FPS and CRT bytes, and marks leaders
provisional while correctness checks or other candidates are pending. Benchmark
numbers become available when each method's timed run finishes, not on every
emulated frame. Failed/partial JSON writes are ignored until readable.

For machine-readable snapshots:

```bash
python perf/watch.py --id v9-pilot-01 --json > logs/v9-pilot-01/live.jsonl
```

Use `--once` for one snapshot. Ctrl-C stops the viewer without stopping the
benchmark. Completed/failed/interrupted runs display their last state and exit.
A forcibly killed runner can leave a stale `running` manifest; check its process
and resume the run rather than treating that status as proof it is still active.

## Towards automatic search

The next search layer should enumerate bounded, explicitly implemented candidates
rather than mutate old assembly arbitrarily. Reject infeasible memory maps and
bank layouts first, then verify rendered images, measure, and keep non-dominated
choices across speed, slow-frame behavior and resource use. Candidate identity
must include its parameters, input hash, source hash and toolchain. Reuse cached
results only for an exact identity. Budget the search by candidates or time.

This release of the runner evaluates existing methods, reports winners, supports
streaming/CRT-budget recommendation filters and collects evidence for analysis.
It does not yet explore arbitrary memory layouts or generate new instruction
sequences. A future integrated renderer needs full-cartridge validation after
selection, including music/IRQ tests when a player is introduced.

## Trace where time is spent

After an uncapped run completes, profile one candidate's menu entries:

```bash
python perf/stages.py --id v9-pilot-01 --method yunroll-cart-v9 --entry 0 1 2
```

Omit `--entry` for every entry; add `--ram` for the RAM variant. Entry indices
refer to that candidate's built menu, which may omit unsupported datasets.
The command prints each entry name before running and writes stage-cycle JSON
under `logs/<run-id>/stages/`. Run `bundle` after profiling to include it.

Stages include fetching, recycling/clearing, drawing, colours where applicable,
and publishing/waiting. A combined queue-wait/lookup stage is not wholly CPU
work. Elapsed stage costs include VIC/IRQ effects; the largest non-wait stage is
a target for investigation, not proof that eliminating it will translate directly
to FPS. Re-profile after each change because the bottleneck can move.

Profiles require the preserved method's supported labels. Missing stage labels
are explicitly reported as unsupported; no invented timings or modifications to
historical assembly are used. Throughput rankings still come ONLY from PLAY ALL.


## Recover framework-01 aggregation failure

Framework-01 incorrectly required elapsed observation totals to agree within
10 ms. Valid SPHERE traces cross that threshold because monitor/IRQ boundaries
can shift within the benchmark's existing per-window cycle allowance. Framework
fix 02 checks matching protocol settings (loops, duration setting, PAL clock,
seed, harness), source/frame counts and raw windows instead. It verifies all
window/flip totals and ranks FPS normalized by actual measured time. This does
not change any recorded samples or renderer behavior. Very small differences
are numerical leaders, not evidence of a repeatable speed advantage.

Recover a completed run without rebuilding or launching VICE:

```bash
python perf/pipeline.py summarize --id local-pilot-01
python perf/watch.py --id local-pilot-01 --once
python perf/pipeline.py bundle --id local-pilot-01
```

The summary records its analysis-script hash separately from the original run
manifest. Do not use `resume` just to recompute a summary: resume is for incomplete
measurements, and rejects changed pipeline code. The viewer fits an 80-column
terminal and shortens V9 labels. JSON output retains full names and precision.

`--workers` already runs separate candidate jobs and VICE instances concurrently.
The pilot has four jobs (step, yunroll, V9 FPS, V9 RAM). Use `--workers 4` for a new
pilot or full run to occupy more cores; each candidate's own measurements stay
sequential. Additional workers do not create more jobs than the selected profile.
Start a genuinely new run with a new ID; keep the completed pilot for comparison.
