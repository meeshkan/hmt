import abc
from typing import Awaitable, Union

from hmt.build.result import BuildResult


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
