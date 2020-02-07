import asyncio
import json
from meeshkan.sinks.file import FileSystemSink
from meeshkan.sources.file import FileSource

from typing import Sequence
from .types import *
from .sources import AbstractSource, KafkaSource
from .sources.kafka import KafkaProcessorConfig
from meeshkan.schemabuilder.builder import build_schema_async

import click
from http_types import HttpExchangeReader

from meeshkan.schemabuilder.result import BuildResult
from meeshkan.convert.pcap import convert_pcap

from .schemabuilder import build_schema_online
from .schemabuilder.writer import write_build_result
from .config import setup
from .logger import get as getLogger

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
        for sink in sinks:
            sink.flush()


def run_from_source(source: AbstractSource, sinks: Sequence[AbstractSink]):
    loop = asyncio.get_event_loop()

    async def run(loop):
        exchange_stream, source_task = await source.start(loop)

        result_stream = build_schema_async(exchange_stream)

        sink_task = loop.create_task(write_to_sink(result_stream, sinks))

        if source_task is None:
            await asyncio.gather(sink_task)
        else:
            await asyncio.gather(source_task, sink_task)
    try:
        loop.run_until_complete(run(loop))
    finally:
        source.shutdown()
        loop.close()


@click.command()
@click.option("-i", "--input-file", required=False, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=True, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output directory. If the directory does not exist, it is created if the parent directory exists.")
@click.option("--source", required=False, default='file', type=str, help="Source to read recordings from. For example, 'kafka'")
@click.option("--sink", required=False, type=str,  help="Sink where to write results.")
def build(input_file, out, source, sink):
    """
    Build OpenAPI schema from recordings.
    """

    # TODO Support sinks
    # sinks: Sequence[Sink] = [file_sink(out)]

    if input_file is not None and source != "file":
        raise Exception("Only specify input-file for --source file")

    sinks = [FileSystemSink(out)]

    if source == 'kafka':
        kafka_source = KafkaSource(config=KafkaProcessorConfig(
            broker="localhost:9092",
            topic="express_recordings"))

        run_from_source(kafka_source, sinks=sinks)
    elif source == 'file':
        if input_file is None:
            raise Exception("Option --input-file for source 'file' required.")
        file_source = FileSource(input_file)
        run_from_source(file_source, sinks=sinks)
    elif source is not None:
        raise Exception("Unknown source {}".format(source))
    elif input_file is not None:
        requests = HttpExchangeReader.from_jsonl(input_file)
        schema = build_schema_online(requests)
        build_result = BuildResult(openapi=schema)
        log("Result: %s", json.dumps(schema))
        write_build_result(out, build_result)
    else:
        raise Exception("Either --source or --input-file is required.")


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
