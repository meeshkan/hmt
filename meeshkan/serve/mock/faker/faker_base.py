from abc import ABC, abstractmethod
from typing import Any

from http_types import Request
from openapi_typed_2 import OpenAPIObject

from meeshkan.serve.mock.storage.mock_data import MockData


class FakerBase(ABC):
    @abstractmethod
    def process(self, spec: OpenAPIObject, storage: MockData, request: Request) -> Any:
        pass
