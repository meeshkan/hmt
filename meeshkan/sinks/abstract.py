import abc
from openapi_typed import OpenAPIObject
from typing import Union, Awaitable
from typing import Awaitable


class AbstractSink(abc.ABC):

    @abc.abstractmethod
    def push(self, schema: OpenAPIObject) -> Union[Awaitable[None], None]:
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
    def flush(self) -> Union[Awaitable[None], None]:
        raise NotImplementedError("Not implemented")
