#!/usr/bin/env bash
# Single-subject debug job.
# Usage: sbatch run_one_subject.sbatch <subject_id> <dicom_dir> <out_dir>
# Example: sbatch run_one_subject.sbatch sub-001 /data/dicom/sub-001 /data/out/sub-001
set -euo pipefail

#SBATCH --job-name=recon_one
#SBATCH --output=logs/%x_%A.out
#SBATCH --error=logs/%x_%A.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=normal

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
subject_id="${1:?Usage: sbatch run_one_subject.sbatch <subject_id> <dicom_dir> <out_dir>}"
dicom_dir="${2:?}"
out_dir="${3:?}"

FS_LICENSE="${FS_LICENSE:-$HOME/.freesurfer/license.txt}"
APPTAINER_SIF="${APPTAINER_SIF:-}"

mkdir -p logs "$out_dir"

if [[ -n "${SLURM_TMPDIR:-}" ]]; then
  WORK_SUBJECTS="$SLURM_TMPDIR/subjects"
  WORK_NIFTI="$SLURM_TMPDIR/nifti"
  mkdir -p "$WORK_SUBJECTS" "$WORK_NIFTI"
  export SUBJECTS_DIR="$WORK_SUBJECTS"
  export NIFTI_OUTPUT_DIR="$WORK_NIFTI"
else
  export SUBJECTS_DIR="${SUBJECTS_DIR:-$out_dir/../subjects}"
  mkdir -p "$SUBJECTS_DIR"
fi

export FREESURFER_HOME="${FREESURFER_HOME:-/opt/freesurfer}"
export USE_DOCKER=false

cd "$REPO_DIR"
NIFTI_OUT="${NIFTI_OUTPUT_DIR:-/tmp/nifti_output}"
if [[ -n "$APPTAINER_SIF" ]] && [[ -f "$APPTAINER_SIF" ]]; then
  BINDS="$dicom_dir,$out_dir,$(dirname "$FS_LICENSE")"
  [[ -n "${SLURM_TMPDIR:-}" ]] && BINDS="$BINDS,$SLURM_TMPDIR"
  apptainer exec --bind "$BINDS" \
    -e "FS_LICENSE=$FS_LICENSE" \
    -e "SUBJECTS_DIR=$SUBJECTS_DIR" \
    -e "NIFTI_OUTPUT_DIR=$NIFTI_OUT" \
    -e "USE_DOCKER=false" \
    "$APPTAINER_SIF" bash -c "cd '$REPO_DIR' && python -m src.cli run --dicom-dir '$dicom_dir' --subject-id '$subject_id' --output-dir '$NIFTI_OUT'"
else
  export FS_LICENSE
  python -m src.cli run \
    --dicom-dir "$dicom_dir" \
    --subject-id "$subject_id" \
    --output-dir "$NIFTI_OUT"
fi

if [[ -n "${SLURM_TMPDIR:-}" ]]; then
  SUBJ_DIR="$SUBJECTS_DIR/$subject_id"
  [[ -d "$SUBJ_DIR" ]] && cp -a "$SUBJ_DIR" "$out_dir/"
fi
