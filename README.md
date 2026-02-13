# Neuroimaging Structural Pipeline

Production-style structural MRI processing pipeline that ingests T1-weighted DICOM images, runs FreeSurfer cortical reconstruction, and loads volumetric outputs into a relational database for downstream analytics.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DICOM Input                              │
│                    (T1-weighted MRI scans)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION MODULE                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DicomProcessor                                           │  │
│  │  • Validate modality (T1 structural)                     │  │
│  │  • Convert DICOM → NIfTI (dcm2niix)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING MODULE                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FreeSurferRunner                                         │  │
│  │  • Run recon-all via Docker                               │  │
│  │  • Track runtime and status                               │  │
│  │  • Output: FreeSurfer subject directory                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACTION MODULE                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  StatsParser                                             │  │
│  │  • Parse aseg.stats (subcortical volumes)               │  │
│  │  • Parse aparc.stats (cortical thickness)                │  │
│  │  • Extract: ICV, hippocampus, amygdala, thickness       │  │
│  │  • Output: Tidy pandas DataFrame                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE MODULE                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DatabaseLoader                                          │  │
│  │  • SQLAlchemy ORM                                        │  │
│  │  • Normalized schema:                                    │  │
│  │    - subjects (subject metadata)                         │  │
│  │    - scans (scan sessions)                               │  │
│  │    - volumetrics (measurements)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│              (Structured volumetric data)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Modular Architecture**: Clear separation of concerns across ingestion, processing, extraction, and loading
- **DICOM Validation**: Ensures T1-weighted structural scans before processing
- **Containerized Processing**: FreeSurfer runs in Docker for reproducibility
- **Robust Extraction**: Parses FreeSurfer stats files for key neuroimaging metrics
- **Normalized Database**: Relational schema for scalable data management
- **Production Ready**: Logging, error handling, and CI/CD integration

## Project Structure

```
neuroimaging-structural-pipeline/
├── src/
│   ├── __init__.py
│   ├── pipeline.py              # Main orchestration
│   ├── config.py                # Configuration management
│   ├── cli.py                   # Command-line interface
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── dicom_processor.py   # DICOM validation & conversion
│   ├── processing/
│   │   ├── __init__.py
│   │   └── freesurfer_runner.py # FreeSurfer execution
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── stats_parser.py      # Stats file parsing
│   └── database/
│       ├── __init__.py
│       ├── models.py            # SQLAlchemy models
│       ├── loader.py            # Database loading
│       └── init_db.py           # Schema initialization
├── tests/
│   ├── test_stats_parser.py
│   └── test_dicom_processor.py
├── .github/workflows/
│   └── ci.yml                   # GitHub Actions CI
├── Dockerfile                   # FreeSurfer container
├── docker-compose.yml           # PostgreSQL service
├── Makefile                     # Orchestration commands
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- dcm2niix (for DICOM conversion)
- FreeSurfer license file (required for FreeSurfer processing)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd neuroimaging-structural-pipeline
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL:**
   ```bash
   make setup-db
   make init-db
   ```

## Usage

### Running the Pipeline

Process a single subject's DICOM data:

```bash
python -m src.cli run \
    --dicom-dir /path/to/dicom \
    --subject-id sub-001
```

Or using Make:

```bash
make run-pipeline DICOM_DIR=/path/to/dicom SUBJECT_ID=sub-001
```

### Programmatic Usage

```python
from pathlib import Path
from src.pipeline import Pipeline
from src.config import get_database_url

pipeline = Pipeline(
    database_url=get_database_url(),
    subjects_dir="/data/freesurfer/subjects",
    use_docker=True
)

results = pipeline.run(
    dicom_dir=Path("/path/to/dicom"),
    subject_id="sub-001"
)
```

## Database Schema

### Subjects Table
- `id`: Primary key
- `subject_id`: Unique subject identifier
- `created_at`: Timestamp

### Scans Table
- `id`: Primary key
- `subject_id`: Foreign key to subjects
- `scan_date`: Date of scan
- `modality`: Imaging modality (default: T1w)
- `nifti_path`: Path to converted NIfTI file
- `processing_status`: Status (pending/completed/failed)
- `processing_runtime_seconds`: Processing time
- `freesurfer_output_dir`: FreeSurfer output directory

### Volumetrics Table
- `id`: Primary key
- `subject_id`: Foreign key to subjects
- `scan_id`: Foreign key to scans
- `icv`: Intracranial volume (mm³)
- `hippocampus_left`, `hippocampus_right`: Hippocampal volumes (mm³)
- `amygdala_left`, `amygdala_right`: Amygdala volumes (mm³)
- `mean_thickness_lh`, `mean_thickness_rh`: Mean cortical thickness (mm)
- `total_area_lh`, `total_area_rh`: Total surface area (mm²)
- `gray_volume_lh`, `gray_volume_rh`: Gray matter volume (mm³)

## Extracted Metrics

The pipeline extracts the following neuroimaging metrics:

### Subcortical Volumes (from aseg.stats)
- Intracranial Volume (ICV)
- Left/Right Hippocampus
- Left/Right Amygdala

### Cortical Metrics (from aparc.stats)
- Mean cortical thickness (left/right hemispheres)
- Total surface area (left/right hemispheres)
- Total gray matter volume (left/right hemispheres)

## Docker Configuration

### FreeSurfer Container

The pipeline uses a Docker container for FreeSurfer processing. Ensure you have:
- FreeSurfer license file mounted at `/opt/freesurfer/license.txt`
- Sufficient disk space for FreeSurfer outputs (~1-2 GB per subject)

### PostgreSQL Container

PostgreSQL runs via docker-compose. Default configuration:
- User: `neuroimaging`
- Password: `neuroimaging`
- Database: `neuroimaging`
- Port: `5432`

## Development

### Running Tests

```bash
make test
```

### Linting

```bash
make lint
```

### Formatting

```bash
make format
```

## CI/CD

GitHub Actions workflow runs on push/PR:
- Linting (flake8, black, mypy)
- Unit tests (pytest with coverage)
- Database integration tests

Note: FreeSurfer execution is skipped in CI due to resource constraints.

## Sample Dataset Structure

For testing, organize DICOM data as follows:

```
sample_data/
├── sub-001/
│   └── dicom/
│       ├── IMG_0001.dcm
│       ├── IMG_0002.dcm
│       └── ...
├── sub-002/
│   └── dicom/
│       └── ...
└── ...
```

## Troubleshooting

### FreeSurfer License
Ensure FreeSurfer license is available:
- In Docker: Mount license file or set `FS_LICENSE` environment variable
- Native: Place license at `$FREESURFER_HOME/license.txt`

### Database Connection
Verify PostgreSQL is running:
```bash
docker-compose ps
```

### DICOM Conversion
Ensure `dcm2niix` is installed and in PATH:
```bash
which dcm2niix
```

## License

[Specify your license]

## Contributing

[Contributing guidelines]

## Citation

If you use this pipeline in your research, please cite:

[Citation information]
