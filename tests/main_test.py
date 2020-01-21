from meeshkan.__main__ import cli
from click.testing import CliRunner
from .util import read_requests
import yaml
from hamcrest import assert_that, has_key

requests = read_requests()


def test_cli_build():
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('input.jsonl', 'w') as f:
            for request in requests:
                f.write(request)

        result = runner.invoke(
            cli, ['build', '-i', 'input.jsonl', '-o', 'output.yaml'])

        # Smoke test output
        with open('output.yaml', 'rb') as f:
            as_yaml = yaml.safe_load(f)
            assert_that(as_yaml, has_key("openapi"))

    assert result.exit_code == 0
    assert len(result.output) == 0
