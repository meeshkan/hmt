import logging
import uuid

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
        self._entities[name] = dict()

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
        return list(self._entities[entity].values())

    def query_one(self, entity, request: Request):
        id_field = self.id_field(entity)
        if id_field in request.bodyAsJson:
            return self._entities[entity].get(request.bodyAsJson[id_field], {})

    def insert_from_request(self, entity, request):
        id_field = self.id_field(entity)
        id_value = request.bodyAsJson.get(id_field, str(uuid.uuid1()))
        entity_val = request.bodyAsJson
        entity_val[id_field] = id_value
        self._entities[entity][id_value] = entity_val
        return entity_val

    def insert(self, name, entity):
        id_field = self.id_field(name)
        self._entities[name][entity[id_field]] = entity

    def upsert_from_request(self, entity, request: Request):
        id_field = self.id_field(entity)
        entities = self._entities[entity]
        req_body = request.bodyAsJson
        if not id_field in req_body or not req_body[id_field] in entities:
            return self.insert_from_request(entity, request)

        return self._merge(entities[req_body[id_field]], req_body)


    def _merge(self, entity1, entity2):
        for k, v in entity2.items():
            entity1[k] = v
        return entity1

    def id_field(self, entity):
        return '{}Id'.format(entity)


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
                for val in values:
                    storage.insert(entity, val)

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
