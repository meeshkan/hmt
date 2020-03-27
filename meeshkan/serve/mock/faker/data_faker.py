from faker import Faker
from http_types import Request
from meeshkan.serve.mock.storage.mock_data import MockData
from openapi_typed_2 import OpenAPIObject, Any, Operation

from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker



class MeeshkanDataFaker(MeeshkanSchemaFaker):
    def __init__(self, text_faker: Faker, request: Request, spec: OpenAPIObject, storage: MockData):
        super().__init__(text_faker, request, spec, storage)

    def fake_ref(self, schema: Any, depth: int):
        name = schema["$ref"].split("/")[2]
        if name in self._storage:
            if name == self._entity_name and self._generated_data is not None:
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
            return [self.fake_it(self._top_schema["definitions"][name], depth) for _ in range(count)]

    def _update_data(self, method: Operation):
        if method._x is None or 'x-meeshkan-operation' not in method._x:
            return None

        if method._x['x-meeshkan-operation'] == 'read':
            return None

        if self._entity_name is None:
            return None

        if method._x['x-meeshkan-operation'] == 'insert':
            return self._storage.insert_from_request(self._entity_name, self._request)

        elif method._x['x-meeshkan-operation'] == 'upsert':
            return self._storage.upsert_from_request(self._entity_name, self._request)





