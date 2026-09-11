#!/usr/bin/env bash
# Rebuild Sande's registry and collect a portable benchmark log bundle.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd -- "$repo_dir"
python_bin=${PYTHON:-python3}
tass_bin=${TASS:-64tass}
cartconv_bin=${CARTCONV:-cartconv}
vice_bin=${VICE:-x64sc}
vice_data=${VICE_DATA:-/usr/local/share/vice}
jobs=${JOBS:-3}
results_dir=${1:-"$repo_dir/../c64-sande-checks-$(date +%Y%m%d-%H%M%S)"}
if [[ -e "$results_dir" ]]; then
  echo "Choose a new results directory: $results_dir" >&2
  exit 2
fi
mkdir -p -- "$results_dir"
results_dir=$(cd -- "$results_dir" && pwd)
export C64_VICE_REAL
C64_VICE_REAL=$(command -v "$vice_bin")
export C64_VICE_LOG_DIR="$results_dir/vice-logs"
run_check() {
  local label=$1
  shift
  "$@" 2>&1 | tee "$results_dir/$label.log"
}
run_check build "$python_bin" tools/build_sande_examples.py --tass "$tass_bin" --cartconv "$cartconv_bin"
run_check build-interactive "$python_bin" tools/build_sande_examples.py --interactive --tass "$tass_bin" --cartconv "$cartconv_bin"
run_check build-colors "$python_bin" tools/build_sande_examples.py --source-colors --tass "$tass_bin" --cartconv "$cartconv_bin"
run_check colors "$python_bin" tools/verify_sande_colors.py --out "$results_dir/colors" \
  --vice "$repo_dir/VICE-BATCH.sh" --vice-data "$vice_data"
run_check controls "$python_bin" tools/verify_sande_controls.py --out "$results_dir/controls" \
  --vice "$repo_dir/VICE-BATCH.sh" --vice-data "$vice_data"
run_check standalone "$python_bin" tools/run_sande_perfs.py --workspace "$results_dir/standalone" \
  --jobs "$jobs" --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$C64_VICE_REAL" --vice-data "$vice_data"
run_check standalone-colors "$python_bin" tools/run_sande_perfs.py --source-colors --workspace "$results_dir/standalone-colors" \
  --jobs "$jobs" --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$C64_VICE_REAL" --vice-data "$vice_data"
run_check methods "$python_bin" tools/run_sande_methods.py --workspace "$results_dir/methods" --skip-build \
  --jobs "$jobs" --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$repo_dir/VICE-BATCH.sh" --vice-data "$vice_data"
run_check methods-colors "$python_bin" tools/run_sande_methods.py --source-colors --workspace "$results_dir/methods-colors" --skip-build \
  --jobs "$jobs" --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$repo_dir/VICE-BATCH.sh" --vice-data "$vice_data"
"$python_bin" - "$results_dir" <<'PY'
from pathlib import Path
import hashlib, sys, zipfile
root = Path(sys.argv[1])
output = root / 'sande-perf-logs.zip'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if path.is_file() and not any(part in ('source', 'carts', 'build', 'vice-logs') for part in rel.parts) and path.suffix in ('.json', '.log', '.md'):
            archive.write(path, rel)
digest = hashlib.sha256(output.read_bytes()).hexdigest()
(root / 'SHA256SUMS.txt').write_text(digest + '  ' + output.name + '\n')
print('Sande checks passed. Share this bundle:', output)
PY
