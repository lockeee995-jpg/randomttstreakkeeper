"""Логирование в консоль и файл."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOGGER_NAME = "tiktok_streak"


def setup_logger(log_file: str | Path = "streak.log") -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:  # не дублируем обработчики при повторном вызове
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    try:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # нет прав на запись файла — пишем только в консоль

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)
