from http_types import Request
from openapi_typed_2 import Any, Operation

from meeshkan.serve.mock.faker.stateless_faker import FakerData, StatelessFaker
from meeshkan.serve.mock.storage.entity import Entity
from meeshkan.serve.utils.opanapi_utils import get_x


class StatefulFaker(StatelessFaker):
    def fake_ref(self, faker_data: FakerData, schema: Any, depth: int):
        name = schema["$ref"].split("/")[2]
        if faker_data.entity is not None and name == faker_data.entity.name:
            if faker_data.updated_data is not None:
                return faker_data.updated_data
            else:
                return faker_data.entity.query_one(
                    faker_data.path_item, faker_data.request
                )
        else:
            return self.fake_it(
                faker_data, faker_data.schema["definitions"][name], depth
            )

    def fake_ref_array(
        self, faker_data: FakerData, schema: Any, depth: int, count: int
    ):
        name = schema["$ref"].split("/")[2]
        if faker_data.entity is not None and name == faker_data.entity.name:
            return faker_data.entity.query(faker_data.path_item, faker_data.request)
        else:
            return [
                self.fake_it(faker_data, faker_data.schema["definitions"][name], depth)
                for _ in range(count)
            ]

    def _update_data(
        self, path_item: str, method: Operation, request: Request, entity: Entity
    ):
        operation_type = get_x(method, "x-meeshkan-operation")
        if operation_type == "insert":
            return entity.insert_from_request(path_item, request)
        elif operation_type == "upsert":
            return entity.upsert_from_request(path_item, request)
