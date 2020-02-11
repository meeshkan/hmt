"""Code for working with OpenAPI paths, e.g., matching request path to an OpenAPI endpoint with parameter."""
import re
import random
import string
from deepdiff import DeepDiff
from typing import cast, Pattern, Optional, Tuple, Mapping, Any
from typing_extensions import TypedDict

from openapi_typed import PathItem, Paths, Operation

# Pattern to match to in the escaped path string
# Search for occurrences such as "{id}" or "{key-name}"
PATH_PARAMETER_PATTERN = r"""\\{([\w-]+)\\}"""

RequestPathParameters = Mapping[str, str]


def _dumb_match_to_path(request_path: str, paths: Paths, request_method: str, operation_candidate: Operation) -> Tuple[str, Optional[str], Optional[Mapping[str, Any]]]:
    """An overly-simplistic, highly-experimental, probably-broken
       function that answers the question "does this path exist in the spec already?"
       For example, if there is /v1/clients/jane and we get
       /v1/clients/john, it should be smart enough to realize that the path is actually
       /v1/clients/{identifier}.

       We do this by using the `deepdiff` library and returning a match
       if there is enough "stuff" that doesn't diverge between two paths that
       could theoretically be the same when doing pattern matching.

       In the future, "machine learning" can take care of this... yeah...
       machine learning... the future... ooohhh....
    """

    def could_these_two_paths_possibly_represent_the_same_underlying_path(a: str, b: str) -> bool:
        """Asks the question "Could these two paths theoretically be the same?
        Uses some brutish heuristics to answer it.

        Arguments:
            a {str} -- A path
            b {str} -- A path
        
        Returns:
            bool -- Could they possibly be the same underlying path?
        """
        if a is b:
            return True
        a_spl = [x for x in a.split("/") if x != '']
        b_spl = [x for x in b.split("/") if x != '']
        # if the two lengths aren't equal, return false
        if len(a_spl) != len(b_spl):
            return False
        # if the first part of the path is not equal, return false
        # APIs almost never have a top-level wildcard
        if a_spl[0] != b_spl[0]:
            return False
        # if there are two successive non-matches, return false
        for x in range(len(a_spl) - 1):
            if a_spl[x] != b_spl[x]:
                if a_spl[x + 1] != b_spl[x + 1]:
                    return False
        # our naive test has passed, they could be theoretically similar...
        return True

    def combine_paths_into_single_path(path0: str, path1: str) -> str:
        """Combine two paths into a single path, adding wildcards when needed.

        Arguments:
            path0 {str} -- One path to combine
            path1 {str} -- Two paths to combine
        
        Returns:
            str -- A combined path
        """
        
        path0_split = [x for x in path0.split('/') if x != '']
        path1_split = [x for x in path1.split('/') if x != '']
        if len(path0_split) != len(path1_split):
            raise ValueError("Incorrect use of path combination function")
        return '/' + '/'.join([a if a == b else a if a[0] == '{' else b if b[0] == '{' else '{%s}' % ''.join(random.choices(string.ascii_lowercase, k=8)) for a, b in zip(path0_split, path1_split)])

    theoretically_plausible_paths = [path for path in paths.keys() if could_these_two_paths_possibly_represent_the_same_underlying_path(path, request_path)]
    for path in theoretically_plausible_paths:
        operation = cast(Operation, paths[path][request_method])
        potential_conflicts = set(operation['responses'].keys()).intersection(set(operation_candidate['responses'].keys()))
        new_path = combine_paths_into_single_path(path, request_path)
        if len(potential_conflicts) != 0:
            irreconcilably_different = False
            for potential_conflict in potential_conflicts:
                # we look to see if potential conflicts resemble each other
                # enough to call them the same thing
                # if not, we deem them as irreconcilably different and give up
                incumbent_potential_conflict = operation['responses'][potential_conflict]
                candidate_potential_conflict = operation_candidate['responses'][potential_conflict]
                diff = DeepDiff(incumbent_potential_conflict, candidate_potential_conflict)
                # we don't care about value differences
                # if there are too many differences based on my totally aribtrary standard,
                # we deem the two to be irreconcilably different
                if 'values_changed' in diff.keys():
                    del diff['values_changed']
                # If there are more than five things that are different between the specs,
                # we deem them as irreconcilably different.
                # This is based on the Helsinki Standard of Irreconcilable Differences Between JSON Objects,
                # ISO-2912432, which has been passed down as an oral traditoin since the dawn of time.
                if sum([len(x) for x in diff.values()], 0) > 5:
                    irreconcilably_different = True
                    break
            if irreconcilably_different:
                continue
        # if it has gotten this far, all potential
        # conflicts can be resolved, so we merge
        matches = _match_to_path(request_path, new_path)
        if matches is None:
            raise ValueError('Algorithm conflict for path matching - got a match for %s %s, but then returned match === None' % (request_path, new_path))
        # TODO: what if there is more than 1 theoretically plausible path?
        # in practice unlikely but possible if, for example, the spec has two conflicting
        # paths already in it
        return (new_path, path, matches)
    return (request_path, None, None)

def _match_to_path(request_path: str, path: str) -> Optional[Mapping[str, Any]]:
    """Match a request path such as "/pets/32" to a variable path such as "/pets/{petId}".

    Arguments:
        request_path {str} -- Request path such as /pets/32
        path {str} -- Path name in OpenAPI format such as /pets/{id}

    Returns:
        Optional[Mapping[str, Any]] -- None if the paths do not match. Otherwise, return a dictionary of parameter names to values (for example: { 'petId': '32' })
    """
    # this function won't work if
    # requests paths have a trailing slash, so we remove it
    if request_path[-1] == '/':
        request_path = request_path[:-1]
    path_as_regex, parameter_names = path_to_regex(path)
    match = path_as_regex.match(request_path)

    if match is None:
        return None

    captures = match.groups()

    assert len(parameter_names) == len(
        captures), "Expected the number of parameter names in the path to match the number of captured parameter values"

    return {parameter_name: parameter_value for parameter_name, parameter_value in zip(parameter_names, captures)}


class MatchingPath(TypedDict):
  path: PathItem
  param_mapping: Mapping[str, Any]
  new_pathname: str
  subsumable_pathname: Optional[str]

def find_matching_path(request_path: str, paths: Paths, request_method: str, operation_candidate: Operation) -> Optional[MatchingPath]:
    """Find path that matches the request path.

    Arguments:
        request_path {str} -- Request path.
        paths {Paths} -- OpenAPI Paths object.
        request_method {str} -- The method (ie get, post, etc)
        operation_candidate {Operation} -- An operation to match against other paths.

    Returns:
        Optional[MatchingPath] -- The matching path (if any)
    """

    # First pass - we find an explicit match
    # Second pass - we construct a match if it looks like
    # two paths are in fact similar.
    for fn in [
        lambda p, pi: (request_path, None, _match_to_path(request_path=request_path, path=p)),
        lambda p, pi: _dumb_match_to_path(request_path, paths, request_method, operation_candidate)]:
        for path, path_item in paths.items():
            new_pathname, subsumable_pathname, path_match = fn(path, path_item)

            if path_match is None:
                continue
            return {'path': path_item, 'param_mapping': path_match, 'new_pathname': new_pathname, 'subsumable_pathname': subsumable_pathname }

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
