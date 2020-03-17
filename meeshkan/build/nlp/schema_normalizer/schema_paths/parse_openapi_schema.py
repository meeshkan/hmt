import sys

sys.path.append('..')
from schema_paths.schema_to_vector import generate_schema_vectors
from schema_paths.schema_to_vector import split_type, split_level
from schema_paths.schema_to_vector import _object, _array, _string, _integer, _number, _boolean, _unknown

from schema_paths.schema_to_fields import schema_remove_types

def create_schema_levels(obj):
    # obj is list object
    schema_levels_dict = dict()
    obj = [feature.split(split_level) for feature in obj]
    for feature in obj:
        length = str(len(feature))
        feature = '#'.join(feature)
        if schema_levels_dict.get(length) is None:
            schema_levels_dict[length] = [feature]
        else:
            schema_levels_dict[length] += [feature]
    
    total_keys = len(schema_levels_dict)
    level_keys = dict()
    for i in range(1, total_keys, 1):
        for each in schema_levels_dict[str(i)]:
            if each.endswith(_array) or each.endswith(_object):
                if level_keys.get(str(i + 1)) is None:
                    level_keys[str(i + 1)] = [each]
                else:
                    level_keys[str(i + 1)] += [each]


    for each in range(total_keys, 1, -1):
        schema_levels_dict[str(each - 1)] += schema_levels_dict[str(each)]

    schema_nested_levels = []
    for i in range(1, total_keys + 1, 1):
        if i == 1:
            schema_nested_levels.append({ '$schema' : schema_levels_dict[str(i)]})
        else:
            temp = dict()
            for keys in level_keys[str(i)]:
                temp[keys] = []
                for value in schema_levels_dict[str(i)]:
                    if value.startswith(keys):
                        value = value.replace(keys, '')[1:]
                        temp[keys] += [value]
            schema_nested_levels.append(temp)

    for levels in schema_nested_levels:
        for keys in levels:
            arr1 = [schema_remove_types(value) for value in levels[keys]]
            levels[keys] = sorted(arr1)
    
    return schema_nested_levels


    

def parse_schema(obj):
    if not isinstance(obj, dict):
        raise TypeError('The input object passed is not a type dict')

    obj['$schema'] = 'root'
    root_features = generate_schema_vectors(obj)
    return create_schema_levels(root_features)

