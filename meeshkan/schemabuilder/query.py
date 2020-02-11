"""Code for working with query parameters."""

from http_types import Query
from openapi_typed import Parameter, Reference, Schema
from typing import Sequence, Union, cast, Sequence, List
from genson import SchemaBuilder  # type: ignore

SchemaQuery = Sequence[Union[Parameter, Reference]]


def build_query(query: Query) -> SchemaQuery:
    """Build a list of query parameters from request query parameters.

    Arguments:
        query {Query} -- Key-value map of query parameters and values.

    Returns:
        SchemaQuery -- OpenAPI list of parameters.
    """
    return update_query(query, [], set_new_as_required=True)


def build_query_param(name: str, value: Union[str, Sequence[str]], required: bool) -> Parameter:
    """Build a new OpenAPI compatible query parameter definition from query parameter
    name and value.

    Arguments:
        name {str} -- Parameter name.
        value {Any} -- Query parameter value.
        required {bool} -- Whether the parameter should be marked as required.
    Returns:
        Parameter -- [description]
    """
    if isinstance(value, list) and len(value) == 1:
        query_value = value[0]
    else:
        query_value = value
    schema_builder = SchemaBuilder()
    schema_builder.add_object(query_value)
    schema = cast(Schema, schema_builder.to_schema())
    return Parameter(name=name, schema=schema, required=required, **{'in': 'query'})


def _update_required(param: Parameter, required: bool) -> Parameter:
    if param['required'] == required:
        return param

    params = dict(**param)
    params.pop('required')
    return Parameter(**params, required=required)


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

    missing_query_params = [
        _update_required(param, required=False) for param in query_params if param['name'] in missing_query_param_names]

    updated_query_params = new_query_params + shared_query_params + \
        missing_query_params + non_query_params

    return cast(SchemaQuery, updated_query_params)
