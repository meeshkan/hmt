import logging
import logging.config as config

_loggers = {}


def get(name):
    if name in _loggers:
        return _loggers[name]
    config.fileConfig(fname='logging.conf',
                      disable_existing_loggers=False)
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger
