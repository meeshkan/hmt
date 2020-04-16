"""Code for writing builder results to file system.
"""
import json
from pathlib import Path
from typing import cast

from openapi_typed_2 import OpenAPIObject, convert_from_openapi

from ..logger import get as getLogger
from .result import BuildResult

LOGGER = getLogger(__name__)


OPENAPI_FILENAME = "openapi.json"


def _ensure_dir_exists(path: Path) -> None:
    """Ensure directory at `path` exists. Does NOT create parent directories.

    Arguments:
        path {Path} -- Path to the directory to create.

    Raises:
        FileNotFoundError -- If the directory does not exist and its parents do not exist.
    """
    path.mkdir(parents=False, exist_ok=True)


def _resolve_path(directory: str) -> Path:
    """Return directory as absolute Path.

    Arguments:
        directory {str} -- Path to directory, possibly relative.

    Returns:
        Path -- Absolute Path.
    """
    path = Path(directory)
    return path.resolve()


def write_build_result(directory: str, result: BuildResult) -> None:
    """Write builder result to a directory.

    Arguments:
        directory {str} -- Directory where to write results, possibly relative.
        result {BuildResult} -- Builder result.
    """
    output_dir_path = _resolve_path(directory)
    LOGGER.info("Writing to folder %s.", str(output_dir_path))

    _ensure_dir_exists(output_dir_path)

    openapi_output = output_dir_path / OPENAPI_FILENAME

    openapi_object = result["openapi"]

    schema_json = cast(str, json.dumps(convert_from_openapi(openapi_object), indent=2))

    with openapi_output.open("wb") as f:
        LOGGER.debug("Writing to: %s\n", str(openapi_output))
        f.write(schema_json.encode(encoding="utf-8"))
