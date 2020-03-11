from meeshkan.build.paths import path_to_regex, find_matching_path
from hamcrest import *
from openapi_typed_2 import convert_to_Operation, convert_to_openapi
import pytest
from yaml import safe_load

@pytest.fixture
def schema():
    with open("/tests/build/schemas/petstore/index.yaml", "r") as f:
        oas = convert_to_openapi(safe_load(f.read()))
        return oas


def test_path_to_regex():
    as_regex, parameters = path_to_regex('/pets/{id}')

    # assert_that(as_regex.pattern, is_('^\\/pets\\/(\\w+)$'))
    # assert_that(as_regex.pattern, is_(r"""^\/pets\/(\w+)$"""))

    assert_that("/pets/32", matches_regexp(as_regex))
    assert_that("/pets/32?id=3", matches_regexp(as_regex))
    assert_that("/pets/32#reference", matches_regexp(as_regex))

    assert_that("/pets/32/", not_(matches_regexp(as_regex)))

    assert parameters == ('id', )


def test_path_to_regex_with_multiple_params():
    as_regex, _ = path_to_regex(
        '/pets/{id}/items/{name}')

    assert_that("/pets/32/items/car", matches_regexp(as_regex))


def test_match_paths(schema):
    paths = schema.paths
    request_path = "/pets/32"

    match_result = find_matching_path(request_path, paths, "get", convert_to_Operation({
        'responses': {}
    }))

    assert match_result is not None

    expected_path_item = schema.paths['/pets/{petId}']
    path_item, parameters = match_result.path, match_result.param_mapping

    assert_that(path_item, equal_to(expected_path_item))
    assert_that(parameters, has_entry('petId', '32'))
