"""Initialize database schema."""

import logging
import sys

from .loader import DatabaseLoader
from ..config import get_database_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Create database tables."""
    database_url = get_database_url()
    loader = DatabaseLoader(database_url)
    loader.create_tables()
    logger.info("Database initialization complete")


if __name__ == "__main__":
    main()
