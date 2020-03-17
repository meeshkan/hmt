import json
import os
from pathlib import Path
from typing import List

import pkg_resources
from click.testing import CliRunner
from hamcrest import assert_that, has_key
from openapi_typed_2 import OpenAPIObject, convert_from_openapi

from meeshkan.__main__ import cli
from meeshkan.build.builder import BASE_SCHEMA
from meeshkan.config import DEFAULT_SPECS_DIR

from .util import read_recordings_as_strings

requests = read_recordings_as_strings()


def write_input_file(target_file: str, requests: List[str]):
    with open(target_file, "w") as f:
        for request in requests:
            f.write(request)


def write_base_schema(target_file: str, schema: OpenAPIObject):
    with open(target_file, "w") as f:
        f.write(json.dumps(convert_from_openapi(schema)))


def test_build_default_output_dir():
    runner = CliRunner()

    input_file = "input.jsonl"
    base_schema = "openapi.yml"

    with runner.isolated_filesystem():
        # Prepare input file
        write_input_file(input_file, requests)
        write_base_schema(base_schema, BASE_SCHEMA)

        runner_result = runner.invoke(
            cli, ["build", "-i", input_file, "-a", base_schema, "--source", "file"]
        )
        assert (
            runner_result.exit_code == 0
        ), "Exited with code {}, expected zero".format(runner_result.exit_code)
        expected_outputdir_path = Path(DEFAULT_SPECS_DIR)
        assert expected_outputdir_path.is_dir(), "Output directory specs/ should exist"
        with open(expected_outputdir_path.joinpath("openapi.json"), "r") as oai:
            build_result = json.loads(oai.read())

            # Verify result
            assert_that(build_result, has_key("openapi"))


def test_build_cmd():
    """An uber test verifying build command input and output.
    """
    runner = CliRunner()

    input_file = "input.jsonl"
    base_schema = "openapi.yml"
    output_directory = "out"

    with runner.isolated_filesystem():
        output_directory_path = Path(output_directory)
        # Prepare input file
        write_input_file(input_file, requests)
        write_base_schema(base_schema, BASE_SCHEMA)

        assert (
            not output_directory_path.is_dir()
        ), "Output directory {} should not exist yet".format(output_directory)

        runner_result = runner.invoke(
            cli,
            [
                "build",
                "-i",
                input_file,
                "-o",
                output_directory,
                "-a",
                base_schema,
                "--source",
                "file",
            ],
        )

        assert (
            runner_result.exit_code == 0
        ), "Exited with code {}, expected zero".format(runner_result.exit_code)

        assert (
            output_directory_path.is_dir()
        ), "Output directory {} should exist".format(output_directory_path.absolute)
        with open(os.path.join(output_directory, "openapi.json"), "r") as oai:
            build_result = json.loads(oai.read())

            # Verify result
            assert_that(build_result, has_key("openapi"))

    assert runner_result.exit_code == 0
    assert len(runner_result.output) == 0


def test_version():
    expected_version = pkg_resources.require("meeshkan")[0].version

    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"cli, version {expected_version}\n"
