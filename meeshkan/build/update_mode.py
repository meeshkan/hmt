import enum


class UpdateMode(enum.Enum):
    GEN = 0
    REPLAY = 1
    MIXED = 2
    NLP = 3


__all__ = ["UpdateMode"]
