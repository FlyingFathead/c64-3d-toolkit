# Upgrade to 0.7.0

v0.7.0 uses hors-render-v1 / hors-render-v1-scene by default. Explicit V9 and
older renderers remain available. The current package includes the accepted
640-sample Marbles presentation and current menu, standalone and Horse/Sunflower
cartridges. GMod backends and automatic renderer selection remain planned.

## Apply the documentation fix pack

Save `c64-3d-toolkit-v0.7.0-docs-fix.zip` in `~/NeuralNetwork/`. It contains
changed Markdown files beneath `c64-3d-toolkit/`, including the main README fix.
Extract from the parent directory, not from inside the repository:

```bash
(
set -euo pipefail
cd ~/NeuralNetwork
unzip -oq c64-3d-toolkit-v0.7.0-docs-fix.zip
cd c64-3d-toolkit
python tools/compare_renderers.py --check
git diff --check
git diff --stat
)
```

This pack changes documentation only; VERSION stays 0.7.0. Renderer sources,
cartridges, labels, manifests, samples and saved performance measurements are
unchanged. It does not rebuild, commit, push or move any tag. Review local
Markdown edits before overwriting them with the supplied versions.

## Fresh installation and older checkouts

Use the complete v0.7.0 source package or release checkout for a fresh install;
the documentation fix pack is not a complete toolkit. Old pre-release overlay
names are historical and are no longer the installation instructions.

If an older overlay left obsolete example cartridges behind, see
[repository cleanup](REPOSITORY_CLEANUP_070.md). Current builds and their
reproduction requirements are documented in [V10_TESTING.md](V10_TESTING.md).
Historical upgrade guides apply only to their named releases.

For code changes, run the source regression suite and required emulator checks.
If fingerprinted comparison inputs change, regenerate the full uncapped matrix
before publishing. A Markdown-only correction does not require new renderer
measurements when `python tools/compare_renderers.py --check` passes. Use new
experiment IDs when source/tool fingerprints change.

## Next release: 0.7.1

Apply and review this documentation correction first. The next planned toolkit
version is 0.7.1, to include the upcoming changes; this pack does not perform
that bump or alter the published v0.7.0 tag/release. Version changes affect the
comparison fingerprint, so release packaging and the required validation will
be handled together after the new changes are defined.

For the completed menu update, see [upgrading to 0.7.1](UPGRADING_0.7.1.md).
