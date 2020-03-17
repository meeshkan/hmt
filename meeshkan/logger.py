import logging
import logging.config
from typing import List

from .config import setup

# Do not expose anything by default (internal module)
__all__ = []  # type: List[str]

# Loggers cached by name
_loggers = {}


def get(name):
    setup()  # Setup needed before creating any loggers
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger
