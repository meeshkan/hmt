import typing
from abc import ABC, abstractmethod
from typing import Any

from faker import Faker
from http_types import Request
from openapi_typed_2 import OpenAPIObject, Operation

from meeshkan.serve.mock.storage.entity import Entity
from meeshkan.serve.mock.storage.mock_data import MockData


class FakerBase(ABC):
    _entity: typing.Optional[Entity]
    _text_faker: Faker
    _request: Request
    _spec: OpenAPIObject
    _storage: MockData
    _path_item: str

    def __init__(
        self,
        text_faker: Faker,
        request: Request,
        spec: OpenAPIObject,
        storage: MockData,
    ):
        self._fkr = text_faker
        self._request = request
        self._spec = spec
        self._storage = storage
        self._entity = None

    @abstractmethod
    def execute(self) -> Any:
        pass

    def _update_data(self, method: Operation):
        pass
