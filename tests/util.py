import json
from typing import Any, Dict, List
from http_types import RequestResponsePair, RequestResponseBuilder


def read_requests(requests_path="resources/recordings.jsonl") -> List[str]:
    with open(requests_path) as f:
        return [line for line in f]


def request_samples_dict() -> List[Dict[Any, Any]]:
    requests = read_requests()
    return [json.loads(line) for line in requests]


def request_samples() -> List[RequestResponsePair]:
    requests = request_samples_dict()
    return [RequestResponseBuilder.from_dict(reqres) for reqres in requests]
