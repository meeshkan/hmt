import json
import logging
import os
from dataclasses import dataclass
from typing import Sequence

import yaml
from openapi_typed_2 import OpenAPIObject, convert_to_openapi


@dataclass
class OpenAPISpecification:
    """An OpenAPI object with information about the source it was created from (such as the file name or URL)."""

    api: OpenAPIObject
    source: str


def load_specs(specs_dir: str) -> Sequence[OpenAPISpecification]:
    if not os.path.exists(specs_dir):
        logging.info("OpenAPI schema directory not found %s", specs_dir)
        return []
    specs_with_sources = []
    specs_paths = [
        s
        for s in os.listdir(specs_dir)
        if s.endswith("yml") or s.endswith("yaml") or s.endswith("json")
    ]
    for spec_path in specs_paths:
        full_spec_path = os.path.join(specs_dir, spec_path)
        with open(full_spec_path, encoding="utf8") as spec_file:
            specs_with_sources.append(
                OpenAPISpecification(
                    convert_to_openapi(
                        (json.loads if spec_path.endswith("json") else yaml.safe_load)(
                            spec_file.read()
                        )
                    ),
                    spec_path,
                )
            )
    return specs_with_sources
