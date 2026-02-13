"""Unit tests for DICOM processor."""

import tempfile
from pathlib import Path

import pytest

from src.ingestion.dicom_processor import DicomProcessor


def test_validate_modality_no_files():
    """Test validation with no DICOM files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processor = DicomProcessor()
        is_valid, error_msg = processor.validate_modality(Path(tmpdir))
        assert not is_valid
        assert "No DICOM files found" in error_msg


def test_dicom_processor_init():
    """Test DICOM processor initialization."""
    processor = DicomProcessor(dcm2niix_path="dcm2niix")
    assert processor.dcm2niix_path == "dcm2niix"
