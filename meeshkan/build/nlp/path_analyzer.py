from enum import Enum
from typing import Optional

from dataclasses import dataclass


@dataclass(frozen=True)
class PathItems:
    entity: Optional[str]
    action: Optional[str]
    id: Optional[str]
    group_id: Optional[str]


class PathAnalyzer:
    def __init__(self):
        pass

    def extract_values(self, path): #path="/payemnts/35234"
        return PathItems(entity="payment", action="confirm",
                id=None, group_id=None)