import sys
from .schemabuilder import build_schema_batch
import json
from http_types import RequestResponseBuilder
from .logger import get as getLogger
from yaml import dump
from typing import cast


logger = getLogger(__name__)


def log(*args):
    logger.debug(*args)


def main(iterator=iter(sys.stdin.readline, '')) -> str:
    """Read request-response dictionaries to build a schema.

    Keyword Arguments:
        iterator {iterator} -- Iterator (default: {iter(sys.stdin.readline, '')})

    Returns:
        str -- Schema as string
    """

    requests = []
    schema = {}
    for line in iterator:
        requests.append(RequestResponseBuilder.from_dict(
            json.loads(line)))
        new_schema = build_schema_batch(requests)
        if new_schema != schema:
            log("Updated schema:\n%s", dump(new_schema))
        schema = new_schema

    log("Result:\n%s", dump(schema))
    return cast(str, dump(schema))


if __name__ == '__main__':
    print(main())
