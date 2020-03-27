import typing
import uuid

from http_types import Request
from jsonpath_rw import parse
from meeshkan.build.paths import _match_to_path
from openapi_typed_2 import PathItem, Operation, Reference


class EntityPathItem:
    methods = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']

    def __init__(self, entity_name, pathname: str, path_item: PathItem):
        self._entity_name = entity_name
        self._pathname = pathname
        self._path_item = path_item
        self._request_entity_selectors = self._build_request_entity_selectors(path_item)

    def _build_request_entity_selectors(self, path_item: PathItem) -> typing.Mapping[str, typing.Callable]:
        res: typing.Dict[str, typing.Callable] = {}
        for method_name in self.methods:
            method: Operation = getattr(path_item, method_name)
            if method is not None and method._x is not None and "x-meeshkan-operation" in method._x:
                if method._x["x-meeshkan-operation"] == "insert" or method._x["x-meeshkan-operation"] == "upsert":
                    if "application/json" in method.requestBody.content:
                        schema = method.requestBody.content["application/json"].schema
                        if schema is not None:
                            entity_path = self._find_entity(schema, "$")
                            if res is not None:
                                res[method_name] = parse(entity_path)
        return res

    def _find_entity(self, schema, path):
        if isinstance(schema, Reference):
            name = schema._ref.split("/")[3]
            if name == self._entity_name:
                return path
        elif schema.get("type", None) == "array":
            if "items" not in schema:
                return None
            elif isinstance(schema["items"], list):
                return next((x for x in (self._find_entity(item, path + "[*]") for item in schema["items"])
                             if x is not None))
            else:
                return self._find_entity(schema["items"], path + "[*]")
        elif schema.get("type", "object") == "object" and "properties" is schema:
            return next((x for x in (self._find_entity(schema["properties"][p], "{}.{}".format(path, p)) for p in
                                     schema["properties"])
                         if x is not None))

        return None

    def filter(self, request: Request):
        return lambda x: True

    def id_filter(self, request: Request):
        return None

    def extract_id(self, request: Request):
        match = _match_to_path(self._pathname, request.pathname)
        if match is None or not "id" in match:
            return self.id_filter(request)

        return match["id"]

    def extract_entity(self, request: Request):
        found = self._request_entity_selectors[request.method.value].find(request.bodyAsJson)
        if len(found) == 0:
            return None
        return found[0].value


class Entity:
    def __init__(self, name, schema):
        self._name = name
        self._path_config: typing.Dict[str, EntityPathItem] = {}
        self._id_path = parse(schema._x["x-meeshkan-id-path"])

        self._data = dict()

    @property
    def name(self):
        return self._name

    def add_path(self, pathname: str, path_item: PathItem):
        self._path_config[pathname] = EntityPathItem(self.name, pathname, path_item)

    def query(self, path_item: str, request: Request):
        return [x for x in self._data.values() if self._path_config[path_item].filter(request)]

    def query_one(self, path_item: str, request: Request):
        id = self._path_config[path_item].extract_id(request)
        return self._data.get(id, {}) if id is not None else {}



    def insert_from_request(self, path_item: str, request: Request):
        id = self._path_config[path_item].extract_id(request)
        if id is None:
            id = self._generate_id()
        entity_val = self._path_config[path_item].extract_entity(request)
        entity_val = self._id_path.set(entity_val, id)
        self._data[id] = entity_val
        return entity_val

    def insert(self, entity):
        id = self._extract_id(entity)
        self._data[id] = entity

    def upsert_from_request(self, path_item: str, request: Request):
        id = self._path_config[path_item].extract_id(request)
        if id is None:
            return self.insert_from_request(path_item, request)
        else:
            entity_val = self._path_config[path_item].extract_entity(request)
            return self._merge(self._data[id], entity_val)

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

    def clear(self):
        self._data.clear()

    def _generate_id(self):
        return str(uuid.uuid4())

    def _merge(self, entity1, entity2):
        for k, v in entity2.items():
            entity1[k] = v
        return entity1

    def _extract_id(self, entity):
        found = self._id_path.find(entity)
        if len(found) == 0:
            return None
        return found[0].value

