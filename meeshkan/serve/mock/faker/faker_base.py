from abc import ABC, abstractmethod
from typing import Any

from faker import Faker
from http_types import Request
from openapi_typed_2 import OpenAPIObject, Operation

from meeshkan.serve.mock.storage.entity import Entity
from meeshkan.serve.mock.storage.mock_data import MockData


class FakerBase(ABC):
    _text_faker: Faker

    def __init__(self):
        self._text_faker = Faker()

    @abstractmethod
    def process(self, spec: OpenAPIObject, storage: MockData, request: Request) -> Any:
        pass

    def _update_data(
        self, path_item: str, method: Operation, request: Request, entity: Entity
    ):
        pass
