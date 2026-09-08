# Remove obsolete outputs from an older checkout

The v0.7.0 snapshot already has the cleanup applied. If extracting it over an
older working tree leaves superseded files behind, run from the repository root:

```bash
python perf/prune_old_examples.py
git status --short
```

The script accepts VERSION 0.7.0 or 0.7.1 and the accepted main Marbles cartridge. It
moves obsolete outputs from the menu, Marbles and Horse/Sunflower directories,
their history subtrees, and the old HiFi showcase to the sibling
`../c64-3d-toolkit-history/` tree. Current hors-render-v1 cartridges and source
assets remain in place. Repeated runs do not duplicate identical archive files.
Conflicting local bytes are kept under the archive's `local-modified/<sha256>/`
path. The script does not stage, commit or rewrite Git history.

Historical reproduction tools may need that external archive; it is optional
and is not shipped in a fresh clone. Some archive-dependent tests then skip;
source/encoder checks still run. The full renderer comparison uses bundled
frozen references and does not require the archive.

Ignored `comparison-tests/` and `logs/` are separate local experiment data and
are left alone. The accepted Marbles reproduction workflow depends on its local
compiled checkpoint; the shipped cart itself does not need it to run.

The release includes the regenerated v0.7.0 performance chart. Run
`python tools/compare_renderers.py --check` to validate the current fingerprint.
Cleanup instructions are not evidence of a new benchmark run.

In v0.7.1 it also archives the superseded v0.7.0 menu carts and metadata.
