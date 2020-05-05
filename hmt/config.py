import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

DEFAULT_SPECS_DIR = "specs/"

PACKAGE_PATH = Path(os.path.dirname(os.path.realpath(__file__)))  # type: Path

LOG_CONFIG_FILE = PACKAGE_PATH.joinpath("logging.yaml")

BASE_DIR = Path.home().joinpath(".hmt")
LOGS_DIR = BASE_DIR.joinpath("logs")


# Don't automatically expose anything to top level, as the entire module is loaded as-is
__all__ = []  # type: List[str]

_SETUP_DONE = False


def _ensure_base_dirs(verbose=True):
    def create_dir_if_not_exist(path: Path):
        if not path.is_dir():
            # Print instead of logging as loggers may not have been configured yet
            if verbose:
                print("Creating directory {path}".format(path=path))
            path.mkdir()

    create_dir_if_not_exist(BASE_DIR)
    create_dir_if_not_exist(LOGS_DIR)


def _setup_logging(log_config: Path = LOG_CONFIG_FILE, silent: bool = False) -> None:
    """Setup logging configuration. This must be done before creating loggers.

    Keyword Arguments:
        log_config {Path} -- Path to logging configuration YAML (default: {LOG_CONFIG_FILE})
        silent {bool} -- Whether to remove non-file logging handlers or not. (default: {False})

    """

    if not log_config.is_file():
        raise RuntimeError(
            "Logging file {log_file} not found".format(log_file=log_config)
        )

    with log_config.open() as log_file:
        config_orig = yaml.safe_load(log_file.read())  # type: Any

    def prepare_filenames(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepend `LOGS_DIR` to all 'filename' attributes listed for handlers in logging.yaml
        :param config: Configuration dictionary
        :return: Configuration with 'filename's prepended with LOGS_DIR
        """
        for handler_name in config["handlers"].keys():
            handler_config = config["handlers"][handler_name]
            if "filename" in handler_config:
                filename = Path(handler_config["filename"]).name
                handler_config["filename"] = str(LOGS_DIR.joinpath(filename))
        return config

    config = prepare_filenames(config_orig)
    # for some reason, pyright fails with "'config' is not a known member of module"
    # even though this is an officially documented member of logging
    # for now we ignore the type
    logging.config.dictConfig(config)  # type: ignore
    if silent:
        _remove_non_file_handlers()


def _remove_non_file_handlers():
    root_logger = logging.getLogger()  # Root logger
    for handler in root_logger.handlers.copy():
        if not isinstance(handler, logging.FileHandler):
            root_logger.handlers.remove(handler)


def setup(verbose=True):
    """
    Setup Meeshkan CLI by ensuring necessary directories exist and loggers have been configured.

    Keyword Arguments:
        verbose {bool} -- Verbose mode or not (default: {True})
    """
    global _SETUP_DONE
    if _SETUP_DONE:
        return
    _ensure_base_dirs(verbose=False)
    _setup_logging()
    _SETUP_DONE = True
