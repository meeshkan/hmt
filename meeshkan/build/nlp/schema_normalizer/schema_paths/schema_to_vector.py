"""
    This module is to analyze the jsonschema generated genson
    and convert it into feature vector
"""
_object = 'object'
_array = 'array'
_string = 'string'
_integer = 'integer'
_number = 'number'
_boolean = 'boolean'
_unknown = 'unknown'
no_properties = '_noProps_'

split_type = '@'
split_level = '#'
type_mapping = {
    _object : '1',
    _array : '2',
    _string : '3',
    _integer : '4',
    _number : '5',
    _boolean : '6',
    _unknown : '0',
}

reverse_type_mapping = {}
for (key, value) in type_mapping.items():
    reverse_type_mapping[value] = key


def get_type_mapping(value_type: str) -> int:
    num_mapping = type_mapping.get(value_type)
    if num_mapping is not None:
        return num_mapping
    else:
        return type_mapping['unknown']


def check_object(obj):
    return isinstance(obj, dict)

def properties_vector(obj):
    properties_vector = []
    if obj.get('type') == _array:
        if obj.get('items') is None:
            return properties_vector
        else:
            obj = obj['items']
    if obj.get('properties') is not None:
        for (key, value) in obj['properties'].items():
            if check_object(value):
                properties_vector.append(f"{key}{split_type}{value.get('type')}")
            else:
                raise TypeError(f"The value of key '{key}'is not an object type")
    else:
        properties_vector.append(f"{no_properties}{split_type}{obj.get('type')}")
    return properties_vector


def split_parent_structure(parent_name):
    type_items = []
    if parent_name is not None:
        level_items = parent_name.split(split_level)
        if isinstance(level_items, list):
            type_items = [item.split(split_type) for item in level_items]
        else:
            raise ValueError('split function is unable to convert into a list')
    return type_items


def create_object_structure(parent_name):
    type_items = split_parent_structure(parent_name)
    structure_list = []
    for level in type_items:
        if isinstance(level, list) and len(level) == 2:
            if level[1] == _array:
                structure_list += ['properties', level[0], 'items']
            elif level[1] == _object:
                structure_list += ['properties', level[0]]
        else:
            raise ValueError("The level of schema type is not correct ")
    if type_items[-1][-1] == _array and structure_list[-1] == 'items':
        return structure_list[:-1]
    return structure_list



def generate_new_object(obj, structure_list, len_of_list):
    if len_of_list == 0:
        return obj
    else:
        return generate_new_object(obj[structure_list[-len_of_list]], structure_list, len_of_list - 1)


def generate_nested_object(obj, parent_path):
    if not isinstance(obj, dict):
        raise TypeError('The object is not a type dict')

    structure_list = create_object_structure(parent_path)
    if len(structure_list) < 2:
        raise ValueError('The parent path is not correct')
    len_of_list = len(structure_list)
    new_obj = generate_new_object(obj, structure_list, len_of_list)
    # To check if the new object is of type array then we need to nest inside 'items'
    if new_obj['type'] == _array:
        if new_obj.get('items') is not None:
            return new_obj['items']
    return new_obj



def generate_child_vectors(obj, parent=None):
    if check_object(obj):
        if parent is None:
            if obj.get('$schema') is not None:
                if obj.get('properties') is None:
                    return []
                child_vector = properties_vector(obj)
                return child_vector
            else:
                raise KeyError("Only root schema can have no parent")
        else:
            structure_list = create_object_structure(parent)
            if len(structure_list) < 2:
                raise ValueError("The generated stucture is not correct")
            len_of_list = len(structure_list)
            new_obj = generate_new_object(obj, structure_list, len_of_list)
            child_vector = properties_vector(new_obj)
            child_vector = [f"{parent}{split_level}{child}" for child in child_vector]
            return child_vector


def generate_schema_vectors(obj, vectors=None, tagged_vectors=None):
    if vectors is None:
        vectors = generate_child_vectors(obj)
        if vectors is None:
            raise Exception("There is no property in the base schema")
    if tagged_vectors is None:
        temp_vectors = vectors
    else:
        temp_vectors = tagged_vectors
    temp2 = []
    for c_vector in temp_vectors:
        if c_vector.split(split_type)[-1] in (_array, _object):
            temp2.append(c_vector)
    if len(temp2) != 0:
        tagged_vectors = []
        for item in temp2:
            #print(item) #Good for debug
            tagged_vectors += generate_child_vectors(obj, item)
        vectors += tagged_vectors
        return generate_schema_vectors(obj, vectors, tagged_vectors)
    else:
        return vectors
