from http_types.utils import HttpExchangeBuilder
from typing import AsyncIterable
import asyncio
from .abstract import AbstractSource
from typing import Tuple

from ..meeshkan_types import HttpExchangeStream
try:
    import faust
except ImportError:
    faust = None


class KafkaProcessorConfig:
    broker: str
    topic: str

    def __init__(self, broker, topic):
        self.broker = broker
        self.topic = topic


class KafkaProcessor:

    def __init__(self, options: KafkaProcessorConfig):
        self.options = options
        self.app = faust.App('myapp', broker=options.broker,
                             stream_wait_empty=False)
        self.faust_topic = self.app.topic(
            options.topic, key_type=str, value_type=str)

        # self.stream = self.faust_topic.stream()

        @self.app.agent(self.faust_topic, sink=[])
        async def gen(recordings: AsyncIterable):
            async for recording in recordings:
                yield HttpExchangeBuilder.from_dict(recording)

        self.agent = gen

    @staticmethod
    def run(app: faust.App, loop: asyncio.AbstractEventLoop, loglevel='info'):
        worker = faust.Worker(app, loop=loop, loglevel=loglevel)

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        try:
            loop.run_until_complete(start_worker(worker))
        finally:
            worker.stop_and_shutdown()


class KafkaSource(AbstractSource):

    def __init__(self, config: KafkaProcessorConfig):

        if faust is None:
            raise Exception(
                "Cannot find module faust. Try `pip install meeshkan[kafka]`")

        self.config = config
        self.processor = KafkaProcessor(config)
        self.recording_stream = self.processor.agent.stream()
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

        return source, self.worker_task

    def shutdown(self):
        self.worker_task.cancel()
        self.worker.stop_and_shutdown()


__all__ = ["KafkaProcessorConfig", "KafkaProcessor", "KafkaSource"]
