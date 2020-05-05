import enum
from dataclasses import dataclass, field
from typing import Sequence, Union

from openapi_typed_2 import Reference, Schema

####################################
#### does a diff on two schemas


class SM(enum.Enum):
    SEQUENCE = 0
    MAPPING = 1


@dataclass(frozen=True)
class SchemaDiff:
    differing_types: Sequence[Sequence[Union[str, SM]]] = field(default_factory=list)
    differing_keys: Sequence[Sequence[Union[str, SM]]] = field(default_factory=list)


def make_schema_diff(
    s0: Union[Schema, Reference],
    s1: Union[Schema, Reference],
    path: Sequence[Union[str, SM]] = [],
) -> SchemaDiff:
    if isinstance(s0, Schema) and isinstance(s1, Schema):
        if s0._type != s1._type:
            return SchemaDiff(differing_types=[path])
        elif s0._type == "object":
            props = [
                set(x.keys()) if x is not None else set([])
                for x in [s0.properties, s1.properties]
            ]
            kdiff = props[0].symmetric_difference(props[1])
            diffs = [
                make_schema_diff(s0.properties[p], s1.properties[p])
                for p in props[0].intersection(props[1])
            ]
            return SchemaDiff(
                differing_types=sum([x.differing_types for x in diffs], []),
                differing_keys=sum(
                    [x.differing_keys for x in diffs], [[x, *path] for x in kdiff]
                ),
            )
        elif s0._type == "array":
            if type(s0.items) != type(s1.items):
                return SchemaDiff(differing_types=[[SM.SEQUENCE, *path]])
            elif isinstance(s0.items, Schema) and isinstance(s1.items, Schema):
                return make_schema_diff(s0.items, s1.items, path=[SM.SEQUENCE, *path])
            else:
                # a tuple or some weird state we didn't predit
                # for now we give up as it is so rare,
                # but should inspect this in the future
                return SchemaDiff()
        return SchemaDiff()
    elif isinstance(s0, Reference) and isinstance(s1, Reference):
        return SchemaDiff(differing_types=[path] if s0._ref != s1._ref else [])
    else:
        return SchemaDiff(differing_types=[path])
