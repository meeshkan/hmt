import asyncio
import json

from typing import Sequence
from .types import *
from .sources.kafka import KafkaSource, KafkaProcessorConfig
from meeshkan.schemabuilder.builder import build_schema_agen

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


def file_sink(out: str) -> Sink:
    async def handle(results: BuildResultStream):
        async for result in results:
            write_build_result(out, result)

    return handle


@click.command()
@click.option("-i", "--input-file", required=False, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=False, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output directory. If the directory does not exist, it is created if the parent directory exists.")
@click.option("--source", required=False, type=str, help="Source to read recordings from. For example, 'kafka'")
@click.option("--sink", required=False, type=str,  help="Sink where to write results.")
def build(input_file, out, source, sink):
    """
    Build OpenAPI schema from recordings.
    """

    if source is None and input_file is None:
        raise Exception("Either --source or --input-file is required.")

    # TODO Support sinks
    # sinks: Sequence[Sink] = [file_sink(out)]

    if source == 'kafka':

        loop = asyncio.get_event_loop()

        kafka_source = KafkaSource(config=KafkaProcessorConfig(
            broker="localhost:9092",
            topic="express_recordings"))

        async def run(loop):
            exchange_iterable, source_task = await kafka_source.start(loop)

            builder_coro = build_schema_agen(
                exchange_iterable.__aiter__(), lambda x: print(x))

            builder_task = loop.create_task(builder_coro)

            await source_task

        try:
            loop.run_until_complete(run(loop))
        finally:
            kafka_source.shutdown()

        return

    requests = HttpExchangeReader.from_jsonl(input_file)

    schema = build_schema_online(requests)

    build_result = BuildResult(openapi=schema)

    log("Result: %s", json.dumps(schema))
    write_build_result(out, build_result)


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
