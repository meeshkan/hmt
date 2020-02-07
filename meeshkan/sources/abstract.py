import abc
import asyncio
from typing import Tuple, Optional
from ..types import HttpExchangeStream


class AbstractSource(abc.ABC):
    @abc.abstractmethod
    async def start(self, loop: asyncio.AbstractEventLoop) -> Tuple[HttpExchangeStream, Optional[asyncio.Task]]:
        raise NotImplementedError("")

    @abc.abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError("")
