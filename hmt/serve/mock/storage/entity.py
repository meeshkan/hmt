import typing
import uuid

from http_types import Request
from jsonpath_rw import Fields, parse
from openapi_typed_2 import (
    OpenAPIObject,
    Operation,
    PathItem,
    RequestBody,
    convert_from_openapi,
)

from hmt.build.paths import _match_to_path
from hmt.serve.utils.opanapi_ext import ApiOperation, get_x


def replace_path(expression, doc, val):
    if isinstance(expression, Fields):
        doc[expression.fields[0]] = val
    else:
        occurrencies = expression.left.find(doc)
        assert len(occurrencies) > 0, "Got empty occurrencies list"

        for place in occurrencies:
            place.value[expression.right.fields[0]] = val

    return doc


class EntityPathItem:
    """
    The EntityPathItem object contains various settings to deal with entities
    appeared in different methods of a single PathItem in an OpenAPI spec.
    """

    methods = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]

    def __init__(self, entity_name: str, pathname: str, path_item: PathItem):
        self._entity_name = entity_name
        self._pathname = pathname
        self._path_item = path_item
        self._request_entity_selectors = self._build_request_entity_selectors(path_item)

    def _build_request_entity_selectors(self, path_item: PathItem) -> typing.Dict:
        res = {}
        for method_name in self.methods:
            method: Operation = getattr(path_item, method_name)
            operation = (
                ApiOperation.UNKNOWN
                if method is None
                else ApiOperation(
                    get_x(method, "x-hmt-operation", ApiOperation.UNKNOWN)
                )
            )
            if operation == ApiOperation.UPSERT or operation == ApiOperation.INSERT:
                request_body = typing.cast(RequestBody, method.requestBody)
                if "application/json" in request_body.content:
                    schema = request_body.content["application/json"].schema
                    if schema is not None:
                        entity_path = self._find_entity(
                            convert_from_openapi(schema), "$"
                        )
                        if res is not None:
                            res[method_name] = parse(entity_path)
        return res

    def _find_entity(self, schema, path):
        if "$ref" in schema:
            name = schema["$ref"].split("/")[3]
            if name == self._entity_name:
                return path
        elif schema.get("type", None) == "array":
            if "items" not in schema:
                return None
            elif isinstance(schema["items"], list):
                return next(
                    (
                        x
                        for x in (
                            self._find_entity(item, path + "[*]")
                            for item in schema["items"]
                        )
                        if x is not None
                    )
                )
            else:
                return self._find_entity(schema["items"], path + "[*]")
        elif schema.get("type", "object") == "object" and "properties" in schema:
            return next(
                (
                    x
                    for x in (
                        self._find_entity(
                            schema["properties"][p], "{}.{}".format(path, p)
                        )
                        for p in schema["properties"]
                    )
                    if x is not None
                )
            )

        return None

    def filter(self, request: Request):
        """
        Builds a filter from an http request to search for specific entities. It is currently unsupported,
        so we return everything that is inside a storage for every search request.
        :param request:
        :return:
        """
        return lambda x: True

    def id_filter(self, request: Request):
        """
        Extracts id from an http request arguments, e.g. GET /items?id=123. It is currently unsupported.
        :param request:
        :return:
        """
        return None

    def extract_id(self, request: Request):
        match = _match_to_path(request.pathname, self._pathname)
        if match is None or "id" not in match:
            return self.id_filter(request)

        return match["id"]

    def extract_entity(self, request: Request):
        """
        Extracts entity from an http request. Currently suppored case is to extract entity from a specific path
        inside a POST body.
        :param request:
        :return:
        """
        found = self._request_entity_selectors[request.method.value].find(
            request.bodyAsJson
        )
        if len(found) == 0:
            return None
        return found[0].value


class Entity:
    """
    The Entity object can be used as a typing.Dict[str, typing.Any] in callbacks. It also contains utility functions
    to implement automatic insetion/extraction logic extracted from an OpenAPI spec.
    """

    def __init__(self, name: str, spec: OpenAPIObject):
        self._name = name
        self._id_path = parse(spec.components.schemas[name]._x["x-hmt-id-path"])

        self._path_config: typing.Dict[str, EntityPathItem] = {}
        for pathname, path_item in spec.paths.items():
            if get_x(path_item, "x-hmt-entity") == self.name:
                self.add_path(pathname, path_item)

        self._data = dict()

    @property
    def name(self):
        return self._name

    def add_path(self, pathname: str, path_item: PathItem):
        self._path_config[pathname] = EntityPathItem(self.name, pathname, path_item)

    def query(self, path_item: str, request: Request):
        """
        Queries a set of entities. The current implementation doesn't support filtering.
        So it always return the full list of entities.
        :param path_item:
        :param request:
        :return:
        """
        filter = self._path_config[path_item].filter(request)
        return [x for x in self._data.values() if filter(x)]

    def query_one(self, path_item: str, request: Request):
        """
        Queries a single entities by an id extracted from an http request.
        :param path_item:
        :param request:
        :return:
        """
        id = self._path_config[path_item].extract_id(request)
        return self._data.get(id, {}) if id is not None else {}

    def insert_from_request(self, path_item: str, request: Request) -> typing.Any:
        """
        Extracts an entity from an http request. It is used to automatically post new data into a mock storage.
        If an entity doesn't contain an id it will be generated automatically.
        :param path_item:
        :param request:
        :return:
        """
        entity_val = self._path_config[path_item].extract_entity(request)
        id = self._path_config[path_item].extract_id(request)
        if id is None:
            id = self._extract_id(entity_val)
        if id is None:
            id = self._generate_id()
        entity_val = replace_path(self._id_path, entity_val, id)
        self._data[id] = entity_val
        return entity_val

    def insert(self, entity):
        """
        Inserts an entity
        :param entity:
        """
        id = self._extract_id(entity)
        self._data[id] = entity
        return entity

    def upsert_from_request(self, path_item: str, request: Request) -> typing.Any:
        """
        Either inserts or updates an entity in a storage depending on
        whether an entity with the same id presents in it or not.
        :param path_item:
        :param request:
        :return:
        """
        entity_val = self._path_config[path_item].extract_entity(request)
        id = self._extract_id(entity_val)
        id = self._path_config[path_item].extract_id(request) if id is None else id
        if id is None or id not in self._data:
            id = self._generate_id() if id is None else id
            entity_val = replace_path(self._id_path, entity_val, id)
            self._data[id] = entity_val
            return entity_val
        else:
            return self._merge(self._data[id], entity_val)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __delitem__(self, key):
        del self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def keys(self):
        return self._data.keys()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def clear(self):
        self._data.clear()

    def __len__(self):
        return len(self._data)

    def _generate_id(self):
        return str(uuid.uuid4())

    def _merge(self, entity1, entity2) -> typing.Any:
        for k, v in entity2.items():
            entity1[k] = v
        return entity1

    def _extract_id(self, entity):
        found = self._id_path.find(entity)
        if len(found) == 0:
            return None
        return found[0].value
