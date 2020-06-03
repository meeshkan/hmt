from functools import reduce
from typing import Callable

from openapi_typed_2 import OpenAPIObject, PathItem

from hmt.serve.mock.matcher import get_path_item_with_method

def keep_method_if_required_request_body_is_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_request_body_is_present(p: PathItem) -> PathItem:
        out = (
            p
            if (operation_from_string(p, req.method.value) is None)
            or (
                len(
                    [
                        s
                        for s in get_required_request_body_schemas(req, oai, p)
                        if not valid_schema(
                            req.bodyAsJson
                            if req.bodyAsJson is not None
                            else json.loads(req.body)
                            if req.body is not None
                            else "",
                            {
                                # TODO: this line is different than the TS implementation
                                # because I think there is a logic bug there
                                # it should look like this line as we are not sure
                                # if the schema will be a reference or not
                                # perhaps I'm wrong in the assumption... only testing will tell...
                                # otherwise, change the TS implementation in unmock-js and delete this comment.
                                **convert_from_openapi(
                                    change_ref(s)
                                    if isinstance(s, Reference)
                                    else change_refs(s)
                                ),
                                "definitions": make_definitions_from_schema(oai),
                            },
                        )
                    ]
                )
                == 0
            )
            else omit_method_from_path_item(p, req.method.value)
        )
        return out

    return _keep_method_if_required_request_body_is_present

@timed
def keep_method_if_required_header_parameters_are_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_header_parameters_are_present(p: PathItem) -> PathItem:
        out = keep_method_if_required_query_or_header_parameters_are_present(
            True, req, oai, p
        )
        logger.info("Headers matched")
        return out

    return _keep_method_if_required_header_parameters_are_present

@timed
def keep_method_if_required_query_parameters_are_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_query_parameters_are_present(p: PathItem) -> PathItem:
        out = keep_method_if_required_query_or_header_parameters_are_present(
            False, req, oai, p
        )
        logger.info("Query matched")
        return out

    return _keep_method_if_required_query_parameters_are_present



def  _path_item_modifier(oai: OpenAPIObject) -> Callable[[PathItem], PathItem]:
    def __path_item_modifier(path_item: PathItem) -> PathItem:
        return reduce(
            lambda a, b: b(a),
            [
                # keep_method_if_required_header_parameters_are_present(req, oai),
                # keep_method_if_required_query_parameters_are_present(req, oai),
                ##### keep_method_if_required_request_body_is_present
                ##### should be uncommented in a separate PR
                ##### it breaks the logic in the new schemabuilder
                ##### but it should be reimplemented
                ##### now, the issue is that API requests will not
                ##### have their body validated
                ##### as there are so few API requests that require body
                ##### validation for mocking, this is a small loss
                ##### but should still be acknowledged and fixed when
                ##### someone has time
                # keep_method_if_required_request_body_is_present(req, oai),
            ],
            get_path_item_with_method(req.method.value, path_item),
        )

    return __path_item_modifier