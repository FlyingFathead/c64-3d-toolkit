#!/usr/bin/env bash
# Run from anywhere; outputs go beside the repository by default.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd -- "$repo_dir"
toolkit_version=$(tr -d '\r\n' < "$repo_dir/VERSION")
results_dir=${1:-"$repo_dir/../c64-${toolkit_version//./}-local-tests"}
if [[ -e "$results_dir" ]]; then
  echo "Results directory already exists: $results_dir. Choose a new directory." >&2
  exit 2
fi
mkdir -p -- "$results_dir"
results_dir=$(cd -- "$results_dir" && pwd)
python_bin=${PYTHON:-python}
vice_bin=${VICE:-x64sc}
tass_bin=${TASS:-64tass}
cartconv_bin=${CARTCONV:-cartconv}
vice_data=${VICE_DATA:-/usr/local/share/vice}
jobs=${JOBS:-3}
vice_real=$(command -v "$vice_bin") || { echo "VICE executable not found: $vice_bin" >&2; exit 2; }
export C64_VICE_REAL="$vice_real"
export C64_VICE_LOG_DIR="$results_dir/vice-logs"
mkdir -p -- "$C64_VICE_LOG_DIR"
vice_bin="$repo_dir/VICE-BATCH.sh"
if [[ ! -x "$vice_bin" ]]; then echo "Test launcher is not executable: $vice_bin" >&2; exit 2; fi
"$vice_real" --version > "$results_dir/vice-version.txt" 2>&1
sha256sum -- "$vice_real" "$vice_bin" > "$results_dir/vice-executables.sha256"
run_check() {
  local check_name=$1
  shift
  "$@" 2>&1 | tee "$results_dir/$check_name.log"
}
run_check unit "$python_bin" -m unittest discover -s tests -p 'test_*.py'
run_check boundaries "$python_bin" tools/verify_hors_v2.py \
  --out "$results_dir/boundaries" --tass "$tass_bin" \
  --cartconv "$cartconv_bin" --vice "$vice_bin" --vice-data "$vice_data"
extra_search=()
if [[ ${EXTENDED_SEARCH:-0} == 1 ]]; then extra_search+=(--extended-search); fi
run_check showcase "$python_bin" tools/run_hors_v2_perfs.py \
  --workspace "$results_dir/showcase" --jobs "$jobs" \
  --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$vice_bin" \
  --vice-data "$vice_data" "${extra_search[@]}"
run_check menu-ui "$python_bin" tools/verify_cart_menu.py \
  "$results_dir/showcase/carts/demo-cart-2-preview-hors-v2.crt" \
  --vice "$vice_bin" --vice-data "$vice_data" --report "$results_dir/menu-ui.json"
run_check canonical "$python_bin" tools/compare_renderers.py \
  --workspace "$results_dir/canonical" --workers "$jobs" \
  --tass "$tass_bin" --cartconv "$cartconv_bin" --vice "$vice_bin" \
  --vice-data "$vice_data"
# Update the chart only after every preceding command has succeeded.
cp -- "$results_dir/canonical/PERFORMANCE_COMPARISON.md" docs/PERFORMANCE_COMPARISON.md
run_check provenance "$python_bin" tools/compare_renderers.py --check
echo "Checks passed. Results: $results_dir"
echo "hors-render-v2 is the $toolkit_version default. Review video output after local rebuilds."
echo 'No renderer default, Git commit, tag or push was changed.'
