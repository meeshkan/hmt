
import asyncio
from typing import Tuple

from .kafka import KafkaSource
from ..types import HttpExchangeStream


class AbstractSource:
    async def start(self, loop: asyncio.AbstractEventLoop) -> Tuple[HttpExchangeStream, asyncio.Task]:
        raise NotImplementedError("")

    def shutdown(self) -> None:
        raise NotImplementedError("")
