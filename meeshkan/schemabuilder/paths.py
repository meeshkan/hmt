"""Code for working with OpenAPI paths, e.g., matching request path to an OpenAPI endpoint with parameter."""
import re
from typing import Pattern, Optional, Tuple, Mapping, Any, Sequence

from openapi_typed import PathItem, Paths

# Pattern to match to in the escaped path string
# Search for occurrences such as "{id}" or "{key-name}"
PATH_PARAMETER_PATTERN = r"""\\{([\w-]+)\\}"""

RequestPathParameters = Mapping[str, str]


def _match_to_path(request_path: str, path: str) -> Optional[Mapping[str, Any]]:
    """Match a request path such as "/pets/32" to a variable path such as "/pets/{petId}".

    Arguments:
        request_path {str} -- Request path such as /pets/32
        path {str} -- Path name in OpenAPI format such as /pets/{id}

    Returns:
        Optional[Mapping[str, Any]] -- None if the paths do not match. Otherwise, return a dictionary of parameter names to values (for example: { 'petId': '32' })
    """
    path_as_regex, parameter_names = path_to_regex(path)
    match = path_as_regex.match(request_path)

    if match is None:
        return None

    captures = match.groups()

    assert len(parameter_names) == len(
        captures), "Expected the number of parameter names in the path to match the number of captured parameter values"

    return {parameter_name: parameter_value for parameter_name, parameter_value in zip(parameter_names, captures)}


def find_matching_path(request_path: str, paths: Paths) -> Optional[Tuple[PathItem, RequestPathParameters]]:
    """Find path that matches the request path.

    Arguments:
        request_path {str} -- Request path.
        paths {Paths} -- OpenAPI Paths object.

    Returns:
        Optional[Tuple[PathItem, Mapping[str, Any]]] -- PathItem and key-value pairs of found path parameters with names
    """

    for path, path_item in paths.items():
        path_match = _match_to_path(request_path=request_path, path=path)

        if path_match is None:
            continue

        return (path_item, path_match)

    return None


PATH_PARAMETER_REGEX = r"""(\w+)"""


def path_to_regex(path: str) -> Tuple[Pattern[str], Tuple[str]]:
    """Convert an OpenAPI path such as "/pets/{id}" to a regular expression. The returned regular expression
    contains capturing groups for path parameters. Parameter names are returned in the second tuple.

    Arguments:
        path {str} -- [description]

    Returns:
        {} -- Tuple containing (1) pattern for path with parameters replaced by regular expressions, and (2) list of parameters with names.
    """

    # Work on string whose regex characters are escaped ("/"" becomes "//" etc.)
    # This makes it easier to replace matches with regular expressions.
    # For example: /pets/{id} becomes \/pets\/\{id\}
    escaped_path = re.escape(path)

    param_names = ()  # type: Tuple[str]

    for match in re.finditer(PATH_PARAMETER_PATTERN, escaped_path):
        full_match = match.group(0)
        param_name = match.group(1)

        param_names = param_names + (param_name, )

        escaped_path = escaped_path.replace(full_match, PATH_PARAMETER_REGEX)

    regex_pattern = re.compile(r'^' + escaped_path + r'(?:\?|#|$)')

    return (regex_pattern, param_names)
