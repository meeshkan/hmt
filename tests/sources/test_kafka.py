from meeshkan.sources.kafka import KafkaProcessor, KafkaProcessorConfig, KafkaSource
from os import read
import pytest
from ..util import read_recordings_as_request_response
from hamcrest import *

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
        for exchange in exchanges:
            await agent.put(exchange)
        res = agent.results
        assert_that(list(res.keys()), has_length(168))
        assert_that(res[0], is_(exchanges[0]))


@pytest.mark.asyncio()
async def test_source(test_processor: KafkaProcessor):
    # TODO How to test the source stream with `agent.test_context()` (without running Kafka)?
    pass
