from meeshkan.schemabuilder.paths import path_to_regex
from hamcrest import assert_that, matches_regexp, not_, is_


def test_path_to_regex():
    as_regex = path_to_regex('/pets/{id}', id={'type': 'number'})

    assert_that(as_regex.pattern, is_('^\\/pets\\/\\d+$'))
    assert_that(as_regex.pattern, is_(r"""^\/pets\/\d+$"""))

    assert_that("/pets/32", matches_regexp(as_regex))
    assert_that("/pets/32/", not_(matches_regexp(as_regex)))
    assert_that("/pets/foo", not_(matches_regexp(as_regex)))


def test_path_to_regex_with_multiple_params():
    as_regex = path_to_regex(
        '/pets/{id}/items/{name}', id={'type': 'number'}, name={'type': 'string'})

    assert_that("/pets/32/items/car", as_regex)
    assert_that("/pets/32/items/car", matches_regexp(as_regex))
