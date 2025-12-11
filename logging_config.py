import logging
from loguru import logger
from .config import settings


def setup_logging() -> None:
    # Standard logging for uvicorn / FastAPI
    logging.basicConfig(level=logging.INFO)

    # Loguru JSON logs
    logger.add(
        settings.log_file,
        serialize=True,
        rotation="1 MB",
        retention="7 days",
        enqueue=True,
    )
