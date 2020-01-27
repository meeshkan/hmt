"""Code for working with OpenAPI paths, combining and transforming them."""
import re


TYPE_TO_REGEX = {
    'string': re.compile(r"""\w+"""),
    'number': re.compile(r"""\d+"""),
}


def path_to_regex(path: str, **kwargs):
    """Convert an OpenAPI path such as "/pets/{id}" to a regular expression.

    Arguments:
        path {str} -- [description]
        kwargs: Keyword arguments listing the type of each parameter: For example: { 'id': { 'type': 'string' } }
    """

    # Extract parameters
    param_name = 'id'

    param_pattern = r"""\\{([\w-]+)\\}"""

    return_string = re.escape(path)

    for match in re.finditer(param_pattern, return_string):
        full_match = match.group(0)
        param_name = match.group(1)
        if not param_name in kwargs:
            raise Exception(
                "No match for parameter %s in kwargs".format(param_name))
        param_type = kwargs[param_name]['type']
        type_regex = TYPE_TO_REGEX[param_type]

        return_string = return_string.replace(full_match, type_regex.pattern)

    return re.compile(r'^' + return_string + r'$')
