from typing import Any

from faker import Faker
from http_types import Request
from openapi_typed import OpenAPIObject
from openapi_typed_2 import Operation

from meeshkan.serve.mock.storage import Storage


class MeeshkanFakerBase:
    def __init__(self, text_faker: Faker, request: Request, spec: OpenAPIObject, storage: Storage):
        self._fkr = text_faker
        self._request = request
        self._spec = spec
        self._storage = storage

    def execute(self) -> Any:
        raise NotImplementedError

    def _update_data(self, method: Operation):
        pass
