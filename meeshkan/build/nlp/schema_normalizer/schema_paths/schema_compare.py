import json
import json
import sys


def exact_match(list1, list2):
    if list1 == list2:
        return True
    else:
        return False

def compare_nested_schema(list1, list2):
    match_list = list()
    for each1 in list1:
        for key1, value1 in each1:
            for each2 in list2:
                for key2, value2 in each2:
                    if value1 == value2:
                        match_list.append((key1, key2))
