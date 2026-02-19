"""Unit tests for stats parser."""

import tempfile
from pathlib import Path

import pytest

from src.extraction.stats_parser import StatsParser


@pytest.fixture
def sample_aseg_stats():
    """Sample aseg.stats content."""
    return """# Measure Intracranial Vol, ICV, Intracranial Volume
# ColHeaders  Index SegId NVoxels Volume_mm3 StructName Mean StdDev Min Max Range
  1    4  12345  1234567.89  Left-Lateral-Ventricle 0.0 0.0 0.0 0.0 0.0
  2   10  23456  2345678.90  Left-Thalamus-Proper 0.0 0.0 0.0 0.0 0.0
  3   17  34567  3456789.01  Left-Hippocampus 0.0 0.0 0.0 0.0 0.0
  4   18  45678  4567890.12  Left-Amygdala 0.0 0.0 0.0 0.0 0.0
  5   53  56789  5678901.23  Right-Hippocampus 0.0 0.0 0.0 0.0 0.0
  6   54  67890  6789012.34  Right-Amygdala 0.0 0.0 0.0 0.0 0.0
# Intracranial Vol = 1500000.00 mm^3
"""


@pytest.fixture
def sample_aparc_stats():
    """Sample aparc.stats content."""
    return """# Measure Cortex, MeanThickness, mean thickness
# ColHeaders  StructName NumVert SurfArea GrayVol ThickAvg ThickStd MeanCurv GausCurv FoldInd CurvInd
# TableCol  1  StructName  string
# TableCol  2  NumVert  int
# TableCol  3  SurfArea  float
# TableCol  4  GrayVol  float
# TableCol  5  ThickAvg  float
# TableCol  6  ThickStd  float
# TableCol  7  MeanCurv  float
# TableCol  8  GausCurv  float
# TableCol  9  FoldInd  int
# TableCol  10  CurvInd  float
# N TableCols 10
# N TableRows 34
# TableEnd
# mean thickness = 2.45 mm
# total surface area = 123456.78 mm^2
# total gray matter volume = 234567.89 mm^3
"""


@pytest.fixture
def temp_subjects_dir(sample_aseg_stats, sample_aparc_stats):
    """Create temporary subjects directory with sample stats files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subjects_dir = Path(tmpdir)
        subject_dir = subjects_dir / "test_subject" / "stats"
        subject_dir.mkdir(parents=True)

        # Write aseg.stats
        (subject_dir / "aseg.stats").write_text(sample_aseg_stats)

        # Write aparc.stats
        (subject_dir / "lh.aparc.stats").write_text(sample_aparc_stats)
        (subject_dir / "rh.aparc.stats").write_text(sample_aparc_stats)

        yield subjects_dir


def test_parse_aseg_stats(temp_subjects_dir):
    """Test parsing aseg.stats file."""
    parser = StatsParser(str(temp_subjects_dir))
    metrics = parser.parse_aseg_stats("test_subject")

    assert "icv" in metrics
    assert metrics["icv"] == 1500000.00
    assert "hippocampus_left" in metrics
    assert "hippocampus_right" in metrics
    assert "amygdala_left" in metrics
    assert "amygdala_right" in metrics


def test_parse_aparc_stats(temp_subjects_dir):
    """Test parsing aparc.stats files."""
    parser = StatsParser(str(temp_subjects_dir))
    metrics = parser.parse_aparc_stats("test_subject", hemi="both")

    assert "mean_thickness_lh" in metrics
    assert metrics["mean_thickness_lh"] == 2.45
    assert "mean_thickness_rh" in metrics
    assert "total_area_lh" in metrics
    assert "total_area_rh" in metrics
    assert "gray_volume_lh" in metrics
    assert "gray_volume_rh" in metrics


def test_extract_all_metrics(temp_subjects_dir):
    """Test extracting all metrics as DataFrame."""
    import pandas as pd

    parser = StatsParser(str(temp_subjects_dir))
    df = parser.extract_all_metrics("test_subject")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["subject_id"] == "test_subject"
    assert "icv" in df.columns
    assert "hippocampus_left" in df.columns
