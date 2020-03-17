import os
import sys
import json

sys.path.append('..')
from schema_paths.schema_to_vector import generate_schema_vectors


methods = ['get', 'post']
openapi_filepath = '../openapi_specs/original.json'
openapi_relpath = os.path.relpath(openapi_filepath)
with open(openapi_relpath, 'r') as f:
    specs = json.load(f)

if not isinstance(specs, dict):
    raise TypeError('OpenApi file is not a valid object type')

all_paths = [path for path in specs['paths'].keys()]
all_paths_dict = {key : [] for key in all_paths}

for path in all_paths:

    for method in specs['paths'][path].keys():
        if method in methods:
            schema = specs['paths'][path][method]['responses']['200']['content']['application/json']['schema']
            all_paths_dict[path].append({method : schema})

schema = all_paths_dict[all_paths[2]][0]['get']
schema['$schema'] = 'root'
print(generate_schema_vectors(schema))