import typing
from abc import ABC, abstractmethod
from typing import Any

from http_types import Request

from hmt.serve.mock.specs import OpenAPISpecification


class FakerBase(ABC):
    """
    An abstract interface for a class that produces faked API responses.
    """

    @abstractmethod
    def process(
        self,
        pathname: str,
        spec: typing.Optional[OpenAPISpecification],
        request: Request,
    ) -> Any:
        """
        Produces a fake response according to a spec and a request.
        May produce side effects, i.e. modify internal states according to specific requests.
        Returned data depends on a MIME Type defined in a spec.
        :param spec:
        :param request:
        """
        pass
