import typing
from dataclasses import dataclass

from http_types import Request
from openapi_typed_2 import Any, Operation

from hmt.serve.mock.faker.stateless_faker import FakerData, StatelessFaker
from hmt.serve.mock.storage.entity import Entity
from hmt.serve.utils.opanapi_ext import ApiOperation, get_x


@dataclass(frozen=True)
class StatefulFakerData(FakerData):
    """
    Common data passed through recursion steps in the StatefulFaker object.
    """

    entity: typing.Optional[Entity]
    """
    An entity related to a faked endpoint
    """
    updated_data: typing.Optional[typing.Any]
    """
    It is preserved for requests that do updates and returns updated data
    """


class StatefulFaker(StatelessFaker):
    """
    A stateful implementation of the BaseFaker interface. It requires an extended spec with x-hmt fields defined
    to automatically implement stateful logic. For specs without hmt extensions
    it works the same way as the StatelessFaker.
    """

    def __init__(self, mock_data_store):
        super().__init__()
        self._mock_data_store = mock_data_store

    def _fake_json(
        self, status_code: int, headers: typing.Mapping[str, str], faker_data: FakerData
    ):
        entity_name = get_x(
            faker_data.spec.api.paths[faker_data.path_item], "x-hmt-entity"
        )
        entity: typing.Optional[Entity] = (
            self._mock_data_store[faker_data.spec.source].get_entity(entity_name)
            if entity_name is not None
            else None
        )

        updated_data = self._update_data(
            faker_data.path_item, faker_data.method, faker_data.request, entity,
        )

        faker_data = StatefulFakerData(
            spec=faker_data.spec,
            path_item=faker_data.path_item,
            method=faker_data.method,
            schema=faker_data.schema,
            request=faker_data.request,
            updated_data=updated_data,
            entity=entity,
        )

        return super()._fake_json(status_code, headers, faker_data)

    def _fake_ref(self, faker_data: StatefulFakerData, schema: Any, depth: int):
        name = schema["$ref"].split("/")[2]
        if self._matches_entity(faker_data.entity, name):
            if faker_data.updated_data is not None:
                return faker_data.updated_data
            else:
                return faker_data.entity.query_one(
                    faker_data.path_item, faker_data.request
                )
        else:
            return self._fake_it(
                faker_data, faker_data.schema["definitions"][name], depth
            )

    def _fake_ref_array(
        self, faker_data: StatefulFakerData, schema: Any, depth: int, count: int
    ):
        name = schema["$ref"].split("/")[2]
        if self._matches_entity(faker_data.entity, name):
            return faker_data.entity.query(faker_data.path_item, faker_data.request)
        else:
            return [
                self._fake_it(faker_data, faker_data.schema["definitions"][name], depth)
                for _ in range(count)
            ]

    def _update_data(
        self,
        path_item: str,
        method: Operation,
        request: Request,
        entity: typing.Optional[Entity],
    ) -> typing.Any:
        operation_type = ApiOperation(get_x(method, "x-hmt-operation", "unknown"))
        if operation_type == ApiOperation.INSERT:
            return entity.insert_from_request(path_item, request)
        elif operation_type == ApiOperation.UPSERT:
            return entity.upsert_from_request(path_item, request)

    def _matches_entity(self, entity, ref_name):
        return entity is not None and ref_name == entity.name
