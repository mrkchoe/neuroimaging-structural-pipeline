# Running on HPC (Slurm)

This directory provides Slurm job scripts to run the neuroimaging structural pipeline (DICOM → FreeSurfer → metrics) at scale on a cluster.

## Prerequisites

- **Slurm** scheduler on the cluster.
- **Apptainer or Singularity** (Docker is often unavailable on HPC; use container images via Apptainer/Singularity).
- **FreeSurfer license**: obtain from [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/registration.html). Do **not** commit the license to the repo. Place it in a private location (e.g. `$HOME/.freesurfer/license.txt`) and point the scripts to it (see below).
- **Pipeline environment**: either
  - A built **Apptainer/Singularity image** (recommended), or
  - A **conda/venv** on the cluster with the pipeline installed and FreeSurfer available (e.g. module + `USE_DOCKER=false`).

## Apptainer vs Docker

- **Docker** is usually not available on HPC login/compute nodes. Use **Apptainer** (or Singularity) to run the same container image.
- Build an image from the repo Dockerfile:
  ```bash
  apptainer build pipeline.sif Dockerfile
  ```
  Run with appropriate bind mounts so the container can read DICOM dirs and write to output and scratch (see example in the sbatch scripts).
- If you run the pipeline **without** a container (native Python + FreeSurfer on the node), set `USE_DOCKER=false` and ensure `FREESURFER_HOME` and `SUBJECTS_DIR` are set; the scripts use `FS_LICENSE` for the license path.

## License handling

- Scripts expect the FreeSurfer license path to be **configurable** and **not** stored in the repo.
- Default used in the Slurm scripts: `FS_LICENSE=${FS_LICENSE:-$HOME/.freesurfer/license.txt}`.
- Override by setting before submitting, e.g.:
  ```bash
  export FS_LICENSE=/path/to/your/license.txt
  ./submit_array.sh manifest.tsv
  ```
- Ensure the path is visible inside the container (bind mount the directory containing the license when using Apptainer).

## Quick start

1. **Manifest**: create a TSV with one subject per line (header required): `subject_id`, `dicom_dir`, `out_dir`. See `manifest.example.tsv`.
2. **Submit array** (from repo root, or set `REPO_DIR`):
   ```bash
   cd /path/to/neuroimaging-structural-pipeline
   ./hpc/slurm/submit_array.sh /path/to/your/manifest.tsv
   ```
   This counts manifest rows and submits an array job with a concurrency cap.
3. **Single-subject debug**:
   ```bash
   sbatch hpc/slurm/run_one_subject.sbatch sub-001 /path/to/dicom /path/to/out
   ```

## Monitoring commands

- **Array status**:
  ```bash
  squeue -u $USER -j <array_job_id>
  ```
- **Per-task logs** (deterministic paths):
  - Stdout: `logs/<jobname>_<array_job_id>_<task_id>.out`
  - Stderr: `logs/<jobname>_<array_job_id>_<task_id>.err`
- **Failed tasks** (example):
  ```bash
  sacct -j <array_job_id> --format=JobID,State,ExitCode
  ```
- **Re-run only failed tasks**: resubmit with `--array` restricted to the failed indices, or adjust the manifest and submit a new array.

## Scripts

| File | Purpose |
|------|--------|
| `manifest.example.tsv` | Example manifest: `subject_id`, `dicom_dir`, `out_dir`. |
| `submit_array.sh` | Counts manifest rows, submits `recon_all_array.sbatch` as an array with concurrency limit. |
| `recon_all_array.sbatch` | One subject per array task; uses `SLURM_ARRAY_TASK_ID`; optional `SLURM_TMPDIR` scratch; logs to `logs/`; runs pipeline CLI. |
| `run_one_subject.sbatch` | Single-subject job for debugging. |

## Log paths

Logs are written under `logs/` with deterministic names:

- `logs/%x_%A_%a.out` (stdout)
- `logs/%x_%A_%a.err` (stderr)

where `%x` = job name, `%A` = array job ID, `%a` = array task index. Create `logs/` before submitting if your cluster does not create it automatically (the scripts create it when possible).
