from enum import Enum
from typing import Optional
import re

from dataclasses import dataclass
from entity_extractor import EntityExtractor
from gib_detect import IdClassifier

@dataclass(frozen=True)
class PathItems:
    entity: Optional[str]
    action: Optional[str]
    id: Optional[str]
    group_id: Optional[str]


class PathAnalyzer:
    def __init__(self):
        self._entity_extractor = EntityExtractor()
        self._id_classifier = IdClassifier()

    def extract_values(self, path):
        path_list=path.split('/')[1:]
        nopunc_string=[]
        for i in path_list:
            if len(re.findall('[0-9]+', i))!=0 :
                 nopunc_string.append(i)
            else:
                 i = re.sub('[^0-9a-z]+', ' ', i.lower())
                 for word in i.split(" "):
                     nopunc_string.append(word)
        pos= {value:index for index,value in enumerate(nopunc_string)}
        maybe_entity = self._entity_extractor._split_pathes(path_list)[-1]
        maybe_id = self._id_classifier.id_classifier(path_list)
       # print(type(maybe_id))
        if maybe_id is not None:
            if pos[maybe_id]==pos[maybe_entity]+1:
                    return PathItems(entity=self._entity_extractor.get_entity_from_url(path_list), id=maybe_id, action=None, group_id=None)
            else:
                    return PathItems(entity=self._entity_extractor.get_entity_from_url(path_list), id=None, action=None, group_id=None)
        else:
             return PathItems(entity=self._entity_extractor.get_entity_from_url(path_list), id=None, action=None, group_id=None)
 #       return PathItems(entity=self._entity_extractor.get_entity_from_url(path_list), id=id_classifier(path_list), action=None, group_id=None)
