"""Application logging configuration."""

import logging
import sys
from pathlib import Path

from app.config.settings import settings


def setup_logging() -> logging.Logger:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)

    logger = logging.getLogger("ahsteellab")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
