from typing import Tuple
from openapi_typed_2 import OpenAPIObject, convert_to_openapi, convert_from_openapi
from openapi_typed_2 import OpenAPIObject, convert_to_openapi, convert_from_openapi
from meeshkan.build.nlp.schema_normalizer.schema_paths.schema_reference import check_and_create_ref


class EntityNormalizer:
    def __init__(self, ):
        self.path_tuple = (
        '/accounts/v3/accounts/eg9Mno2tvmeEE039chWrHw7sk1155oy5Mha8kQp0mYs.sxajtselenSScKPZrBMYjg.SoFWGrHocw1YoNb3zw-vfw',
        '/accounts/v3/accounts')

    def normalize(self, specs: OpenAPIObject, path_tuple: Tuple) -> OpenAPIObject:
        specs_dict = convert_from_openapi(specs)
        is_updated, updated_specs = check_and_create_ref(specs_dict, path_tuple)

        if is_updated:
            return convert_to_openapi(updated_specs)
        else:
            return specs