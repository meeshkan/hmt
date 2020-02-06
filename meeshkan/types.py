import asyncio
from typing import Callable, Awaitable, AsyncIterable, Tuple, Optional
from http_types import HttpExchange
from .schemabuilder.result import BuildResult

HttpExchangeStream = AsyncIterable[HttpExchange]
BuildResultStream = AsyncIterable[BuildResult]

Source = Callable[[asyncio.events.AbstractEventLoop],
                  Tuple[HttpExchangeStream, asyncio.Task]]
Sink = Callable[[BuildResultStream], Awaitable[None]]


class AbstractSource:
    async def start(self, loop: asyncio.AbstractEventLoop) -> Tuple[HttpExchangeStream, Optional[asyncio.Task]]:
        raise NotImplementedError("")

    def shutdown(self) -> None:
        raise NotImplementedError("")
