# v0.7.9 release check: preserve the README showreel

The README links to `assets/c64-3d-toolkit-examples-showreel-v0.7.7.mp4`.
Keep that file in the repository. The teaser GIF is a separate file; removing
the MP4 would break the full-video link once the deletion is committed.

## Cause and correction

The comparison fingerprint previously hashed every non-Markdown file under
`assets/`, including local recordings. The supplied source snapshot omitted
the MP4, so a checkout containing that additional video failed the release
check even when all recorded renderer inputs matched.

The fingerprint now excludes `.mp4`, `.m4v`, `.mov`, `.webm`, `.mkv`, and `.avi`
files under `assets/`, with case-insensitive suffix matching. These formats are
promotional recordings, not inputs to the benchmark. Model data, reference
data, images, renderer sources, tools and measured cartridge files retain
their previous checks. This exclusion does not move or delete any files and
does not change which tracked files `git archive` includes.

Regression coverage checks video addition, replacement and removal without
invalidating the fingerprint, and still requires actual input changes to
invalidate it. The complete uncapped comparison was rerun because the checker
itself is a recorded source file. See the accompanying
[validation record](benchmarks/release-final-v5-media-fix/validation.json).
The standalone HORS-V3, Dragon and SAKU measurements retain their verified
cartridge bytes and measurements; their broad source inventories update only
the unrelated comparison-checker/test hashes, with a separate audit in
[evidence-refresh.json](benchmarks/release-final-v5-media-fix/evidence-refresh.json).

## Applying this correction

Apply the media-fix incremental ZIP after the cumulative `release_final_v5`
update, from the parent of the checkout. This small correction leaves the
showreel in place and contains no replacement video or cartridge binaries.

If the MP4 was moved aside using the earlier workaround, restore it from the
`c64-showreel-backup.*` directory before committing. The repository has a
general video ignore rule, so preserve this intentional README asset with:

```bash
git add -f -- assets/c64-3d-toolkit-examples-showreel-v0.7.7.mp4
python examples/stanford_dragon/verify.py --check
python tools/run_hors_v3_perfs.py --check
python tools/compare_renderers.py --check
```

The release remains `v0.7.9`. Continue with the commit, annotated tag,
`git archive`, push and release steps after these checks pass. The failed
preflight attempt did not create a release commit or tag.
