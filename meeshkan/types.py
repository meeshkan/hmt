import abc
from typing import Union, Awaitable
import asyncio
from typing import Callable, Awaitable, AsyncIterable, Tuple
from http_types import HttpExchange
from .schemabuilder.result import BuildResult

HttpExchangeStream = AsyncIterable[HttpExchange]
BuildResultStream = AsyncIterable[BuildResult]

Source = Callable[[asyncio.events.AbstractEventLoop],
                  Tuple[HttpExchangeStream, asyncio.Task]]
Sink = Callable[[BuildResultStream], Awaitable[None]]


class AbstractSink(abc.ABC):

    @abc.abstractmethod
    def push(self, result: BuildResult) -> Union[Awaitable[None], None]:
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
    def flush(self) -> Union[Awaitable[None], None]:
        raise NotImplementedError("Not implemented")
