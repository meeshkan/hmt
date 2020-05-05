import abc
import asyncio
from typing import Optional, Tuple

from ..hmt_types import HttpExchangeStream


class AbstractSource(abc.ABC):
    """Abstract source of HTTP exchanges.
    """

    @abc.abstractmethod
    async def start(
        self, loop: asyncio.AbstractEventLoop
    ) -> Tuple[HttpExchangeStream, Optional[asyncio.Task]]:
        """Start source task to read HTTP Exchanges.

        Arguments:
            loop {asyncio.AbstractEventLoop} -- Event loop to use.

        Returns:
            Tuple[HttpExchangeStream, Optional[asyncio.Task]] -- Stream of HttpExchange objects and possibly a reader task.
        """
        raise NotImplementedError("")

    @abc.abstractmethod
    def shutdown(self) -> None:
        """Shutdown source.
        """
        raise NotImplementedError("")
