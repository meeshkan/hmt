import logging

from meeshkan.serve.mock.storage.entity import Entity
from meeshkan.serve.mock.storage.mock_data import MockData
from openapi_typed import OpenAPIObject

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        self._storages = dict()

    def add_mock(self, mockname: str, spec: OpenAPIObject):
        storage = MockData()
        self._storages[mockname] = storage
        for pathname, path_item in spec.paths.items():
            if path_item._x is not None and "x-meeshkan-entity" in path_item._x:
                storage.add_entity(Entity(pathname, path_item))

        if spec._x is not None and 'x-meeshkan-data' in spec._x:
            for entity, values in spec._x['x-meeshkan-data'].items():
                for val in values:
                    storage.get_entity(entity).insert(entity, val)

    def __getitem__(self, mockname):
        return self._storages[mockname]

    def clear(self):
        for storage in self._storages.values():
            storage.clear()
        logger.debug("Storages cleared")


storage_manager = StorageManager()
