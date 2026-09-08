# Upgrade to 0.7.0

Apply the pre-release-v0.7.0-v1 overlay at the repository root. It is cumulative relative to published 0.6.9 (including the chart-format correction), and also applies over the supplied candidate-framework/fix-02 working tree. No file deletions are required. Back up uncommitted local edits first. Generated logs and test outputs are excluded.

VERSION is 0.7.0. hors-render-v1/hors-render-v1-scene become the build defaults. Explicit V9 and older choices remain available. New cartridges have separate hors-render-v1 names; historical cartridges keep their original labels and bytes. GMod backends and automatic renderer selection remain planned. See V10_TESTING.md for the new build/export commands.

```bash
python -m unittest discover -s tests
python tools/compare_renderers.py --check
git add -A
git diff --cached --check
git diff --cached --stat
```

Use new experiment IDs after upgrading: source fingerprints change with version updates. Existing results remain valuable historical evidence. See [hors-render-v1 and Marbles testing](V10_TESTING.md) for commands, output locations and metric definitions. Run the optional Marbles benchmark independently of the menu sweep.

Before publishing, review the staged diff and preserve the historical source/binary checks. Packaging this overlay does not push, tag or create a GitHub release.
