import typing
import uuid

from http_types import Request
from jsonpath_rw import parse
from meeshkan.build.paths import _match_to_path
from openapi_typed_2 import PathItem, Operation


class Entity:
    methods = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']

    def __init__(self, path: str, path_item: PathItem):
        self._path = path
        self._path_item = path_item
        self._name = path_item._x["x-meeshkan-entity"]
        self._id_path = parse(path_item._x["x-meeshkan-id-path"])
        self._data = dict()
        self._request_entity_selectors = self._build_request_entity_selectors(path_item)

    def query(self, request: Request):
        return [x for x in self._data.values() if self._filter(request)]

    def query_one(self, request: Request):
        id = self._get_id(request)
        return self._data.get(id, {}) if id is not None else {}

    def _get_id(self, request: Request):
        id = _match_to_path(self._path, request.pathname).get('id', self._id_filter(request))
        return id

    def insert_from_request(self, request: Request):
        id = self._get_id(request)
        if id is None:
            id = self._generate_id()
        entity_val = self._request_entity_selectors[request.method].find()
        entity_val = self._id_path.set(entity_val, id)
        self._data[id] = entity_val
        return entity_val

    def insert(self, name, entity):
        id = self._id_path.find(entity).value()
        self._data[id] = entity

    def upsert_from_request(self, request: Request):
        id = self._get_id(request)
        if id is None:
            return self.insert_from_request(request)
        else:
            entity_val = self._request_entity_selectors[request.method].find()
            return self._merge(self._data[id], entity_val)


    def _merge(self, entity1, entity2):
        for k, v in entity2.items():
            entity1[k] = v
        return entity1

    def _extact_id(self, entity):
        return self._id_path.find(entity)

    def _filter(self, request: Request):
        return lambda x: True

    def _id_filter(self, request: Request):
        return None

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __delitem__(self, key):
        del self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def _build_request_entity_selectors(self, path_item: PathItem) -> typing.Mapping[str, typing.Callable]:
        res: typing.Dict[str, typing.Callable] = {}
        for method_name in self.methods:
            method: Operation = getattr(path_item, method_name)
            if method is not None and method._x is not None and "x-meeshkan-operation" in method._x:
                if method._x["x-meeshkan-operation"] == "insert" or method._x["x-meeshkan-operation"] == "upsert":
                    if "application/json" in method.requestBody.content:
                        schema = method.requestBody.content["application/json"].schema
                        if schema is not None:
                            entity_path = self._find_entity(schema, "")
                            if res is not None:
                                res[method_name] = parse(entity_path)
        return res

    def _find_entity(self, schema, path):
        if "$ref" in schema:
            name = schema["$ref"].split("/")[3]
            if name == self._name:
                return path
        elif schema.get("type", None) == "array":
                if "items" not in schema:
                    return None
                elif isinstance(schema["items"], list):
                    return next((x for x in (self._find_entity(item, path+"[*]") for item in schema["items"])
                                 if x is not None))
                else:
                    return self._find_entity(schema["items"], path+"[*]")
        elif  schema.get("type", "object") == "object" and "properties" is schema:
            return next((x for x in (self._find_entity(schema["properties"][p], "{}.{}".format(path, p)) for p in schema["properties"] )
                                 if x is not None))

        return None

    def _generate_id(self):
        return str(uuid.uuid4())




