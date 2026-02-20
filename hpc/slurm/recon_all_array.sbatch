#!/usr/bin/env bash
# One subject per array task: DICOM -> FreeSurfer -> metrics via pipeline CLI.
# Uses SLURM_TMPDIR for scratch when available. Logs to logs/%x_%A_%a.out/err.
# Requires MANIFEST and REPO_DIR in environment (set by submit_array.sh).
set -euo pipefail

#SBATCH --job-name=recon_all
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=normal

REPO_DIR="${REPO_DIR:?Set REPO_DIR}"
MANIFEST="${MANIFEST:?Set MANIFEST}"
FS_LICENSE="${FS_LICENSE:-$HOME/.freesurfer/license.txt}"
APPTAINER_SIF="${APPTAINER_SIF:-}"

mkdir -p logs

# Line number in manifest (1-based index; line 1 = header)
LINE=$((SLURM_ARRAY_TASK_ID + 1))
read -r subject_id dicom_dir out_dir <<< "$(sed -n "${LINE}p" "$MANIFEST")"

if [[ -z "$subject_id" ]] || [[ "$subject_id" == "subject_id" ]]; then
  echo "Invalid or header line at task $SLURM_ARRAY_TASK_ID" >&2
  exit 1
fi

mkdir -p "$out_dir"

# Prefer scratch on node when available
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

# Copy subject dir to final out_dir if we used scratch
if [[ -n "${SLURM_TMPDIR:-}" ]]; then
  SUBJ_DIR="$SUBJECTS_DIR/$subject_id"
  if [[ -d "$SUBJ_DIR" ]]; then
    cp -a "$SUBJ_DIR" "$out_dir/"
  fi
fi
