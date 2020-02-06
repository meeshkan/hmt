import asyncio
from . import AbstractSource
from typing import Tuple
from ..kafka import KafkaProcessor, KafkaProcessorConfig
import faust
from ..types import HttpExchangeStream


class KafkaSource(AbstractSource):

    def __init__(self, config: KafkaProcessorConfig):
        self.config = config
        self.processor = KafkaProcessor(config)
        self.recording_stream = self.processor.gen.stream()
        self.worker = None
        self.worker_task = None

    async def start(self, loop: asyncio.AbstractEventLoop) -> Tuple[HttpExchangeStream, asyncio.Task]:
        self.worker = faust.Worker(
            self.processor.app, loop=loop, loglevel='info')

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        source = self.recording_stream
        worker_coro = start_worker(self.worker)
        self.worker_task = loop.create_task(worker_coro)

        return (source, self.worker_task)

    def shutdown(self):
        self.worker_task.cancel()
        self.worker.stop_and_shutdown()
