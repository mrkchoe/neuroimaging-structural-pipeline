"""Database loading utilities."""

import logging
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Scan, Subject, Volumetric

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load extracted metrics into PostgreSQL database."""

    def __init__(self, database_url: str):
        """Initialize database loader.

        Args:
            database_url: SQLAlchemy database URL (e.g., postgresql://user:pass@host/db)
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

    def load_metrics(
        self,
        metrics_df: pd.DataFrame,
        subject_id: str,
        scan_id: Optional[int] = None,
        processing_status: str = "completed",
        processing_runtime: Optional[float] = None,
        nifti_path: Optional[str] = None,
        freesurfer_output_dir: Optional[str] = None,
    ) -> int:
        """Load metrics DataFrame into database.

        Args:
            metrics_df: DataFrame with volumetric metrics (one row per subject)
            subject_id: Subject identifier
            scan_id: Optional scan ID to link volumetric to scan
            processing_status: Processing status for scan record
            processing_runtime: Processing runtime in seconds
            nifti_path: Path to NIfTI file
            freesurfer_output_dir: Path to FreeSurfer output directory

        Returns:
            ID of created volumetric record
        """
        session = self.Session()

        try:
            # Get or create subject
            subject = session.query(Subject).filter_by(subject_id=subject_id).first()
            if not subject:
                subject = Subject(subject_id=subject_id)
                session.add(subject)
                session.flush()
                logger.info(f"Created new subject: {subject_id}")
            else:
                logger.info(f"Found existing subject: {subject_id}")

            # Create scan record if not provided
            if scan_id is None:
                scan = Scan(
                    subject_id=subject_id,
                    modality="T1w",
                    processing_status=processing_status,
                    processing_runtime_seconds=processing_runtime,
                    nifti_path=nifti_path,
                    freesurfer_output_dir=freesurfer_output_dir,
                )
                session.add(scan)
                session.flush()
                scan_id = scan.id

            # Extract metrics from DataFrame (should be single row)
            if len(metrics_df) != 1:
                raise ValueError(f"Expected single row DataFrame, got {len(metrics_df)}")

            row = metrics_df.iloc[0]

            # Create volumetric record
            volumetric = Volumetric(
                subject_id=subject_id,
                scan_id=scan_id,
                icv=row.get("icv"),
                hippocampus_left=row.get("hippocampus_left"),
                hippocampus_right=row.get("hippocampus_right"),
                amygdala_left=row.get("amygdala_left"),
                amygdala_right=row.get("amygdala_right"),
                mean_thickness_lh=row.get("mean_thickness_lh"),
                mean_thickness_rh=row.get("mean_thickness_rh"),
                total_area_lh=row.get("total_area_lh"),
                total_area_rh=row.get("total_area_rh"),
                gray_volume_lh=row.get("gray_volume_lh"),
                gray_volume_rh=row.get("gray_volume_rh"),
            )

            session.add(volumetric)
            session.commit()

            logger.info(f"Loaded metrics for subject {subject_id}, volumetric_id={volumetric.id}")
            return volumetric.id

        except Exception as e:
            session.rollback()
            logger.error(f"Error loading metrics: {e}")
            raise
        finally:
            session.close()
