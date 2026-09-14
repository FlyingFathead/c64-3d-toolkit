# Checkpoint and recovery workflow

Save a uniquely numbered archive after each completed fix. Record what passed,
what is complete, and what remains. After two or three incremental checkpoints,
save a full source snapshot as well. Copy each archive to durable storage before
continuing; a checkpoint only inside a disposable workspace is insufficient.

From the checkout:

```sh
python tools/checkpoint.py --destination ../c64-checkpoints --baseline-zip ../baseline.zip --done "Camera clipping implemented" --pending "Native playback checks" --validation "311 unit tests passed; 3 skipped"
python tools/checkpoint.py --destination ../c64-checkpoints --full --done "Verified source snapshot"
```

Each invocation allocates the next `cpNNN` number and uses exclusive creation.
It cannot overwrite an existing archive. It writes a SHA-256 sidecar and embeds
`docs/checkpoints/<checkpoint-name>.json` with completed/pending items, supplied
validation results, baseline checksum and per-file checksums. The command
records validation results; it does not run or infer tests.

An incremental includes every changed/new source file relative to its baseline,
so apply the latest cumulative incremental directly over that baseline. Extract
from the checkout's parent directory; entries start with `c64-3d-toolkit/`.
Review recorded deletions manually. ZIP overlays never remove files themselves.

Full source snapshots exclude `.git`, local configuration, build work,
comparison workspaces, caches, logs, ZIPs and symbolic links. Keep troubleshooting
assets and other material that must not ship outside the checkout. A ZIP does
not preserve Git index/staging state or commit history; record those separately
when relevant.

Before delivery: validate the archive's checksums, inspect the changed-file
list, check public documentation, and scan for excluded names/content. Never
reuse a checkpoint filename for a different revision.
