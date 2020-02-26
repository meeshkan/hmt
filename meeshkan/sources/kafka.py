import asyncio
from dataclasses import dataclass
from typing import Tuple

import faust
from http_types.utils import HttpExchangeBuilder

from .abstract import AbstractSource
from ..meeshkan_types import HttpExchangeStream


@dataclass(frozen=True)
class KafkaSourceConfig:
    broker: str
    topic: str


class KafkaSource(AbstractSource):
    def __init__(self, config: KafkaSourceConfig):
        self.app = faust.App('meeshkan-kafka-source',
                              broker=config.broker,
                              stream_wait_empty=False)

        faust_topic = self.app.topic(config.topic, key_type=str, value_type=str)

        async def http_exchange_stream():
            async for rec in faust_topic.stream():
                yield HttpExchangeBuilder.from_dict(rec)

        self.http_exchange_stream = http_exchange_stream

        self.worker = None
        self.worker_task = None

    async def start(self, loop: asyncio.AbstractEventLoop) -> Tuple[HttpExchangeStream, asyncio.Task]:
        self.worker = faust.Worker(self.app, loop=loop, loglevel='info')

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        source = self.http_exchange_stream()
        worker_coro = start_worker(self.worker)
        self.worker_task = loop.create_task(worker_coro)

        return source, self.worker_task

    def shutdown(self):
        self.worker_task.cancel()
        self.worker.stop_and_shutdown()


__all__ = ["KafkaProcessorConfig", "KafkaProcessor", "KafkaSource"]
