"""SQLAlchemy models for neuroimaging database schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Subject(Base):
    """Subject table."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scans = relationship("Scan", back_populates="subject", cascade="all, delete-orphan")
    volumetrics = relationship(
        "Volumetric", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Subject(subject_id='{self.subject_id}')>"


class Scan(Base):
    """Scan table - tracks individual imaging sessions."""

    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(100), ForeignKey("subjects.subject_id"), nullable=False, index=True)
    scan_date = Column(DateTime, nullable=True)
    modality = Column(String(50), nullable=False, default="T1w")
    nifti_path = Column(String(500), nullable=True)
    processing_status = Column(String(50), nullable=False, default="pending")
    processing_runtime_seconds = Column(Float, nullable=True)
    freesurfer_output_dir = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    subject = relationship("Subject", back_populates="scans")

    def __repr__(self):
        return f"<Scan(subject_id='{self.subject_id}', status='{self.processing_status}')>"


class Volumetric(Base):
    """Volumetric measurements table."""

    __tablename__ = "volumetrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(100), ForeignKey("subjects.subject_id"), nullable=False, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)

    # Subcortical volumes (mm^3)
    icv = Column(Float, nullable=True, comment="Intracranial volume")
    hippocampus_left = Column(Float, nullable=True)
    hippocampus_right = Column(Float, nullable=True)
    amygdala_left = Column(Float, nullable=True)
    amygdala_right = Column(Float, nullable=True)

    # Cortical metrics
    mean_thickness_lh = Column(Float, nullable=True, comment="Left hemisphere mean thickness (mm)")
    mean_thickness_rh = Column(Float, nullable=True, comment="Right hemisphere mean thickness (mm)")
    total_area_lh = Column(Float, nullable=True, comment="Left hemisphere total area (mm^2)")
    total_area_rh = Column(Float, nullable=True, comment="Right hemisphere total area (mm^2)")
    gray_volume_lh = Column(Float, nullable=True, comment="Left hemisphere gray matter volume (mm^3)")
    gray_volume_rh = Column(Float, nullable=True, comment="Right hemisphere gray matter volume (mm^3)")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subject = relationship("Subject", back_populates="volumetrics")
    scan = relationship("Scan")

    def __repr__(self):
        return f"<Volumetric(subject_id='{self.subject_id}')>"
