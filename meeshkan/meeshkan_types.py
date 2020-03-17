import asyncio
from typing import AsyncIterable, Awaitable, Callable, Tuple

from http_types import HttpExchange

from .build.result import BuildResult

HttpExchangeStream = AsyncIterable[HttpExchange]
BuildResultStream = AsyncIterable[BuildResult]

Source = Callable[[asyncio.AbstractEventLoop], Tuple[HttpExchangeStream, asyncio.Task]]
Sink = Callable[[BuildResultStream], Awaitable[None]]
