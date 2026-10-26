"""CLI script to idempotently seed OrbitOps virtual constellation."""

import logging
import sys

from app.db.bootstrap import seed_virtual_constellation
from app.db.session import get_db_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("orbitops.cli.seed")


def main() -> None:
    """Run idempotent seed routine."""
    logger.info("Initializing database seed for OrbitOps virtual constellation...")
    try:
        with get_db_context() as session:
            result = seed_virtual_constellation(session)
            logger.info("Seed completed successfully: %s", result)
    except Exception as e:
        logger.error("Failed to seed database: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
