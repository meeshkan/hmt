from meeshkan.schemabuilder.result import BuildResult
from meeshkan.convert.pcap import convert_pcap
import click
import json
from http_types import RequestResponseBuilder

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


@click.command()
@click.option("-i", "--input-file", required=True, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=False, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output directory. If the directory does not exist, it is created if the parent directory exists.")
def build(input_file, out):
    """
    Build OpenAPI schema from recordings.
    """
    requests = (RequestResponseBuilder.from_dict(
        json.loads(line)) for line in input_file)

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
        raise ValueError('Only .pcap files are accepted as input. Got: {}'.format(input_file))

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
