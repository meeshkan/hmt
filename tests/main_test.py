from meeshkan.schemabuilder.builder import BASE_SCHEMA
from meeshkan.__main__ import cli, _convert
from click.testing import CliRunner
from .util import read_recordings_as_strings
from hamcrest import assert_that, has_key
from pathlib import Path
from typing import List
import os
from openapi_typed_2 import OpenAPIObject, convert_from_openapi
import json

requests = read_recordings_as_strings()


def write_input_file(target_file: str, requests: List[str]):
    with open(target_file, 'w') as f:
        for request in requests:
            f.write(request)

def write_base_schema(target_file: str, schema: OpenAPIObject):
    with open(target_file, 'w') as f:
        f.write(json.dumps(convert_from_openapi(schema)))

def test_build_default_output_dir():
    runner = CliRunner()

    input_file = 'input.jsonl'
    base_schema = 'openapi.yml'

    with runner.isolated_filesystem():
        # Prepare input file
        write_input_file(input_file, requests)
        write_base_schema(base_schema, BASE_SCHEMA)

        runner_result = runner.invoke(
            cli, ['build', '-i', input_file, '-a', base_schema, '--source', 'file'])
        assert runner_result.exit_code == 0, "Exited with code {}, expected zero".format(runner_result.exit_code)
        assert Path("specs/").is_dir(), "Output directory specs/ should exist"

def test_build_cmd():
    """An uber test verifying build command input and output.
    """
    runner = CliRunner()

    input_file = 'input.jsonl'
    base_schema = 'openapi.yml'
    output_directory = 'out'

    with runner.isolated_filesystem():
        output_directory_path = Path(output_directory)
        # Prepare input file
        write_input_file(input_file, requests)
        write_base_schema(base_schema, BASE_SCHEMA)

        assert not output_directory_path.is_dir(
        ), "Output directory {} should not exist yet".format(output_directory)

        runner_result = runner.invoke(
            cli, ['build', '-i', input_file, '-o', output_directory, '-a', base_schema, '--source', 'file'])

        assert runner_result.exit_code == 0, "Exited with code {}, expected zero".format(runner_result.exit_code)

        assert output_directory_path.is_dir(), "Output directory {} should exist".format(output_directory_path.absolute)
        with open(os.path.join(output_directory, 'openapi.json'), 'r') as oai:
            build_result = json.loads(oai.read())

            # Verify result
            assert_that(build_result, has_key('openapi'))

    assert runner_result.exit_code == 0
    assert len(runner_result.output) == 0


def test_convert_cmd():
    runner = CliRunner()

    # Absolute path, can be accessed in Click's "isolated filesystem"
    input_file = Path('resources/recordings.pcap').resolve()
    output_file = 'recordings.jsonl'

    with runner.isolated_filesystem():

        assert not Path(output_file).is_file(
        ), "Expected output file {} to not exist".format(output_file)

        runner_result = runner.invoke(
            cli, ['convert', '-i', str(input_file), '-o', output_file])

        assert Path(output_file).is_file(
        ), "Expected output file {} to exist".format(output_file)

        assert runner_result.exit_code == 0

######
## TODO: these tests are basically identical, with the one below
## only existing to get a more complete error log in case the one
## above is broken.

def test_convert_cmd_without_invocation():
    runner = CliRunner()

    # Absolute path, can be accessed in Click's "isolated filesystem"
    input_file = Path('resources/recordings.pcap').resolve()
    output_file = 'recordings.jsonl'

    with runner.isolated_filesystem():

        assert not Path(output_file).is_file(
        ), "Expected output file {} to not exist".format(output_file)

        runner_result = _convert(str(input_file), output_file)

        assert Path(output_file).is_file(
        ), "Expected output file {} to exist".format(output_file)