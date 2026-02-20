#!/usr/bin/env bash
# Submit Slurm array job for pipeline (one subject per task).
# Usage: ./submit_array.sh <manifest.tsv> [concurrency_cap]
# Example: ./submit_array.sh /data/manifest.tsv 8
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
MANIFEST="${1:?Usage: $0 <manifest.tsv> [concurrency_cap]}"
CAP="${2:-8}"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Error: manifest not found: $MANIFEST" >&2
  exit 1
fi

# Count data rows (exclude header)
N=$(tail -n +2 "$MANIFEST" | grep -c . || true)
if [[ "$N" -eq 0 ]]; then
  echo "Error: no data rows in manifest $MANIFEST" >&2
  exit 1
fi

mkdir -p "$REPO_DIR/logs"
echo "Submitting array job: 1-$N (max concurrent: $CAP)"
sbatch \
  --array=1-${N}%${CAP} \
  --export=ALL,MANIFEST="$(realpath "$MANIFEST")",REPO_DIR="$(realpath "$REPO_DIR")" \
  "$SCRIPT_DIR/recon_all_array.sbatch"
