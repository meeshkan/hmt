import os
import sys
import json

#sys.path.append('..')
from meeshkan.build.nlp.schema_normalizer.schema_paths.schema_reference import check_and_create_ref



openapi_filepath = '../openapi_specs/original.json'
openapi_relpath = os.path.relpath(openapi_filepath)
with open(openapi_relpath, 'r') as f:
    specs = json.load(f)

if not isinstance(specs, dict):
    raise TypeError('OpenApi file is not a valid object type')

path_tuple = ('/accounts/v3/accounts/eg9Mno2tvmeEE039chWrHw7sk1155oy5Mha8kQp0mYs.sxajtselenSScKPZrBMYjg.SoFWGrHocw1YoNb3zw-vfw',
              '/accounts/v3/accounts')

check_and_create_ref(specs, path_tuple)