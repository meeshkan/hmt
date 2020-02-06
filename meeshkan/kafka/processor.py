import asyncio
from typing import AsyncIterable

from http_types.utils import HttpExchangeBuilder

try:
    import faust
except ImportError:
    faust = None


__all__ = ["KafkaProcessorConfig", "KafkaProcessor"]


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

        self.stream = self.faust_topic.stream()

        @self.app.agent(self.faust_topic, sink=[])
        async def gen(recordings: AsyncIterable):
            async for recording in recordings:
                yield HttpExchangeBuilder.from_dict(recording)

        self.gen = gen

    @staticmethod
    def run(app: faust.App, loop: asyncio.AbstractEventLoop, loglevel='info'):
        worker = faust.Worker(app, loop=loop, loglevel=loglevel)

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        try:
            loop.run_until_complete(start_worker(worker))
        finally:
            worker.stop_and_shutdown()


if __name__ == '__main__':
    config = KafkaProcessorConfig(
        broker="localhost:9092", topic="express_recordings")  # TODO
    processor = KafkaProcessor(config)

    processor.app.main()
