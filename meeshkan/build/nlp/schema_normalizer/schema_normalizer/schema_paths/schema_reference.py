import sys

from meeshkan.build.nlp.schema_normalizer.schema_paths.parse_openapi_schema import parse_schema
from meeshkan.build.nlp.schema_normalizer.schema_paths.schema_compare import compare_nested_schema

sys.path.append('..')


def check_and_create_ref(specs, path_tuple):
    all_paths_dict = {key : [] for key in path_tuple}
    nested_paths_dict = all_paths_dict.copy()
    methods = ['get', 'post']
    
    for path in path_tuple:
        for method in specs['paths'][path].keys():
            if method in methods:
                schema = specs['paths'][path][method]['responses']['200']['content']['application/json']['schema']
                all_paths_dict[path].append({method : schema})
                break  # To ensure that only single method is picked for any endpoint
    
    # Now lets us get the nested structure for schema
    for keys, values in all_paths_dict.items():
        for method in values[0].keys():
            nested_paths_dict[keys] = parse_schema(values[0][method])
    
    # Now we need to compare the two schemas for best refernce
    best_tuple = compare_nested_schema(nested_paths_dict[path_tuple[0]], nested_paths_dict[path_tuple[1]])
                                    
    return best_tuple
    
    



def create_ref_path(tuple1):
    schema_name = None
    schema_comp = '#/components/schema/'
    for item in tuple1:
        if item != '$schema':
            item = item.split('#')
            for levels in item:
                schema_name = levels.split('@')[0]
    

    if schema_name is None:
        return ('schema1' ,schema_comp + 'schema1')
    else:
        return (schema_name, schema_comp + schema_name)