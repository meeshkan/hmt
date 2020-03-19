import logging

from http_types import Request
from openapi_typed import OpenAPIObject

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self):
        self._default = dict()
        self._entities = dict()

    @property
    def default(self):
        return self._default

    def add_entity(self, name):
        self._entities[name] = list()

    def clear(self):
        self._default.clear()
        for entity in self._entities.values():
            entity.clear()
        logger.debug("Storage cleared")

    def __getattr__(self, x):
        if x in self.__dict__:
            return getattr(self, x)
        return self._entities[x]

    def __getitem__(self, x):
        return self._entities[x]

    def __contains__(self, x):
        return x in self._entities

    def query(self, entity, request: Request):
        return self._entities[entity]

    def query_one(self, entity, request: Request):
        return self._entities[entity][0] if len(self._entities[entity]) > 0 else {}

    def insert_from_request(self, entity, request):
        self._entities[entity].append(request)

    def upsert_from_request(self, entity, request):
        id_field = '{}Id'.format(entity)
        for entity in self._entities:
            if entity[id_field] == request[id_field]:
                self._merge(entity[id_field], request[id_field])
                return

        self.insert_from_request(entity, request)

    def _merge(self, entity1, entity2):
        for k, v in entity2:
            entity1[k] = v


class StorageManager:
    def __init__(self):
        self._storages = dict()
        self._default = Storage()

    def add_mock(self, mockname: str, spec: OpenAPIObject):
        storage = Storage()
        self._storages[mockname] = storage
        if spec._x is not None and 'x-meeshkan-data' in spec._x:
            for entity, values in spec._x['x-meeshkan-data'].items():
                storage.add_entity(entity)
                storage[entity].extend(values)

    def __getitem__(self, mockname):
        return self._storages[mockname]

    @property
    def default(self):
        return self._default

    def clear(self):
        self._default.clear()
        for storage in self._storages.values():
            storage.clear()
        logger.debug("Storages cleared")


storage_manager = StorageManager()
