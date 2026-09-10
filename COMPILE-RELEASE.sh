#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python_bin=${PYTHON:-python3}
exec "$python_bin" "$repo_dir/tools/compile_release.py" \
  --jobs "${JOBS:-3}" --tass "${TASS:-64tass}" --cartconv "${CARTCONV:-cartconv}" \
  --vice "${VICE:-x64sc}" --vice-data "${VICE_DATA:-/usr/local/share/vice}" "$@"
