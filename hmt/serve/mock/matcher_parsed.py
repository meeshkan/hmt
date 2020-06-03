import typing
from openapi_typed_2 import OpenAPIObject


class Matcher:
    def __init__(self, specs: typing.List[OpenAPIObject]):
        self._config = dict()
        paths = []
        for spec in specs:
            for pathname, path_item in spec.paths.items():
                paths.append([x for x in pathname.split("/") if x != ""])


