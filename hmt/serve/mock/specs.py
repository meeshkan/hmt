import json
import os
from dataclasses import dataclass
from typing import Any, Sequence, Union

import requests
import yaml
from openapi_typed_2 import OpenAPIObject, convert_to_openapi
from requests.exceptions import RequestException

from hmt.serve.mock.refs import make_definitions_from_spec


@dataclass
class OpenAPISpecification:
    """An OpenAPI object with information about the source it was created from (such as the file name or URL)."""

    api: OpenAPIObject
    source: str
    definitions: Any


def load_spec(spec_source: str, is_http: bool) -> OpenAPISpecification:
    spec_text: str
    if is_http:
        try:
            response = requests.get(spec_source)
            spec_text = response.text
        except RequestException:
            raise Exception(f"Failed to load {spec_source}")
    else:
        with open(spec_source, encoding="utf8") as spec_file:
            spec_text = spec_file.read()

    spec = convert_to_openapi(
        (json.loads if spec_source.endswith("json") else yaml.safe_load)(spec_text)
    )
    return OpenAPISpecification(spec, spec_source, make_definitions_from_spec(spec))


def load_specs(specs: Union[str, Sequence[str]]) -> Sequence[OpenAPISpecification]:
    if isinstance(specs, str):
        specs = (specs,)

    specs_with_sources = []

    for spec in specs:
        is_http = spec.startswith("http://") or spec.startswith("https://")

        if is_http or os.path.isfile(spec):
            specs_paths = [spec]
        elif os.path.isdir(spec):
            specs_paths = []
            for dir_path, dirs, files in os.walk(spec):
                for filename in files:
                    if (
                        filename.endswith("yml")
                        or filename.endswith("yaml")
                        or filename.endswith("json")
                    ):
                        full_path = os.path.join(dir_path, filename)
                        specs_paths.append(full_path)
        else:
            raise Exception(f"OpenAPI specification {spec} not found")

        for spec_source in specs_paths:
            loaded_spec = load_spec(spec_source, is_http)
            specs_with_sources.append(loaded_spec)

    return specs_with_sources
