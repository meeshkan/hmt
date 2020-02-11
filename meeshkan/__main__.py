import asyncio
import json
import click
import os
from typing import Sequence

from .config import setup
from .logger import get as getLogger
from .schemabuilder.builder import build_schema_async
from .convert.pcap import convert_pcap
from .sinks import AbstractSink, FileSystemSink
from .sources import AbstractSource, KafkaSource, FileSource, FolderSource
from .sources.kafka import KafkaProcessorConfig
from .types import *


LOGGER = getLogger(__name__)


def log(*args):
    LOGGER.debug(*args)


@click.group()
def cli():
    """
    Meeshkan CLI.
    """
    setup()  # Ensure setup is done before invoking the CLI.


async def write_to_sink(result_stream: BuildResultStream, sinks: Sequence[AbstractSink]):
    try:
        async for result in result_stream:
            for sink in sinks:
                sink.push(result)
    finally:
        LOGGER.debug("Flushing all sinks")
        for sink in sinks:
            sink.flush()


def run_from_source(source: AbstractSource, sinks: Sequence[AbstractSink]):
    loop = asyncio.get_event_loop()

    async def run(loop):
        source_stream, source_task = await source.start(loop)
        result_stream = build_schema_async(source_stream, source.initial_openapi_spec())
        sink_task = loop.create_task(write_to_sink(result_stream, sinks))

        if source_task is not None:
            # TODO Kafka source behaves a bit bad at SIG_INT: it does not raise but returns,
            # leaving the sink task to wait for new input that never arrives. Therefore
            # one cannot `await sink_task` here, at least not without timeout
            await source_task
            try:
                await asyncio.wait_for(sink_task, timeout=3.0)
            except asyncio.TimeoutError:
                LOGGER.warn("Timeout on waiting for sink task to finish.")
        else:
            await sink_task

    try:
        loop.run_until_complete(run(loop))
    finally:
        LOGGER.info("Shutting down source")
        source.shutdown()
        loop.close()


@click.command()
@click.option("-i", "--input-file", required=False, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-f", "--input-folder", required=False, type=click.Path(exists=True, file_okay=False, writable=True, readable=True), help="Input folder.")
@click.option("-o", "--out", required=True, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output directory. If the directory does not exist, it is created if the parent directory exists.")
@click.option("--kafka", required=False, default=False, type=bool, help="Read from kafka")
@click.option("--sink", required=False, type=str,  help="Sink where to write results.")
def build(input_file, input_folder, out, kafka, sink):
    """
    Build OpenAPI schema from HTTP exchanges.
    """

    sinks = [FileSystemSink(out)]

    source = None
    if kafka:
        # TODO Kafka configuration
        source = KafkaSource(config=KafkaProcessorConfig(
            broker="localhost:9092",
            topic="express_recordings"))
    elif input_file:
        source = FileSource(input_file)
    elif input_folder:
        source = FolderSource(input_folder)

    if not source:
        raise ValueError("Unclear source.")

    run_from_source(source, sinks=sinks)


@click.command()
@click.option("-i", "--input-file", required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, allow_dash=True), help="Path to a packet capture file.")
@click.option("-o", "--out", required=False, default='recordings.jsonl', type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, allow_dash=True), help="Output file.")
def convert(input_file, out):
    """
    Convert recordings from PCAP to JSONL format.
    """

    if not input_file.endswith('.pcap'):
        raise ValueError(
            'Only .pcap files are accepted as input. Got: {}'.format(input_file))

    request_response_pairs = convert_pcap(input_file)

    log("Writing to: %s", out)

    counter = 0
    with open(out, 'w') as f:
        for reqres in request_response_pairs:
            f.write((json.dumps(reqres) + "\n"))
            counter += 1

    log("Wrote %d lines.", counter)


cli.add_command(build)  # type: ignore
cli.add_command(convert)  # type: ignore

if __name__ == '__main__':
    cli()
