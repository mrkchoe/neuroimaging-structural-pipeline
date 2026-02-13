"""Parse FreeSurfer stats files and extract volumetric metrics."""

import logging
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class StatsParser:
    """Parse FreeSurfer aseg.stats and aparc.stats files."""

    def __init__(self, subjects_dir: str):
        """Initialize stats parser.

        Args:
            subjects_dir: FreeSurfer subjects directory
        """
        self.subjects_dir = Path(subjects_dir)

    def parse_aseg_stats(self, subject_id: str) -> Dict[str, float]:
        """Parse aseg.stats file for subcortical volumes.

        Args:
            subject_id: Subject identifier

        Returns:
            Dictionary of volumetric metrics
        """
        aseg_file = self.subjects_dir / subject_id / "stats" / "aseg.stats"
        if not aseg_file.exists():
            logger.error(f"aseg.stats not found: {aseg_file}")
            return {}

        metrics = {}
        with open(aseg_file, "r") as f:
            content = f.read()

        # Extract intracranial volume (ICV)
        # Format: "# Intracranial Vol = 1500000.00 mm^3"
        icv_match = re.search(r"Intracranial Vol\s*=\s*([\d.]+)", content, re.IGNORECASE)
        if icv_match:
            metrics["icv"] = float(icv_match.group(1))

        # Parse tab-separated table for structure volumes
        # Format: Index SegId NVoxels Volume_mm3 StructName ...
        lines = content.split("\n")
        in_table = False
        for line in lines:
            if "ColHeaders" in line and "StructName" in line:
                in_table = True
                continue
            if in_table and line.strip() and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 5:
                    struct_name = parts[4]  # StructName column
                    volume = parts[3]  # Volume_mm3 column
                    try:
                        vol_float = float(volume)
                        if "Left-Hippocampus" in struct_name or struct_name == "Left-Hippocampus":
                            metrics["hippocampus_left"] = vol_float
                        elif "Right-Hippocampus" in struct_name or struct_name == "Right-Hippocampus":
                            metrics["hippocampus_right"] = vol_float
                        elif "Left-Amygdala" in struct_name or struct_name == "Left-Amygdala":
                            metrics["amygdala_left"] = vol_float
                        elif "Right-Amygdala" in struct_name or struct_name == "Right-Amygdala":
                            metrics["amygdala_right"] = vol_float
                    except (ValueError, IndexError):
                        continue

        # Fallback: try regex patterns if table parsing didn't work
        if "hippocampus_left" not in metrics:
            lh_hippo_match = re.search(
                r"Left-Hippocampus[^\d]*(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.MULTILINE
            )
            if lh_hippo_match:
                metrics["hippocampus_left"] = float(lh_hippo_match.group(1))

        if "hippocampus_right" not in metrics:
            rh_hippo_match = re.search(
                r"Right-Hippocampus[^\d]*(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.MULTILINE
            )
            if rh_hippo_match:
                metrics["hippocampus_right"] = float(rh_hippo_match.group(1))

        if "amygdala_left" not in metrics:
            lh_amyg_match = re.search(
                r"Left-Amygdala[^\d]*(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.MULTILINE
            )
            if lh_amyg_match:
                metrics["amygdala_left"] = float(lh_amyg_match.group(1))

        if "amygdala_right" not in metrics:
            rh_amyg_match = re.search(
                r"Right-Amygdala[^\d]*(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.MULTILINE
            )
            if rh_amyg_match:
                metrics["amygdala_right"] = float(rh_amyg_match.group(1))

        logger.info(f"Parsed aseg.stats for {subject_id}: {len(metrics)} metrics")
        return metrics

    def parse_aparc_stats(self, subject_id: str, hemi: str = "both") -> Dict[str, float]:
        """Parse aparc.stats files for cortical thickness metrics.

        Args:
            subject_id: Subject identifier
            hemi: Hemisphere ('lh', 'rh', or 'both')

        Returns:
            Dictionary of cortical thickness metrics
        """
        metrics = {}
        hemispheres = ["lh", "rh"] if hemi == "both" else [hemi]

        for h in hemispheres:
            aparc_file = self.subjects_dir / subject_id / "stats" / f"{h}.aparc.stats"
            if not aparc_file.exists():
                logger.warning(f"{h}.aparc.stats not found: {aparc_file}")
                continue

            with open(aparc_file, "r") as f:
                content = f.read()

            # Extract mean thickness
            mean_thick_match = re.search(
                r"mean thickness\s+=\s+([\d.]+)\s+mm", content, re.IGNORECASE
            )
            if mean_thick_match:
                metrics[f"mean_thickness_{h}"] = float(mean_thick_match.group(1))

            # Extract total surface area
            total_area_match = re.search(
                r"total surface area\s+=\s+([\d.]+)\s+mm\^2", content, re.IGNORECASE
            )
            if total_area_match:
                metrics[f"total_area_{h}"] = float(total_area_match.group(1))

            # Extract total gray matter volume
            grayvol_match = re.search(
                r"total gray matter volume\s+=\s+([\d.]+)\s+mm\^3", content, re.IGNORECASE
            )
            if grayvol_match:
                metrics[f"gray_volume_{h}"] = float(grayvol_match.group(1))

        logger.info(f"Parsed aparc.stats for {subject_id}: {len(metrics)} metrics")
        return metrics

    def extract_all_metrics(self, subject_id: str) -> pd.DataFrame:
        """Extract all metrics and return as tidy DataFrame.

        Args:
            subject_id: Subject identifier

        Returns:
            DataFrame with one row per subject
        """
        aseg_metrics = self.parse_aseg_stats(subject_id)
        aparc_metrics = self.parse_aparc_stats(subject_id)

        # Combine all metrics
        all_metrics = {**aseg_metrics, **aparc_metrics}
        all_metrics["subject_id"] = subject_id

        # Convert to DataFrame
        df = pd.DataFrame([all_metrics])

        return df
