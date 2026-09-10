#!/usr/bin/env bash
# Test-only VICE launcher: isolate saved settings and retain each process log.
set -uo pipefail
vice_real=${C64_VICE_REAL:-}
if [[ -z "$vice_real" ]]; then vice_real=$(command -v x64sc) || exit 127; fi
if [[ ! -x "$vice_real" || "$vice_real" -ef "${BASH_SOURCE[0]}" ]]; then
  echo "C64_VICE_REAL must name the actual VICE executable: $vice_real" >&2
  exit 2
fi
log_dir=${C64_VICE_LOG_DIR:-${TMPDIR:-/tmp}}
mkdir -p -- "$log_dir" || exit 2
vice_log=$(mktemp "$log_dir/c64-vice-XXXXXX.log") || exit 2
buffering=()
if command -v stdbuf >/dev/null 2>&1; then buffering=(stdbuf -oL -eL); fi
{
  printf 'VICE batch executable: %s\n' "$vice_real"
  printf 'VICE batch arguments:'
  printf ' %q' -default "$@" +saveres -jamaction 5
  printf '\n'
} > "$vice_log"
"${buffering[@]}" "$vice_real" -default "$@" +saveres -jamaction 5 >> "$vice_log" 2>&1 &
vice_pid=$!
trap 'kill -TERM "$vice_pid" 2>/dev/null || true; wait "$vice_pid" 2>/dev/null; exit 143' TERM
trap 'kill -INT "$vice_pid" 2>/dev/null || true; wait "$vice_pid" 2>/dev/null; exit 130' INT
wait "$vice_pid"
vice_status=$?
trap - TERM INT
cat -- "$vice_log"
# VICE 3.10 can return success when JAMAction=5 quits. A JAM is a test failure.
if LC_ALL=C grep -Eq 'JAM at|CPU JAM' "$vice_log"; then
  echo "VICE CPU JAM: test failed; retained log: $vice_log" >&2
  exit 1
fi
if [[ $vice_status -ne 0 ]]; then
  echo "VICE exited with status $vice_status; retained log: $vice_log" >&2
fi
exit "$vice_status"
