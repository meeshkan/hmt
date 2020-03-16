from enum import Enum


class PathItemTypes(Enum):
    ENTITY=0
    ACTION=1
    ID=2
    GROUP_ID=3#page numbers or something


class PathAnalyzer:
    def __init__(self):
        pass

    def extract_values(self, path):
        return {PathItemTypes.ENTITY: "payment", PathItemTypes.ACTION: "confirm",
                PathItemTypes.ID: None, PathItemTypes.GROUP_ID: None}