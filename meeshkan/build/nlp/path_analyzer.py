from enum import Enum
from typing import Optional

from dataclasses import dataclass
from entity_extractor import EntityExtractor
from gib_detect import id_classifier

@dataclass(frozen=True)
class PathItems:
    entity: Optional[str]
    action: Optional[str]
    id: Optional[str]
    group_id: Optional[str]


class PathAnalyzer:
    def __init__(self):
        self._entity_extractor = EntityExtractor()

    def extract_values(self, path): #path="/payemnts/35234"
        return PathItems(entity=self._entity_extractor.get_entity_from_url(path), id=id_classifier(path), action=None, group_id=None)
