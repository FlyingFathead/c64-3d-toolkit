# Monitor log maintenance

VICE's debugger writes `monitor.log` when logging is enabled without a filename.
Option order matters: `-monlog` opens the file immediately, so `-monlogname`
must come first. Resource resets with `-default` must also precede the selected
filename. The toolkit handles these cases in its launchers and diagnostics.

Every CLI startup checks for a stale root `monitor.log`. If present, maintenance:

1. Copies it into ignored `logs/` with a UTC timestamp and a unique suffix,
   such as `monitor-20260914T120000.123456Z-a1b2c3d4.log`.
2. Flushes the copy and verifies its SHA-256 against the original.
3. Removes the root copy only after verification succeeds and the source has
   not changed during the copy.

Previous archives are never overwritten. If copying or verification fails,
the original remains and the command reports the problem. An absent log is a
no-op. Run maintenance between emulator sessions, not while another process
is actively writing the old root log.

Run it directly when needed:

```sh
python3 tools/maintenance.py
```

Ordinary toolkit VICE launches allocate unique `logs/vice-monitor-*.log`
filenames. Batch checks use their own log directory. Explicit diagnostic log
destinations are preserved, with the filename selected before enabling logging.
`RUN-CHECKS.sh` also runs root-log maintenance before its checks.

## Previously tracked monitor logs

Ignore rules do not remove files already tracked by Git. Older checkouts can
still track a generated benchmark transcript such as
`docs/benchmarks/hors-v2/examples/marbles-ending/monitor.log`.

```sh
python3 tools/maintenance.py --untrack-monitor-logs
```

This archives both working copies and staged contents of tracked files named
exactly `monitor.log`, then removes those paths from Git's index. Backups stay
under ignored `logs/`; unrelated staged files are preserved. The external release
publisher runs this automatically and includes only the generated files' deletions
in the release commit. It still rejects unrelated files outside the reviewed
source inventory. No log archives or publisher scripts enter release assets.
