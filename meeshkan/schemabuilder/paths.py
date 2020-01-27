"""Code for working with OpenAPI paths, combining and transforming them."""
import re
from typing import Pattern


TYPE_TO_REGEX = {
    'string': r"""\w+""",
    'number': r"""\d+""",
}


def path_to_regex(path: str, **kwargs) -> Pattern[str]:
    """Convert an OpenAPI path such as "/pets/{id}" to a regular expression.

    Arguments:
        path {str} -- [description]
        kwargs: Keyword arguments listing the type of each parameter: For example: { 'id': { 'type': 'string' } }

    Returns:
        {str} -- Pattern for path with parameters replaced by regular expressions.
    """

    # Extract parameters
    param_name = 'id'

    # Work on string whose regex characters are escaped ("/"" becomes "//" etc.)
    # For example: /pets/{id} becomes \/pets\/\{id\}
    escaped_path = re.escape(path)

    # Pattern to match to in the escaped path string
    # Search for occurrences such as "{id}" or "{key-name}"
    param_pattern = r"""\\{([\w-]+)\\}"""

    for match in re.finditer(param_pattern, escaped_path):
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

        escaped_path = escaped_path.replace(full_match, type_regex)

    return re.compile(r'^' + escaped_path + r'$')
