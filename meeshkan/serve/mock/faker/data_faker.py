from faker import Faker
from http_types import Request
from openapi_typed_2 import OpenAPIObject, Any, Operation

from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker
from meeshkan.serve.mock.storage import Storage


class MeeshkanDataFaker(MeeshkanSchemaFaker):
    def __init__(self, text_faker: Faker, request: Request, spec: OpenAPIObject, storage: Storage):
        super().__init__(text_faker, request, spec, storage)

    def fake_ref(self, schema: Any, depth: int, count = 1):
        name = schema["$ref"].split("/")[2]
        if name in self._storage:
            if count == 1:
                return self._storage.query_one(name, self._request)
            else:
                return self._storage.query(name, self._request)
        else:
            return self.fake_it(self._top_schema["definitions"][name], depth)

    def _update_data(self, method: Operation):
        if 'x-meeshkan-type' not in method._x:
            return

        if method._x['x-meeshkan-type'] == 'read':
            return

        if method._x['x-meeshkan-type'] == 'insert':
            self._storage.insert_from_request()



