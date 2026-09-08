# Remove obsolete outputs from the checkout

Apply this patch after examples-cleanup-03, then run:

```bash
python perf/prune_old_examples.py
python -m unittest discover -s tests
```

This removes all three cartridge history trees and the obsolete HiFi V2/V3
showcase from the checkout. Files are moved to sibling directory
`../c64-3d-toolkit-history/`; no copies remain in tracked source directories.
Modified files are preserved there as well. Repeated runs are harmless.
The script does not stage or commit changes: `git add -A` records the removals
when preparing the release. Git's existing commit history is not rewritten.

Historical reproduction tools use the external sibling archive. Fresh clones
without that archive explicitly skip three external-data checks; source and
encoder regression checks still run. Restoring that archive enables those
historical checks again. Current assets and renderer source are retained.

The large comparison-tests directory is a separate local experiment cache.
This cleanup leaves it alone because it contains source samples needed for
rebuilding the accepted Marbles cart without running Blender again.

The renderer-comparison provenance gate remains stale and requires separate
validation before release. This patch does not claim fresh benchmark results.
