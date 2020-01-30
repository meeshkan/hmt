import json
from typing import Any, Dict, List, cast
from http_types import HttpExchange, HttpExchangeBuilder
from openapi_typed import OpenAPIObject
from yaml import safe_load
from meeshkan.schemabuilder.schema import validate_openapi_object

SAMPLE_RECORDINGS_PATH = "resources/recordings.jsonl"
PETSTORE_YAML_PATH = "resources/petstore.yaml"


def read_recordings_as_strings(requests_path=SAMPLE_RECORDINGS_PATH) -> List[str]:
    with open(requests_path) as f:
        return [line for line in f]


def read_recordings_as_dict(requests_path=SAMPLE_RECORDINGS_PATH) -> List[Dict[Any, Any]]:
    return [json.loads(line) for line in read_recordings_as_strings(requests_path)]


def read_recordings_as_request_response(requests_path=SAMPLE_RECORDINGS_PATH) -> List[HttpExchange]:
    return [HttpExchangeBuilder.from_dict(reqres) for reqres in read_recordings_as_dict(requests_path)]


def petstore_schema() -> OpenAPIObject:
    with open(PETSTORE_YAML_PATH, "r") as f:
        oas = cast(Any, safe_load(f.read()))

    validate_openapi_object(oas)

    return oas
