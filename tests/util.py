import json
from typing import Any, Dict, List

from http_types import HttpExchange, HttpExchangeBuilder
from meeshkan.serve.mock.log import AbstractSink
from openapi_typed_2 import convert_to_OpenAPIObject

SAMPLE_RECORDINGS_PATH = "resources/github.jsonl"
POKEAPI_RECORDINGS_PATH = "resources/pokeapi.jsonl"
PETSTORE_YAML_PATH = "resources/petstore.yaml"

class MockSink(AbstractSink):
    def __init__(self):
        self.interactions = []

    def write(self, interactions):
        self.interactions = interactions

def read_recordings_as_strings(requests_path=SAMPLE_RECORDINGS_PATH) -> List[str]:
    with open(requests_path, encoding="utf8") as f:
        return [line for line in f if line.rstrip() != ""]


def read_recordings_as_dict(
    requests_path=SAMPLE_RECORDINGS_PATH,
) -> List[Dict[Any, Any]]:
    return [json.loads(line) for line in read_recordings_as_strings(requests_path)]


def read_recordings_as_request_response(
    requests_path=SAMPLE_RECORDINGS_PATH,
) -> List[HttpExchange]:
    return [
        HttpExchangeBuilder.from_dict(reqres)
        for reqres in read_recordings_as_dict(requests_path)
    ]


def spec_dict(
    path="/", method="get", response_schema={}, request_schema=None, components=None
):
    spec = {
        "openapi": "3.0",
        "info": {"title": "Title", "version": "1.1.1"},
        "paths": {
            path: {
                method: {
                    "responses": {
                        "200": {
                            "description": "some",
                            "content": {
                                "application/json": {"schema": response_schema}
                            },
                        }
                    }
                }
            }
        },
    }
    if components is not None:
        spec["components"] = components

    if request_schema is not None:
        spec["paths"][path][method]["requestBody"] = {
            "content": {"application/json": {"schema": request_schema}}
        }
    return spec


def spec(
    path="/", method="get", response_schema={}, request_schema=None, components=None
):
    return convert_to_OpenAPIObject(
        spec_dict(path, method, response_schema, request_schema, components)
    )


def add_item(
    spec,
    path="/",
    method="get",
    response_schema={},
    request_schema=None,
    components=None,
):
    if path not in spec["paths"]:
        spec["paths"][path] = {}

    spec["paths"][path][method] = {
        "responses": {
            "200": {
                "description": "some",
                "content": {"application/json": {"schema": response_schema}},
            }
        }
    }
    if components is not None:
        spec["components"] = components

    if request_schema is not None:
        spec["paths"][path][method]["requestBody"] = {
            "content": {"application/json": {"schema": request_schema}}
        }

    return spec


