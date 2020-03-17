import json
from typing import Any, Dict, List

from http_types import HttpExchange, HttpExchangeBuilder

SAMPLE_RECORDINGS_PATH = "resources/github.jsonl"
POKEAPI_RECORDINGS_PATH = "resources/pokeapi.jsonl"
PETSTORE_YAML_PATH = "resources/petstore.yaml"


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
