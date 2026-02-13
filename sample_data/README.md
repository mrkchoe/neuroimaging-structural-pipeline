# Sample Dataset Structure

This directory should contain sample DICOM data for testing the pipeline.

## Directory Structure

```
sample_data/
├── sub-001/
│   └── dicom/
│       ├── IMG_0001.dcm
│       ├── IMG_0002.dcm
│       └── ... (additional DICOM files)
├── sub-002/
│   └── dicom/
│       └── ...
└── ...
```

## Requirements

- DICOM files must be T1-weighted structural MRI scans
- Files should have `.dcm` extension
- Each subject should have a unique identifier (e.g., `sub-001`)

## Usage

To process sample data:

```bash
python -m src.cli run \
    --dicom-dir sample_data/sub-001/dicom \
    --subject-id sub-001
```

## Note

This directory is excluded from version control. Add your own DICOM data here for testing.
