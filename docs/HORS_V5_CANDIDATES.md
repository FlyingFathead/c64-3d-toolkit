# HORS-V5 candidates

Checkpoint 006 preserves the existing V5 as **c1** and adds a separate,
experimental **c2**. HORS-V4/EasyFlash remains the default. V4 and earlier
renderer assembly is unchanged. GMod3 remains an explicit V4 option; GMod4
remains roadmap work.

| Selector | Meaning |
| --- | --- |
| `hors-v5`, `hors-v5-ef`, `hors-v5-c1`, `hors-v5-c1-ef` | Existing V5 clearing and V3 shared-colour policy; c1 |
| `hors-v5-c2`, `hors-v5-c2-ef` | V5 clearing with per-animation colour-transport selection; c2 |
| `hors-v4`, `hors-v4-ef` | Preserved V4 EasyFlash default |

The accepted `hors-render-v5-c1/c2` and `hors-renderer-v5-c1/c2` spellings
select the corresponding candidate. Old V5 names never silently select c2.

## Build and inspect

```sh
python3 c643d.py build --scene /path/to/scene.c643dscene \
  --renderer hors-v5-c1 --output scene-v5-c1 --output-dir /path/to/private-carts
python3 c643d.py build --scene /path/to/scene.c643dscene \
  --renderer hors-v5-c2 --output scene-v5-c2 --output-dir /path/to/private-carts
x64sc -cartcrt /path/to/private-carts/scene-v5-c2.crt
```

Both candidates produce ordinary EasyFlash CRTs. C2 currently supports standalone
objects and authored scenes without interactive effects. Interactive recolouring,
starfields and presentation switching retain the established c1/V4 paths.
C2 currently requires literal colour encoding; indexed4 is not supported.

For c2, `--v5-color-plan auto` is the default. `runs` or `shared` forces a
transport for a controlled comparison. The chosen mode, heuristic estimates,
and rejected capacity alternatives are recorded in the cartridge manifest.
An ordinary c2 build does not launch VICE. Use `--renderer-contest` to measure
and select among complete renderers, including c1, c2 and the older methods.

## What changed

C1 uses V3's shared colour layout and V5's bounded clear search. C2 evaluates
two ways to send the same already-resolved screen colours to the C64:

* **Runs:** V2-style per-picture colour runs, including the old-colour reset
  when recycling a buffer. This can suit long stretches of one colour.
* **Shared:** V3-style shared-address colour updates, including explicit
  background values. This can suit fragmented colour patterns where run
  metadata and dispatch cost would be large.

Each candidate receives V5's bounded clear planner. A host CPU-cost estimate
selects one colour transport for the whole animation. This avoids a runtime
branch choosing a colour format every picture. It is a heuristic, not a promise
of the fastest actual display rate. Frame metadata must fit the existing 1 KiB
slot cache and each encoded picture must fit an 8 KiB stream bank. Complete
cartridge packing is checked by the normal builder; the heuristic does not
retry a different whole-animation plan after a final cartridge-capacity error.

C2 retains three bitmap buffers and independent pictures; clearing always
describes the picture in the recycled slot. No previous-source-frame delta
dependency or additional bitmap buffer is introduced. Temporary build hooks
are restored on success or failure. C1's rendering/planning functions are
unchanged; its new label and default output suffix identify the candidate.

## Colour appearance

**C2 does not change colour mapping, 8×8 hires colour cells, visibility, or the
default overlap decision.** The Blender linear/sRGB selection is unchanged.
Road-fragment suppression is not enabled. Each encoding plan must preserve
the full input bitmap and colour bytes, followed by completed-picture checks
in VICE. Existing colour conflicts therefore remain visible in these CRTs.

## Evidence

See the new candidate section of [PERFORMANCE_COMPARISON.md](PERFORMANCE_COMPARISON.md)
and [complete candidate tables](V5_CANDIDATE_COMPARISON.md). Public comparison
carts use the same frozen corpus, including separate Dragon and SAKU logo-only
versions. Private Nightdrive Test carts and artwork remain outside the source
archive and repository. Existing historical tables retain all older methods.

Native scenes retain the four-refresh minimum hold; public common-controller
PLAY ALL measurements are uncapped. Compare FPS within each protocol. Average,
tail holds, CRT size and exact picture checks are reported separately. C2 is
not promoted as a universal replacement. Physical C64 and NTSC are unmeasured.
