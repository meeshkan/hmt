from faker import Faker
from http_types import Request
from openapi_typed_2 import OpenAPIObject, Any, Operation

from meeshkan.build.nlp.entity_extractor import EntityExtractorNLP
from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker
from meeshkan.serve.mock.storage import Storage

entity_extractor = EntityExtractorNLP()


class MeeshkanDataFaker(MeeshkanSchemaFaker):
    def __init__(self, text_faker: Faker, request: Request, spec: OpenAPIObject, storage: Storage):
        super().__init__(text_faker, request, spec, storage)
        self._entity_extractor = entity_extractor
        self._entity_name = self._entity_extractor.get_entity_from_url(request.pathname)


    def fake_ref(self, schema: Any, depth: int, count = 1):
        name = schema["$ref"].split("/")[2]
        if name in self._storage:
            if count == 1:
                if name == self._entity_name and self._generated_data is not None:
                    return self._generated_data
                else:
                    return self._storage.query_one(name, self._request)
            else:
                return self._storage.query(name, self._request)
        else:
            return self.fake_it(self._top_schema["definitions"][name], depth)

    def _update_data(self, method: Operation):
        if method._x is None or 'x-meeshkan-operation' not in method._x:
            return None

        if method._x['x-meeshkan-operation'] == 'read':
            return None

        entity = self._entity_extractor.get_entity_from_url(self._request.pathname)
        if entity is None:
            return None

        if method._x['x-meeshkan-operation'] == 'insert':
            return self._storage.insert_from_request(entity, self._request)

        elif method._x['x-meeshkan-operation'] == 'upsert':
            return self._storage.upsert_from_request(entity, self._request)





