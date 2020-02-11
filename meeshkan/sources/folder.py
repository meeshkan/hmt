from typing import AsyncIterable, Tuple, cast
from http_types.types import HttpExchange
from http_types.utils import HttpExchangeReader
from .abstract import AbstractSource
from ..schemabuilder.schema import validate_openapi_object
from ..schemabuilder.builder import BASE_SCHEMA
from yaml import safe_load
import os
import asyncio
from openapi_typed import OpenAPIObject

class FolderSource(AbstractSource):

    def __init__(self, input_folder: str):
        self.input_folder = input_folder

    async def start(self, loop: asyncio.events.AbstractEventLoop) -> Tuple[AsyncIterable[HttpExchange], None]:
        # print(self.input_folder)

        async def read():
            for line in self.input_folder:
                yield HttpExchangeReader.from_json(line)

        return read(), None

    def shutdown(self):
        pass

    def initial_openapi_spec(self) -> OpenAPIObject:
        for f in os.listdir(self.input_folder):
            try:
                with open(os.path.join(self.input_folder, f)) as infile:
                    maybe_openapi = safe_load(infile.read())
                    # will raise if not an API spec
                    validate_openapi_object(maybe_openapi)
                    return cast(OpenAPIObject, maybe_openapi)
            except:
                continue
        return BASE_SCHEMA
