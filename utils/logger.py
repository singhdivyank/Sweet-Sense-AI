"""
Centralised logging configuration for the Sweet-Sense-AI project.

Features
--------
  - Structured log format with timestamp, level, module, and line number
  - Simultaneous console + rotating file output
  - Per-module logger retrieval via get_logger()
  - Environment-aware log level (LOG_LEVEL env var, default INFO)
  - One-line setup: from logger import get_logger; log = get_logger(__name__)
"""

import logging
from logging.handlers import RotatingFileHandler

from .settings import get_settings


class ConfigLogger:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._get_log_settings()
        self._get_console_handler()
        self._set_file_handler()
        self._configure_root_logger()

    def _get_log_settings(self) -> None:
        self.log_level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        self.log_file = self.settings.log_file
        self.max_bytes = self.settings.max_bytes
        self.backup_counts = self.settings.backup_counts
        self.formatter = logging.Formatter(
            fmt=self.settings.log_format, datefmt=self.settings.date_format
        )

    def _get_console_handler(self) -> None:
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(self.log_level)
        self.console_handler.setFormatter(self.formatter)

    def _set_file_handler(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.file_handler = RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_counts,
            encoding="utf-8",
        )
        self.file_handler.setLevel(self.log_level)
        self.file_handler.setFormatter(self.formatter)

    def _configure_root_logger(self) -> None:
        """
        Attach a console handler and a rotating file handler to the root logger.
        Called once when this module is first imported
        """

        root = logging.getLogger()
        if root.handlers:
            return

        root.setLevel(self.log_level)
        root.addHandler(self.console_handler)
        root.addHandler(self.file_handler)


ConfigLogger()


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-level logger.

    Parameters
    ----------
    name : str
        Typically ``__name__`` of the calling module, which produces
        a hierarchy like ``data_pipeline`` or ``train_xgboost``.

    Returns
    -------
    logging.Logger
    """

    return logging.getLogger(name)
