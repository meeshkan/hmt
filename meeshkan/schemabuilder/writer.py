"""Code for writing builder results to file system.
"""
from openapi_typed import OpenAPIObject
from .result import BuildResult
import yaml
from ..logger import get as getLogger
from typing import cast
from pathlib import Path

LOGGER = getLogger(__name__)


OPENAPI_FILENAME = 'openapi.yaml'


def _read_openapi(file: Path) -> OpenAPIObject:
    """Read an OpenAPI YAML from file.

    Arguments:
        file {Path} -- Path to OpenAPI YAML file.

    Returns:
        OpenAPIObject -- OpenAPI object.
    """
    with file.open('rb') as f:
        return cast(OpenAPIObject, yaml.safe_load(f))


def read_directory(directory: str) -> BuildResult:
    """Read BuildResult from directory.

    Arguments:
        directory {str} -- Directory to read, possibly relative.

    Raises:
        FileNotFoundError: If directory is not an existing directory.

    Returns:
        BuildResult -- Build result.
    """
    path = _resolve_path(directory)

    if not path.is_dir():
        raise FileNotFoundError("Cannot read from {}".format(str(path)))

    openapi_path = path / OPENAPI_FILENAME
    openapi_object = _read_openapi(openapi_path)

    return BuildResult(openapi=openapi_object)


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

    openapi_object = result['openapi']

    schema_yaml = cast(str, yaml.safe_dump(openapi_object))

    with openapi_output.open('wb') as f:
        LOGGER.debug("Writing to: %s\n", str(openapi_output))
        f.write(schema_yaml.encode(encoding="utf-8"))
