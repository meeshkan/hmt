import asyncio
from typing import AsyncIterable, TextIO, Tuple

from http_types.types import HttpExchange
from http_types.utils import HttpExchangeReader

from .abstract import AbstractSource


class FileSource(AbstractSource):
    def __init__(self, input_file: TextIO):
        self.input_file = input_file

    async def start(
        self, loop: asyncio.AbstractEventLoop
    ) -> Tuple[AsyncIterable[HttpExchange], None]:
        # print(self.input_file)

        async def read():
            for line in self.input_file:
                if line.rstrip() not in [b"", ""]:  # prevent reading empty space
                    yield HttpExchangeReader.from_json(line)

        return read(), None

    def shutdown(self):
        pass
