import logging

from app.config import get_settings

settings = get_settings()

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(settings.log_level)

        handler = logging.StreamHandler()
        handler.setLevel(settings.log_level)

        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        logger.propagate = False

    return logger