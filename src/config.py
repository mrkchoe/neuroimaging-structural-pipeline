"""Configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_database_url() -> str:
    """Get PostgreSQL database URL from environment variables."""
    user = os.getenv("POSTGRES_USER", "neuroimaging")
    password = os.getenv("POSTGRES_PASSWORD", "neuroimaging")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "neuroimaging")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def get_freesurfer_home() -> str:
    """Get FreeSurfer home directory."""
    return os.getenv("FREESURFER_HOME", "/opt/freesurfer")


def get_subjects_dir() -> str:
    """Get FreeSurfer subjects directory."""
    return os.getenv("SUBJECTS_DIR", "/data/freesurfer/subjects")


def get_nifti_output_dir() -> Path:
    """Get NIfTI output directory."""
    return Path(os.getenv("NIFTI_OUTPUT_DIR", "/tmp/nifti_output"))


def get_use_docker() -> bool:
    """Get whether to use Docker for FreeSurfer."""
    return os.getenv("USE_DOCKER", "true").lower() == "true"


def get_docker_image() -> str:
    """Get Docker image for FreeSurfer."""
    return os.getenv("DOCKER_IMAGE", "freesurfer/freesurfer:latest")
