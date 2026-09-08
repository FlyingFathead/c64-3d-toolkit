# 0.7.0 main examples cleanup

Run `python perf/cleanup_070_examples.py` after extracting cleanup-03.
The accepted 16 FPS force-bytes Marbles is the main presentation. Its startup
now waits indefinitely for SPACE before the intro; its animation is unchanged.
Labels and manifest are retained from the accepted local run.

Superseded outputs are relocated under each example's history directory.
Canonical historical reference bytes are included for regression tests.
Modified local copies are preserved under history/local-modified/<sha256>/,
without overwriting the reference copy. A second run does not repeat the moves.

The cleanup does not rerender, search FPS, delete renderer implementations or
change the measured scene timing. Comparison chart provenance remains stale
following the input relocation; final release validation is still outstanding.
