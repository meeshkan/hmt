"""Code for working with query parameters."""

from http_types import Query
from openapi_typed import Parameter, Reference
from typing import List, Union

SchemaQuery = List[Union[Parameter, Reference]]


def build_query(query: Query) -> SchemaQuery:
    return update_query(query, [])


def update_query(query: Query, existing_query: SchemaQuery) -> SchemaQuery:

    return []
