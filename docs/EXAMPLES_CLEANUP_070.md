# Current examples and historical output cleanup — 0.7.0

The released snapshot already contains the accepted 640-sample, 16 FPS
force-bytes Marbles presentation, with SPACE to start. Current menu,
Horse/Sunflower and standalone cartridges use hors-render-v1; see the
[example index](../examples/README.md) and [inventory](V10_CARTRIDGES.md).

No promotion from `marbles-realtime-01` is required to use this package. Its
accepted Marbles CRT, labels and manifest are already supplied. The earlier
cleanup-02/03 instructions described development patches, not fresh-clone setup.

For leftovers from old overlays, run `python perf/prune_old_examples.py` from
the repository root. `perf/cleanup_070_examples.py` is now a compatibility alias
for that same cleanup; it does not install a cart from a local experiment run.
See [repository cleanup](REPOSITORY_CLEANUP_070.md) for destinations and limits.

The saved [performance comparison](PERFORMANCE_COMPARISON.md) is the v0.7.0
source-fingerprinted chart. Validate it using
`python tools/compare_renderers.py --check`; the pre-release statement that its
provenance was still stale no longer describes the supplied release.
