import asyncio
from typing import Callable

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

    def __init__(self, broker, topic, consumer: Consumer):
        self.broker = broker
        self.topic = topic
        self.consumer = consumer


class KafkaProcessor:

    def __init__(self, options: KafkaProcessorConfig):
        self.options = options
        self.app = faust.App('myapp', broker=options.broker)
        self._faust_topic = self.app.topic(
            options.topic, key_type=str, value_type=str)
        self._consumer = options.consumer

        @self.app.agent(self._faust_topic, sink=[self._consumer])
        async def gen(recordings):
            async for recording in recordings:
                # Or just remove the sink and do `self._consumer(recording)`...
                yield recording
                # await agen.asend(recording)  # Push to generator

    @staticmethod
    def run(app: faust.App, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(), loglevel='info'):
        worker = faust.Worker(app, loop=loop, loglevel=loglevel)

        async def start_worker(worker: faust.Worker) -> None:
            await worker.start()

        try:
            loop.run_until_complete(start_worker(worker))
        finally:
            worker.stop_and_shutdown()


if __name__ == '__main__':
    config = KafkaProcessorConfig(
        broker="localhost:9092", topic="express_recordings", consumer=lambda x: print(x))
    processor = KafkaProcessor(config)

    processor.app.main()
