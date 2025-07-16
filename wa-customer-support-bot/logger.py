# Path: app/logger.py

from functools import lru_cache
import logging
import logging.config
from colorlog import ColoredFormatter

@lru_cache
def get_logger():
    """Get a logger instance."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(asctime)s - %(filename)s - %(levelname)s - %(message)s [line: %(lineno)d]",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "access": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(asctime)s - %(filename)s - %(levelname)s - %(message)s [line: %(lineno)d]",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "log_colors": {"INFO": "green", "WARNING": "yellow", "ERROR": "red"},
            },
            "file": {
                "format": "%(asctime)s - %(filename)s - %(levelname)s - %(message)s [line: %(lineno)d]",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "file",
                "class": "logging.FileHandler",
                "filename": "app.log",  # Change to your desired log file path
                "mode": "a",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {"handlers": ["default", "file"], "level": "DEBUG"},
            "uvicorn.error": {
                "handlers": ["default", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn.access": {"handlers": ["access", "file"], "level": "INFO", "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)

    return logger
