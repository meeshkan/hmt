import pytest
from hamcrest import assert_that, has_length

from hmt.sources.kafka import KafkaSource, KafkaSourceConfig

from ..util import read_recordings_as_dict

exchanges = read_recordings_as_dict()

kafkaSourceConfig = KafkaSourceConfig(broker="'kafka://localhost:9092", topic="example")


@pytest.fixture()
def kafka_source(event_loop):
    processor = KafkaSource(kafkaSourceConfig)
    app = processor.app
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = "memory://"
    app.flow_control.resume()
    return processor


@pytest.mark.asyncio()
async def test_processing(kafka_source: KafkaSource):
    async with kafka_source.recording_agent.test_context() as agent:
        kafka_source.recording_agent = agent
        for exchange in exchanges:
            await agent.put(exchange)
        res = agent.results
        assert_that(list(res.keys()), has_length(168))
        """
        # TODO How to test that kafka_source.http_exchange_stream() works without running Kafka?
        exchange_stream = kafka_source.http_exchange_stream()
        exchange_objs = [exchange async for exchange in exchange_stream]
        assert_that(exchange_objs[0], has_property("request"))
        """
