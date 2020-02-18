"""Code for working with parameters."""

from functools import reduce
from meeshkan.schemabuilder.json_schema import to_const
from meeshkan.schemabuilder.update_mode import UpdateMode
from openapi_typed import Parameter, Reference, Schema
from typing import Sequence, Union, cast, Sequence, List, Mapping
from genson import SchemaBuilder  # type: ignore

SchemaParameters = Sequence[Union[Parameter, Reference]]

# TODO: this won't work for anything other than simple schema
# maybe make more robust?
def unnest(d: List[Schema]) -> List[Schema]:
    return cast(List[Schema], reduce(lambda a, b: [*a, *b],
        [[x] if 'oneOf' not in x else unnest(cast(List[Schema], x['oneOf'])) for x in d
    ], []))
    

# TODO: extended this for all paramaters, but need to verify that
# there is not some subtle difference between query and header

class ParamBuilder:
    def __init__(self, _in: str):
        if _in not in ['header', 'query']:
            raise ValueError('A parameter cannot have an `in` value of %s.' % _in)
        self._in = _in

    def build(self, params: Mapping[str, Union[str, Sequence[str]]], mode: UpdateMode) -> SchemaParameters:
        """Build a list of parameters from request parameters.

        Arguments:
            params {Mapping[str, str]} -- Key-value map of params parameters and values.

        Returns:
            SchemaParameters -- OpenAPI list of parameters.
        """
        existing = []
        # as a defualt, we set nothing new to required
        # can change later if there is a compelling reason
        return self.update(params, mode, existing, set_new_as_required=False)


    def build_param(self, name: str, value: Union[str, Sequence[str]], required: bool, mode: UpdateMode) -> Parameter:
        """Build a new OpenAPI compatible parameter definition from parameter
        name and value.

        Arguments:
            name {str} -- Parameter name.
            value {Any} -- Parameter value.
            required {bool} -- Whether the parameter should be marked as required.
        Returns:
            Parameter -- [description]
        """
        # TODO: this may not be accurate if there are duplicate parameters
        # which is allowed in http
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        else:
            value = value
        out = {}
        if (mode == UpdateMode.GEN):
            schema_builder = SchemaBuilder()
            schema_builder.add_object(value)
            out = schema_builder.to_schema()
        else:
            out = { 'oneOf': [to_const(value)]}
        schema = cast(Schema, out)
        return Parameter(name=name, schema=schema, required=required, **{'in': self._in})


    def _update_required(self, param: Parameter, required: bool) -> Parameter:
        if param['required'] == required:
            return param

        params = dict(**param)
        params.pop('required')
        return Parameter(**params, required=required)


    # TODO Fix types once openapi types are covariant
    def update(self, incoming_params: Mapping[str, Union[str, Sequence[str]]], mode: UpdateMode, existing: SchemaParameters, set_new_as_required=False) -> SchemaParameters:
        non_params: List[Parameter] = [
            param for param in existing if param['in'] != self._in]  # type: ignore

        params: List[Parameter] = [
            param for param in existing if param['in'] == self._in]  # type: ignore

        schema_params_names = frozenset(
            [param['name'] for param in params])

        request_param_names = frozenset(incoming_params.keys())

        # Parameters in request but not in schema
        new_param_names = request_param_names.difference(
            schema_params_names)

        # Parameters in schema but not in request
        missing_param_names = schema_params_names.difference(
            request_param_names)

        # Parameters in schema and in request
        shared_param_names = request_param_names.intersection(
            schema_params_names)

        new_params = [self.build_param(name=param_name,
                                            value=value,
                                            required=set_new_as_required,
                                            mode=mode)
                            for param_name in new_param_names
                            for value in (incoming_params[param_name],)]

        # TODO Update shared incoming_params parameter schema
        shared_params = [
            param if (mode == UpdateMode.GEN) else {
                # use constants
                **param,
                'schema': {'oneOf': unnest([param['schema'], to_const(incoming_params[param['name']])])}
            } for param in params if param['name'] in shared_param_names]

        missing_params = [
            self._update_required(param, required=False) for param in params if param['name'] in missing_param_names]

        # TODO: make sure cast is valid
        updated_params = [
            *new_params,
            *shared_params,
            *missing_params,
            *non_params
        ]
        return cast(SchemaParameters, updated_params)
