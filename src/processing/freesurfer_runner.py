"""FreeSurfer recon-all execution wrapper."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class FreeSurferRunner:
    """Run FreeSurfer recon-all processing."""

    def __init__(
        self,
        freesurfer_home: str = "/opt/freesurfer",
        subjects_dir: Optional[str] = None,
    ):
        """Initialize FreeSurfer runner.

        Args:
            freesurfer_home: Path to FreeSurfer installation
            subjects_dir: Path to FreeSurfer subjects directory
        """
        self.freesurfer_home = freesurfer_home
        self.subjects_dir = subjects_dir or f"{freesurfer_home}/subjects"

    def run_recon_all(
        self,
        nifti_file: Path,
        subject_id: str,
        use_docker: bool = True,
        docker_image: str = "freesurfer/freesurfer:latest",
    ) -> Dict[str, any]:
        """Run FreeSurfer recon-all on a NIfTI file.

        Args:
            nifti_file: Path to input NIfTI file
            subject_id: Subject identifier
            use_docker: Whether to run via Docker
            docker_image: Docker image to use if use_docker=True

        Returns:
            Dictionary with status, runtime_seconds, and output_dir
        """
        start_time = time.time()

        if use_docker:
            return self._run_recon_all_docker(nifti_file, subject_id, docker_image, start_time)
        else:
            return self._run_recon_all_native(nifti_file, subject_id, start_time)

    def _run_recon_all_docker(
        self, nifti_file: Path, subject_id: str, docker_image: str, start_time: float
    ) -> Dict[str, any]:
        """Run recon-all using Docker."""
        nifti_file = nifti_file.resolve()
        nifti_dir = nifti_file.parent

        # Mount volumes: input directory, subjects directory, FreeSurfer license
        # Assume license is at /opt/freesurfer/license.txt or set via env
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{nifti_dir}:/input:ro",
            "-v",
            f"{self.subjects_dir}:/output",
            "-e",
            f"SUBJECTS_DIR=/output",
            "-e",
            f"FREESURFER_HOME={self.freesurfer_home}",
            docker_image,
            "recon-all",
            "-i",
            f"/input/{nifti_file.name}",
            "-s",
            subject_id,
            "-all",
        ]

        try:
            logger.info(f"Running FreeSurfer recon-all for subject {subject_id}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=36000  # 10 hours
            )
            runtime = time.time() - start_time

            output_dir = Path(self.subjects_dir) / subject_id
            status = "completed" if (output_dir / "scripts" / "recon-all.done").exists() else "failed"

            logger.info(f"FreeSurfer completed: {status}, runtime: {runtime:.1f}s")

            return {
                "status": status,
                "runtime_seconds": runtime,
                "output_dir": str(output_dir),
                "stdout": result.stdout[-1000:],  # Last 1000 chars
                "stderr": result.stderr[-1000:] if result.stderr else None,
            }

        except subprocess.CalledProcessError as e:
            runtime = time.time() - start_time
            logger.error(f"FreeSurfer recon-all failed: {e.stderr}")
            return {
                "status": "failed",
                "runtime_seconds": runtime,
                "output_dir": None,
                "stdout": e.stdout[-1000:] if e.stdout else None,
                "stderr": e.stderr[-1000:] if e.stderr else None,
            }
        except subprocess.TimeoutExpired:
            runtime = time.time() - start_time
            logger.error("FreeSurfer recon-all timed out")
            return {
                "status": "timeout",
                "runtime_seconds": runtime,
                "output_dir": None,
                "stdout": None,
                "stderr": "Process timed out after 10 hours",
            }

    def _run_recon_all_native(
        self, nifti_file: Path, subject_id: str, start_time: float
    ) -> Dict[str, any]:
        """Run recon-all natively (requires FreeSurfer installed)."""
        import os

        env = os.environ.copy()
        env["FREESURFER_HOME"] = self.freesurfer_home
        env["SUBJECTS_DIR"] = self.subjects_dir

        cmd = [
            f"{self.freesurfer_home}/bin/recon-all",
            "-i",
            str(nifti_file),
            "-s",
            subject_id,
            "-all",
        ]

        try:
            logger.info(f"Running FreeSurfer recon-all natively for subject {subject_id}")
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, check=True, timeout=36000
            )
            runtime = time.time() - start_time

            output_dir = Path(self.subjects_dir) / subject_id
            status = "completed" if (output_dir / "scripts" / "recon-all.done").exists() else "failed"

            return {
                "status": status,
                "runtime_seconds": runtime,
                "output_dir": str(output_dir),
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:] if result.stderr else None,
            }

        except subprocess.CalledProcessError as e:
            runtime = time.time() - start_time
            logger.error(f"FreeSurfer recon-all failed: {e.stderr}")
            return {
                "status": "failed",
                "runtime_seconds": runtime,
                "output_dir": None,
                "stdout": e.stdout[-1000:] if e.stdout else None,
                "stderr": e.stderr[-1000:] if e.stderr else None,
            }
        except subprocess.TimeoutExpired:
            runtime = time.time() - start_time
            return {
                "status": "timeout",
                "runtime_seconds": runtime,
                "output_dir": None,
                "stdout": None,
                "stderr": "Process timed out after 10 hours",
            }
