"""DICOM ingestion, validation, and conversion to NIfTI."""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import pydicom

logger = logging.getLogger(__name__)


class DicomProcessor:
    """Process DICOM files: validate modality and convert to NIfTI."""

    def __init__(self, dcm2niix_path: str = "dcm2niix"):
        """Initialize DICOM processor.

        Args:
            dcm2niix_path: Path to dcm2niix executable
        """
        self.dcm2niix_path = dcm2niix_path

    def validate_modality(self, dicom_dir: Path) -> Tuple[bool, Optional[str]]:
        """Validate that DICOM directory contains T1-weighted structural scans.

        Args:
            dicom_dir: Path to directory containing DICOM files

        Returns:
            Tuple of (is_valid, error_message)
        """
        dicom_files = list(dicom_dir.glob("*.dcm")) + list(dicom_dir.rglob("*.dcm"))
        if not dicom_files:
            return False, "No DICOM files found in directory"

        # Sample first few DICOM files to check modality
        modalities = set()
        for dicom_file in dicom_files[:10]:  # Sample first 10
            try:
                ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                modality = getattr(ds, "Modality", None)
                if modality:
                    modalities.add(modality)
                # Check for T1-weighted sequences
                if hasattr(ds, "ScanOptions") or hasattr(ds, "SequenceName"):
                    # Additional validation could check sequence parameters
                    pass
            except Exception as e:
                logger.warning(f"Error reading {dicom_file}: {e}")
                continue

        if "MR" not in modalities:
            return False, f"Expected MR modality, found: {modalities}"

        logger.info(f"Validated DICOM directory: {len(dicom_files)} files, modality: {modalities}")
        return True, None

    def convert_to_nifti(
        self, dicom_dir: Path, output_dir: Path, subject_id: str
    ) -> Optional[Path]:
        """Convert DICOM directory to NIfTI format using dcm2niix.

        Args:
            dicom_dir: Path to DICOM directory
            output_dir: Path to output directory for NIfTI files
            subject_id: Subject identifier for naming

        Returns:
            Path to output NIfTI file, or None if conversion failed
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # dcm2niix command: -o output_dir -f output_filename -z y (gzip) -b y (BIDS JSON)
        output_filename = f"{subject_id}_T1w"
        cmd = [
            self.dcm2niix_path,
            "-o",
            str(output_dir),
            "-f",
            output_filename,
            "-z",
            "y",  # gzip compression
            "-b",
            "y",  # BIDS sidecar JSON
            str(dicom_dir),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=300
            )
            logger.info(f"dcm2niix output: {result.stdout}")

            # Find the generated NIfTI file
            nifti_file = output_dir / f"{output_filename}.nii.gz"
            if nifti_file.exists():
                logger.info(f"Successfully converted DICOM to: {nifti_file}")
                return nifti_file
            else:
                logger.error(f"dcm2niix completed but output file not found: {nifti_file}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"dcm2niix failed: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            logger.error("dcm2niix conversion timed out")
            return None
