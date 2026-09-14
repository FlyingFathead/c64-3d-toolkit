#!/usr/bin/env python3
"""Archive stale root monitor.log into logs/ without overwriting earlier logs."""
import argparse
from pathlib import Path
import subprocess
import sys

from c643d.monitor_logs import ROOT, archive_root_monitor, untrack_monitor_logs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='toolkit checkout directory')
    parser.add_argument('--untrack-monitor-logs', action='store_true',
                        help='also archive and untrack generated monitor.log files anywhere in Git')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        archive = archive_root_monitor(root)
        if archive:
            print('Archived root monitor.log to ' + str(archive.relative_to(root)))
        if args.untrack_monitor_logs:
            names = untrack_monitor_logs(root)
            if names:
                print(f'Archived and untracked {len(names)} generated monitor log(s); copies retained in logs/.')
    except (OSError, subprocess.SubprocessError) as exc:
        print(f'Monitor log maintenance failed: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
