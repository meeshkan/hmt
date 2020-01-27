from meeshkan.schemabuilder.paths import path_to_regex


def test_path_to_regex():
    as_regex = path_to_regex('/pets/{id}', id={'type': 'number'})

    assert as_regex.pattern == '^\\/pets\\/\\d+$'
    assert as_regex.match("/pets/32")
    assert not as_regex.match("/pets/32/")
    assert not as_regex.match("/pets/foo")
