"""Code for working with OpenAPI paths, combining and transforming them."""
import re
from typing import Pattern, Optional, Tuple, Mapping, Any, Sequence

from openapi_typed import PathItem, Paths

# Al regex replacements must be capturing groups
TYPE_TO_REGEX = {
    'string': r"""(\w+)""",
    'number': r"""(\d+)""",
}

# Pattern to match to in the escaped path string
# Search for occurrences such as "{id}" or "{key-name}"
PATH_PARAMETER_PATTERN = r"""\\{([\w-]+)\\}"""


def match_to_path(request_path: str, path: str) -> Optional[Mapping[str, Any]]:
    """Match a request path to path

    Arguments:
        request_path {str} -- Request path such as /pets/32
        path {str} -- Path name in OpenAPI format such as /pets/{id}

    Returns:
        Optional[Mapping[str, Any]] -- None if no match, dictionary of parameter name to value otherwise.
    """
    path_as_regex, parameter_names = path_to_regex(path)
    match = path_as_regex.match(request_path)

    if match is None:
        return None

    captures = match.groups()

    assert len(parameter_names) == len(captures)

    return {key: value for key, value in zip(parameter_names, captures)}


def find_matching_path(request_path: str, paths: Paths) -> Optional[Tuple[PathItem, Mapping[str, Any]]]:
    """Find path that matches the request.

    Arguments:
        request_path {str} -- Request path.
        paths {Paths} -- OpenAPI Paths object.

    Returns:
        Optional[Tuple[PathItem, Mapping[str, Any]]] -- PathItem and key-value pairs of found path parameters with names
    """

    for path, path_item in paths.items():
        path_match = match_to_path(request_path, path)

        if path_match is None:
            continue

        return (path_item, path_match)

    return None


def path_to_regex(path: str, **kwargs) -> Tuple[Pattern[str], Tuple[str]]:
    """Convert an OpenAPI path such as "/pets/{id}" to a regular expression.

    Arguments:
        path {str} -- [description]
        kwargs: Keyword arguments listing the type of each parameter: For example: { 'id': { 'type': 'string' } }

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
        if not param_name in kwargs:
            raise Exception(
                "No match for parameter %s in kwargs".format(param_name))

        param_type = kwargs[param_name]['type']

        if not param_type in TYPE_TO_REGEX:
            raise Exception(
                "Unknown type %s, cannot convert to regex".format(param_type))

        type_regex = TYPE_TO_REGEX[param_type]

        param_names = param_names + (param_name, )

        escaped_path = escaped_path.replace(full_match, type_regex)

    return (re.compile(r'^' + escaped_path + r'$'), param_names)
