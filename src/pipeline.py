"""Main pipeline orchestration."""

import logging
from pathlib import Path
from typing import Optional

from .database.loader import DatabaseLoader
from .extraction.stats_parser import StatsParser
from .ingestion.dicom_processor import DicomProcessor
from .processing.freesurfer_runner import FreeSurferRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline orchestrator."""

    def __init__(
        self,
        database_url: str,
        subjects_dir: str = "/data/freesurfer/subjects",
        freesurfer_home: str = "/opt/freesurfer",
        use_docker: bool = True,
    ):
        """Initialize pipeline.

        Args:
            database_url: PostgreSQL connection URL
            subjects_dir: FreeSurfer subjects directory
            freesurfer_home: FreeSurfer installation path
            use_docker: Whether to use Docker for FreeSurfer
        """
        self.dicom_processor = DicomProcessor()
        self.freesurfer_runner = FreeSurferRunner(
            freesurfer_home=freesurfer_home, subjects_dir=subjects_dir
        )
        self.stats_parser = StatsParser(subjects_dir=subjects_dir)
        self.db_loader = DatabaseLoader(database_url)
        self.use_docker = use_docker

    def run(
        self,
        dicom_dir: Path,
        subject_id: str,
        output_dir: Optional[Path] = None,
    ) -> dict:
        """Run full pipeline for a subject.

        Args:
            dicom_dir: Path to DICOM directory
            subject_id: Subject identifier
            output_dir: Optional output directory for NIfTI files

        Returns:
            Dictionary with processing results
        """
        output_dir = output_dir or Path("/tmp/nifti_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "subject_id": subject_id,
            "status": "pending",
            "errors": [],
        }

        # Step 1: Validate and convert DICOM
        logger.info(f"Step 1: Validating DICOM for {subject_id}")
        is_valid, error_msg = self.dicom_processor.validate_modality(dicom_dir)
        if not is_valid:
            results["status"] = "failed"
            results["errors"].append(f"DICOM validation failed: {error_msg}")
            return results

        logger.info(f"Step 2: Converting DICOM to NIfTI for {subject_id}")
        nifti_file = self.dicom_processor.convert_to_nifti(
            dicom_dir, output_dir, subject_id
        )
        if not nifti_file:
            results["status"] = "failed"
            results["errors"].append("DICOM to NIfTI conversion failed")
            return results

        # Step 2: Run FreeSurfer
        logger.info(f"Step 3: Running FreeSurfer recon-all for {subject_id}")
        freesurfer_result = self.freesurfer_runner.run_recon_all(
            nifti_file, subject_id, use_docker=self.use_docker
        )

        if freesurfer_result["status"] != "completed":
            results["status"] = "failed"
            results["errors"].append(f"FreeSurfer processing failed: {freesurfer_result.get('stderr')}")
            results["freesurfer_result"] = freesurfer_result
            return results

        # Step 3: Extract metrics
        logger.info(f"Step 4: Extracting metrics for {subject_id}")
        try:
            metrics_df = self.stats_parser.extract_all_metrics(subject_id)
        except Exception as e:
            results["status"] = "failed"
            results["errors"].append(f"Metrics extraction failed: {e}")
            return results

        # Step 4: Load into database
        logger.info(f"Step 5: Loading metrics into database for {subject_id}")
        try:
            volumetric_id = self.db_loader.load_metrics(
                metrics_df,
                subject_id,
                processing_status="completed",
                processing_runtime=freesurfer_result["runtime_seconds"],
                nifti_path=str(nifti_file),
                freesurfer_output_dir=freesurfer_result["output_dir"],
            )
            results["volumetric_id"] = volumetric_id
        except Exception as e:
            results["status"] = "failed"
            results["errors"].append(f"Database loading failed: {e}")
            return results

        results["status"] = "completed"
        results["metrics"] = metrics_df.to_dict("records")[0]
        results["freesurfer_result"] = freesurfer_result

        logger.info(f"Pipeline completed successfully for {subject_id}")
        return results
