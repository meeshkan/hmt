import abc
from meeshkan.schemabuilder.result import BuildResult
from openapi_typed_2 import OpenAPIObject
from typing import Union, Awaitable
from typing import Awaitable


class AbstractSink(abc.ABC):
    """Abstract sink for build results.
    """

    @abc.abstractmethod
    def push(self, result: BuildResult) -> Union[Awaitable[None], None]:
        """Push build result to the sink.

        Arguments:
            result {BuildResult} -- Build result object.

        Returns:
            Union[Awaitable[None], None] -- Awaitable or None.
        """
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
    def flush(self) -> Union[Awaitable[None], None]:
        """Flush the build results.

        Returns:
            Union[Awaitable[None], None] -- Awaitable or None
        """
        raise NotImplementedError("Not implemented")
