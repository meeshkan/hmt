from meeshkan.schemabuilder.paths import path_to_regex


def test_path_to_regex():
    as_regex = path_to_regex('/pets/{id}', id={'type': 'number'})

    assert as_regex.pattern == '^\\/pets\\/\\d+$'
    assert as_regex.pattern == r"""^\/pets\/\d+$"""
    assert as_regex.match("/pets/32"), "Expected /pets/32 to match"
    assert not as_regex.match("/pets/32/"), "Did not expect /pets/32/ to match"
    assert not as_regex.match("/pets/foo"), "Did not expect /pets/foo to match"
