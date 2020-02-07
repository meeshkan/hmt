from typing import Awaitable
import asyncio
from typing import Callable, Awaitable, AsyncIterable, Tuple
from http_types import HttpExchange
from .schemabuilder.result import BuildResult

HttpExchangeStream = AsyncIterable[HttpExchange]
BuildResultStream = AsyncIterable[BuildResult]

Source = Callable[[asyncio.events.AbstractEventLoop],
                  Tuple[HttpExchangeStream, asyncio.Task]]
Sink = Callable[[BuildResultStream], Awaitable[None]]
