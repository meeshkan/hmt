import asyncio
from typing import AsyncIterable, Callable, Any

try:
    import faust
except ImportError:
    faust = None


__all__ = ["KafkaProcessorConfig", "KafkaProcessor"]


Consumer = Callable[[str], None]


class KafkaProcessorConfig:
    broker: str
    topic: str
    consumer: Consumer
    out: Any

    def __init__(self, broker, topic, out):
        self.broker = broker
        self.topic = topic
        self.out = out


class KafkaProcessor:

    def __init__(self, options: KafkaProcessorConfig):
        self.options = options
        self.app = faust.App('myapp', broker=options.broker)
        self.faust_topic = self.app.topic(
            options.topic, key_type=str, value_type=str)
        self.out = options.out

        @self.app.agent(self.faust_topic, sink=[])
        async def gen(recordings: AsyncIterable):
            async for recording in recordings:
                # Or just remove the sink and do `self._consumer(recording)`...
                # await self.out.asend(recording)
                yield recording
                # await agen.asend(recording)  # Push to generator
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
        broker="localhost:9092", topic="express_recordings", out=None)  # TODO
    processor = KafkaProcessor(config)

    processor.app.main()
