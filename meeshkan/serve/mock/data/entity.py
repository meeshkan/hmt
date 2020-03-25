from http_types import Request
from jsonpath_rw import parse
from openapi_typed import PathItem


class Entity:
    def __init__(self, path: PathItem):
        self._name = path._x["x-meeshkan-entity"]
        self._id_path = path._x["x-meeshkan-id-path"]
        self._data = dict()

    def query(self, request: Request):
        return list(filter(self._filter(request), self._data.values())

    def query_one(self, request: Request):

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

    def _extact_id(self, entity):
        return self._id_path.find(entity)

    def _filter(self, request):
        return lambda x: True