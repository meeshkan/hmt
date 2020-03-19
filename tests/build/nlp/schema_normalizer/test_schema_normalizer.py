
# import os
# import sys
# import json
#
# from meeshkan.build.nlp.schema_normalizer.schema_normalizer.schema_paths.schema_reference import check_and_create_ref
#
# def test_schema_normalizer():
#     openapi_filepath = 'resources/openapi.json'
#     with open(openapi_filepath, 'r') as f:
#         specs = json.load(f)
#
#     if not isinstance(specs, dict):
#         raise TypeError('OpenApi file is not a valid object type')
#
#     path_tuple = ('/accounts/v3/accounts/eg9Mno2tvmeEE039chWrHw7sk1155oy5Mha8kQp0mYs.sxajtselenSScKPZrBMYjg.SoFWGrHocw1YoNb3zw-vfw',
#                   '/accounts/v3/accounts')
#
#     best_tuple = check_and_create_ref(specs, path_tuple)
#     assert "@schema" == best_tuple[0]
#     assert "accounts@array" == best_tuple[1]
