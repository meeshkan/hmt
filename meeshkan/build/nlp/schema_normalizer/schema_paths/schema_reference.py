#import sys
#sys.path.append('..')
from meeshkan.build.nlp.schema_normalizer.schema_paths.parse_openapi_schema import parse_schema
from meeshkan.build.nlp.schema_normalizer.schema_paths.schema_compare import compare_nested_schema
from meeshkan.build.nlp.schema_normalizer.schema_paths.schema_to_vector import generate_nested_object, create_object_structure



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
                                    
    if isinstance(best_tuple, list) and len(best_tuple) > 0:
        ref_component = create_ref_path(best_tuple[0])
        ref_component_obj = create_ref_obj(all_paths_dict, path_tuple, best_tuple[0], ref_component[0])
        ref_replaced_dict = create_replaced_ref(all_paths_dict, path_tuple, best_tuple[0], ref_component[1])
        if len(ref_replaced_dict) != 2:
            return (False, specs)
        # Now update the original specs by replacing the ref components
        for path in path_tuple:
            for method in all_paths_dict[path][0].keys(): # this will run just once
                specs['paths'][path][method]['responses']['200']['content']['application/json']['schema'] = \
                    ref_replaced_dict[path]
        # Now lastly we add the component schema under specs
        specs.update(ref_component_obj)
        return (True, specs)
    else:
        return (False, specs)

        
def create_replaced_ref(all_paths_dict, path_tuple, tuple1, component_path):

    schemas_list = list()
    for paths in path_tuple:
        for schema in all_paths_dict[paths][0].values():
            schemas_list.append(schema)
    
    ref_replaced_dict = dict()
    for index, schema in enumerate(schemas_list):
        if tuple1[index] == '$schema':
            ref_replaced_dict[path_tuple[index]] = {'$ref' : component_path}
        else:
            schema_copy = schema.copy()
            ref_schema = generate_replaced_ref(schema_copy, tuple1[index], component_path)
            if ref_schema.get('$schema') is not None:
                del ref_schema['$schema']
            ref_replaced_dict[path_tuple[index]] = ref_schema
    return ref_replaced_dict
            
            


def generate_replaced_ref(schema, parent_name, component_path):
    structure_list = create_object_structure(parent_name)
    len_of_structure = len(structure_list)
    if len_of_structure < 2:
        raise ValueError('The parent property may be not correct')
    last_index = len_of_structure - 1
    check_and_replace(schema, structure_list, last_index, component_path, 0)
    return schema


def check_and_replace(schema, structure_list, last_index, component_path, index = 0):
    for key, value in schema.items():
        if isinstance(value, dict) and key == structure_list[index]:
            if index != last_index:
                check_and_replace(value, structure_list, last_index, component_path, index + 1)
            elif key == structure_list[index]:
                if schema[key]['type'] == '_array' and schema[key].get('items') is not None:
                    schema[key]['items'] = {'$ref' : component_path}
                else:
                    schema[key] = {'$ref' : component_path}




def create_ref_obj(all_paths_dict, path_tuple, tuple1, component_name):
    # Now we are going to make reference to the same matched nested structure so 
    # for convenience let us just refer to the first element of the path tuple

    ref_index = 1
    # Te beow loop will run only once.
    for method, schema in all_paths_dict[path_tuple[ref_index]][0].items():
        root_property = tuple1[ref_index]
        if root_property == '$schema':
            return generate_component_dict(schema, component_name)
        else:
            nested_schema = generate_nested_object(schema, root_property)
            return generate_component_dict(nested_schema, component_name)
        
            
        


def generate_component_dict(schema, component_name):
    obj_list = [component_name, 'schema', 'components']
    obj_dict = schema
    for item in obj_list:
        obj_dict = {item : obj_dict}
    return obj_dict



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