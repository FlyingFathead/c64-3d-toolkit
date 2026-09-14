# Release preparation checkpoint 007

Date: 2026-09-14. Version: 0.8.1.

Completed:
- Added timestamped, copy-verified root log archival and tracked-log cleanup.
- Verified 8 maintenance regression tests and 6 native VICE checks: the raw
  default reproduces a root log; corrected launchers do not create one.
  [Native log verification](benchmarks/monitor-maintenance-native.json).
- Local release fixtures cover tracked root and nested monitor logs, preserving
  their contents while excluding them from the commit and tagged archive.
- Consolidated camera/colour fixes and the interactive hotfix under one v0.8.1 heading.
- Updated release notes and added a GitHub announcement with version-pinned links.
- Moved the publisher outside the repository and removed it from the reviewed
  file inventory. Added an ignore rule and source-packaging exclusion.
- The external publisher retires the checkpoint-005 copy, preserves local and
  staged copies outside the checkout, and removes it from the Git index.
- Checked shell syntax and tested release flow against a temporary local Git remote,
  with simulated GitHub calls: staged-file guard, source selection, commit, annotated
  tag, atomic push, tagged archive, checksum and existing-tag refusal passed.
- Checked migration of untracked, staged and committed old publishers, including
  preservation of differing local/staged contents. Verified the script cannot run
  from inside the checkout and no publisher reaches the tag or release archive.
- Verified source packaging excludes publishers while retaining toolkit build
  commands, and reran the two checkpoint tests successfully.
- Reran the production source suite: 321 tests, 318 passed, 3 optional historical skips.
- Reran the saved GMod3 release/evidence audit successfully. Renderer code and
  cartridge bytes are unchanged from recovery checkpoint 004.

Pending:
- Run `bash ../RELEASE-v0.8.1-cp007.sh .` from the local main checkout to publish.
  The script performs live remote/tag/release checks before committing or tagging.
  No actual GitHub release was created during preparation.

The preparation ZIP is cumulative over the original supplied v0.8.1 baseline;
applying it also installs all checkpoint-004 fixes. It can be applied directly
over that baseline or over checkpoints 004/005/006. The external publisher is a
top-level delivery file beside the source directory, never a repository file.
ZIP extraction alone cannot retire the old copy: running the new external
publisher performs that cleanup before authentication and publication.
