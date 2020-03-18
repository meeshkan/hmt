from typing import Any

from http_types import Request
from openapi_typed import OpenAPIObject, Reference
from openapi_typed_2 import convert_from_openapi

from meeshkan.serve.mock.matcher import change_ref, change_refs
from meeshkan.serve.mock.storage import Storage


class MeeshkanFakerBase:
    def __init__(self, request: Request, spec: OpenAPIObject, mock_storage: Storage, ):
        to_fake = {
            **convert_from_openapi(
                change_ref(schema)
                if isinstance(schema, Reference)
                else change_refs(schema)
            ),
            "definitions": {
                k: convert_from_openapi(
                    change_ref(v) if isinstance(v, Reference) else change_refs(v)
                )
                for k, v in (
                    spec.components.schemas.items()
                    if (name in match)
                       and (spec.components is not None)
                       and (spec.components.schemas is not None)
                    else []
                )
            },
        }

    def fake_it(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        raise NotImplementedError
