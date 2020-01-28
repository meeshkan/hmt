"""Code for working with query parameters."""

from http_types import Query
from openapi_typed import Parameter, Reference, Schema
from typing import List, Union, cast, Any
import genson

SchemaQuery = List[Union[Parameter, Reference]]


def build_query(query: Query) -> SchemaQuery:
    return update_query(query, [], set_new_as_required=True)


def build_query_param(name: str, value: Any, required: bool) -> Parameter:
    """New query parameters are required by default.

    Arguments:
        name {str} -- [description]
        value {Any} -- [description]

    Returns:
        Parameter -- [description]
    """
    if isinstance(value, list) and len(value) == 1:
        query_value = value[0]
    else:
        query_value = value
    schema_builder = genson.SchemaBuilder()
    schema_builder.add_object(query_value)
    schema = cast(Schema, schema_builder.to_schema())
    return Parameter(name=name, schema=schema, required=True, **{'in': 'query'})


# TODO Fix types once openapi types are covariant
def update_query(query: Query, existing_query: SchemaQuery, set_new_as_required=False) -> SchemaQuery:

    non_query_params: List[Parameter] = [
        param for param in existing_query if param['in'] != "query"]  # type: ignore

    query_params: List[Parameter] = [
        param for param in existing_query if param['in'] == "query"]  # type: ignore

    schema_query_params_names = frozenset(
        [param['name'] for param in query_params])

    request_query_param_names = frozenset(query.keys())

    # Parameters in request but not in schema
    new_query_param_names = request_query_param_names.difference(
        schema_query_params_names)

    # Parameters in schema but not in request
    missing_query_param_names = schema_query_params_names.difference(
        request_query_param_names)

    # Parameters in schema and in request
    shared_query_param_names = request_query_param_names.intersection(
        schema_query_params_names)

    new_query_params = [build_query_param(name=query_param_name,
                                          value=query_value,
                                          required=set_new_as_required)
                        for query_param_name in new_query_param_names
                        for query_value in (query[query_param_name],)]

    # TODO Update shared query parameter schema
    shared_query_params = [
        param for param in query_params if param['name'] in shared_query_param_names]

    # TODO Update missing query parameters to be optional
    missing_query_params = [
        param for param in query_params if param['name'] in missing_query_param_names]

    updated_query_params = new_query_params + shared_query_params + \
        missing_query_params + non_query_params

    return cast(SchemaQuery, updated_query_params)
