from typing import Sequence

import requests_mock

from hmt.serve.mock.specs import OpenAPISpecification, load_specs

spec_directory = "tests/serve/mock/schemas/petstore"
spec_file_path = f"{spec_directory}/index.yaml"


def assert_on_petstore_spec(
    specs: Sequence[OpenAPISpecification], expected_source: str
):
    assert len(specs) == 1
    spec = specs[0]
    assert expected_source == spec.source.replace("\\", "/")  # for windows
    assert "Swagger Petstore" == spec.api.info.title


def test_load_specs_from_dir():
    loaded_specs = load_specs((spec_directory,))
    assert_on_petstore_spec(loaded_specs, spec_file_path)


def test_load_specs_from_file():
    loaded_specs = load_specs((spec_file_path,))
    assert_on_petstore_spec(loaded_specs, spec_file_path)


def test_load_specs_from_http():
    with open(spec_file_path, encoding="utf8") as f:
        spec_text = f.read()

    for protocol in ["http", "https"]:
        spec_url = f"{protocol}://api.example.com/index.yaml"
        with requests_mock.Mocker() as m:
            m.get(spec_url, text=spec_text)
            loaded_specs = load_specs(spec_url)
            assert_on_petstore_spec(loaded_specs, spec_url)
