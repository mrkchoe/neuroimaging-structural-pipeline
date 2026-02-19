.PHONY: help setup-db start-db stop-db init-db test lint clean run-pipeline

help:
	@echo "Neuroimaging Structural Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  setup-db     - Start PostgreSQL database"
	@echo "  stop-db      - Stop PostgreSQL database"
	@echo "  init-db      - Initialize database schema"
	@echo "  test         - Run unit tests"
	@echo "  lint         - Run linting checks"
	@echo "  clean        - Clean temporary files"
	@echo "  run-pipeline - Run pipeline on sample data (requires DICOM_DIR and SUBJECT_ID)"

setup-db:
	docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 5

stop-db:
	docker-compose down

init-db:
	python -m src.database.init_db

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	black --check src/ tests/
	mypy src/

format:
	black src/ tests/

run-pipeline:
	@if [ -z "$(DICOM_DIR)" ] || [ -z "$(SUBJECT_ID)" ]; then \
		echo "Error: DICOM_DIR and SUBJECT_ID must be set"; \
		echo "Usage: make run-pipeline DICOM_DIR=/path/to/dicom SUBJECT_ID=sub-001"; \
		exit 1; \
	fi
	python -m src.cli run \
		--dicom-dir $(DICOM_DIR) \
		--subject-id $(SUBJECT_ID) \
		--database-url $$(python -c "from src.config import get_database_url; print(get_database_url())")

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
