import json
from meeshkan.schemabuilder.builder import BASE_SCHEMA, update_openapi

import click
from http_types import HttpExchangeBuilder, HttpExchangeReader

from meeshkan.schemabuilder.result import BuildResult
from meeshkan.convert.pcap import convert_pcap

from .schemabuilder import build_schema_online
from .schemabuilder.writer import write_build_result
from .config import setup
from .logger import get as getLogger
from .kafka import KafkaProcessor, KafkaProcessorConfig

LOGGER = getLogger(__name__)


def log(*args):
    LOGGER.debug(*args)


@click.group()
def cli():
    """
    Meeshkan CLI.
    """
    setup()  # Ensure setup is done before invoking the CLI.


@click.command()
@click.option("-i", "--input-file", required=False, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=False, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output directory. If the directory does not exist, it is created if the parent directory exists.")
@click.option("-c", "--consumer", required=False, type=str, help="Consumer. For example,'kafka'")
def build(input_file, out, consumer):
    """
    Build OpenAPI schema from recordings.
    """

    if consumer is None and input_file is None:
        raise Exception("Either --consumer or --input-file is required.")

    if consumer == 'kafka':
        schema = BASE_SCHEMA

        def consume(json_exchange):
            global schema
            exchange = HttpExchangeBuilder.from_dict(json_exchange)
            schema = update_openapi(schema, exchange)
            print(schema)

        config = KafkaProcessorConfig(
            broker="localhost:9092",
            topic="express_recordings",
            consumer=consume)
        processor = KafkaProcessor(config)

        processor.process()
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
