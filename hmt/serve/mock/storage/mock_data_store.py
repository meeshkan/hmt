import copy
import logging
import typing

from hmt.serve.mock.specs import OpenAPISpecification
from hmt.serve.mock.storage.entity import Entity
from hmt.serve.mock.storage.mock_data import MockData
from hmt.serve.utils.opanapi_ext import get_x

logger = logging.getLogger(__name__)


class MockDataStore:
    """
    The MockDataStore object contains instances of the MockData class for each configured mock.
    """

    def __init__(self):
        self._storages: typing.Dict[str, MockData] = dict()
        self._default = dict()
        self._specs = dict()

    def add_mock(self, spec: OpenAPISpecification):
        """
        Adds a mock. The method automatically creates entities defined in an OpenAPI spec and populates them with
        data if it is defined in the spec.
        :param mockname: a name of a mock
        :param spec: an OpenAPI spec
        """
        self._specs[spec.source] = spec

        storage = MockData()
        self._storages[spec.source] = storage
        if spec.api.components is not None and spec.api.components.schemas is not None:
            for name, schema in spec.api.components.schemas.items():
                if get_x(schema, "x-hmt-id-path") is not None:
                    storage.add_entity(Entity(name, spec.api))

        for entity, values in get_x(spec.api, "x-hmt-data", dict()).items():
            for val in values:
                storage.get_entity(entity).insert(copy.deepcopy(val))

    def __getitem__(self, mockname):
        return self._storages[mockname]

    def clear(self):
        for storage in self._storages.values():
            storage.clear()
        self._default.clear()
        logger.debug("All storages cleared")

    def reset(self):
        self.clear()
        for spec in self._specs.values():
            storage = self._storages[spec.source]
            for entity, values in get_x(spec.api, "x-hmt-data", dict()).items():
                entity = storage.get_entity(entity)
                for val in values:
                    entity.insert(copy.deepcopy(val))

    @property
    def default(self):
        return self._default
