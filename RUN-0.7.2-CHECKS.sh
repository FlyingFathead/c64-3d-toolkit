#!/usr/bin/env bash
# Compatibility entry point for existing 0.7.2 instructions.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec bash "$repo_dir/RUN-CHECKS.sh" "$@"
