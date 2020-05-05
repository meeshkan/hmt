import asyncio
from dataclasses import dataclass
from typing import AsyncIterable, Tuple

import faust
from http_types.types import HttpExchange
from http_types.utils import HttpExchangeBuilder

from ..hmt_types import HttpExchangeStream
from .abstract import AbstractSource


@dataclass(frozen=True)
class KafkaSourceConfig:
    broker: str
    topic: str


class KafkaSource(AbstractSource):
    def __init__(self, config: KafkaSourceConfig):
        self.app = faust.App(
            "hmt-kafka-source", broker=config.broker, stream_wait_empty=False
        )

        faust_topic = self.app.topic(config.topic, key_type=str, value_type=str)

        @self.app.agent(faust_topic)
        async def recording_agent(stream):
            """Dummy faust agent reading values from Kafka topic and passing values on.

            Yields:
                [dict] -- HttpExchange dictionary objects
            """
            async for rec in stream:
                yield rec

        self.recording_agent = recording_agent

        self.worker = None
        self.worker_task = None

    async def http_exchange_stream(self) -> AsyncIterable[HttpExchange]:
        """Generator of HttpExchange objects.
        Does not generate any values until the underlying agent is started.

        Yields:
            [HttpExchange] -- HttpExchange object
        """
        async for rec in self.recording_agent.stream():
            yield HttpExchangeBuilder.from_dict(rec)

    async def start(
        self, loop: asyncio.AbstractEventLoop
    ) -> Tuple[HttpExchangeStream, asyncio.Task]:
        self.worker = faust.Worker(self.app, loop=loop, loglevel="info")

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        source = self.http_exchange_stream()

        worker_coro = start_worker(self.worker)
        self.worker_task = loop.create_task(worker_coro)

        return source, self.worker_task

    def shutdown(self):
        self.worker_task.cancel()
        self.worker.stop_and_shutdown()


__all__ = ["KafkaSource", "KafkaSourceConfig"]
