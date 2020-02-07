from meeshkan.sources.kafka import KafkaProcessor, KafkaProcessorConfig
from os import read
import pytest
from ..util import read_recordings_as_request_response

exchanges = read_recordings_as_request_response()

kafkaProcessorConfig = KafkaProcessorConfig(
    broker="localhost:9092", topic="example")


@pytest.fixture()
def test_processor(event_loop):
    processor = KafkaProcessor(kafkaProcessorConfig)
    app = processor.app
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    return processor


@pytest.mark.asyncio()
async def test_processing(test_processor: KafkaProcessor):
    async with test_processor.agent.test_context() as agent:
        await agent.put(exchanges[0])
        gen = agent.stream()
        res = agent.results
        assert res[0] == exchanges[0]
        """ async for g in agent:
            agent
            pass """


""" async def run_tests():
    app.conf.store = 'memory://'   # tables must be in-memory
    await test_processing()

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_tests()) """
