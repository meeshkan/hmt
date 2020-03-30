from faker import Faker
from http_types import Request
from meeshkan.serve.mock.faker.stateless_faker import StatelessFaker
from meeshkan.serve.mock.storage.mock_data import MockData
from meeshkan.serve.utils.opanapi_utils import get_x
from openapi_typed_2 import Any, OpenAPIObject, Operation


class StatefulFaker(StatelessFaker):
    def __init__(
            self,
            text_faker: Faker,
            request: Request,
            spec: OpenAPIObject,
            storage: MockData,
    ):
        super().__init__(text_faker, request, spec, storage)

    def fake_ref(self, schema: Any, depth: int):
        if self._entity is None:
            return super().fake_ref(schema, depth)
        else:
            name = schema["$ref"].split("/")[2]

            if name in self._storage:
                if name == self._entity.name and self._generated_data is not None:
                    return self._generated_data
                else:
                    return self._storage.query_one(name, self._request)
            else:
                return self.fake_it(self._top_schema["definitions"][name], depth)

    def fake_ref_array(self, schema: Any, depth: int, count: int):
        name = schema["$ref"].split("/")[2]
        if name in self._storage:
            return self._storage.query(name, self._request)
        else:
            return [
                self.fake_it(self._top_schema["definitions"][name], depth)
                for _ in range(count)
            ]

    def _update_data(self, method: Operation):
        if self._entity is None:
            return super()._update_data(method)

        operation_type = get_x(method, "x-meeshkan-operation")
        if operation_type == "insert":
            return self._entity.insert_from_request(self._path_item, self._request)
        elif operation_type == "upsert":
            return self._entity.upsert_from_request(self._path_item, self._request)
