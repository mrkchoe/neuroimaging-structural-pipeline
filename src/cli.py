"""Command-line interface for the pipeline."""

import logging
from pathlib import Path

import click

from .config import (
    get_database_url,
    get_subjects_dir,
    get_freesurfer_home,
    get_use_docker,
)
from .database.loader import DatabaseLoader
from .pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Neuroimaging Structural Pipeline CLI."""
    pass


@cli.command()
@click.option(
    "--dicom-dir", required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option("--subject-id", required=True, type=str)
@click.option("--database-url", type=str, default=None)
@click.option("--output-dir", type=click.Path(path_type=Path), default=None)
def run(dicom_dir: Path, subject_id: str, database_url: str, output_dir: Path):
    """Run the full pipeline for a subject."""
    database_url = database_url or get_database_url()

    pipeline = Pipeline(
        database_url=database_url,
        subjects_dir=get_subjects_dir(),
        freesurfer_home=get_freesurfer_home(),
        use_docker=get_use_docker(),
    )

    results = pipeline.run(dicom_dir, subject_id, output_dir)

    if results["status"] == "completed":
        click.echo(f"✓ Pipeline completed successfully for {subject_id}")
        click.echo(f"  Volumetric ID: {results.get('volumetric_id')}")
    else:
        click.echo(f"✗ Pipeline failed for {subject_id}")
        for error in results.get("errors", []):
            click.echo(f"  Error: {error}")
        raise click.Abort()


@cli.command()
@click.option("--database-url", type=str, default=None)
def init_db(database_url: str):
    """Initialize database schema."""
    database_url = database_url or get_database_url()
    loader = DatabaseLoader(database_url)
    loader.create_tables()
    click.echo("✓ Database schema initialized")


if __name__ == "__main__":
    cli()
