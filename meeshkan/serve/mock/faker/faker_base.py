from abc import ABC, abstractmethod
from typing import Any

from faker import Faker
from http_types import Request
from meeshkan.serve.mock.storage.mock_data import MockData
from openapi_typed import OpenAPIObject
from openapi_typed_2 import Operation



class MeeshkanFakerBase(ABC):
    def __init__(self, text_faker: Faker, request: Request, spec: OpenAPIObject, storage: MockData):
        self._fkr = text_faker
        self._request = request
        self._spec = spec
        self._storage = storage

    @abstractmethod
    def execute(self) -> Any:
        pass

    def _update_data(self, method: Operation):
        pass
