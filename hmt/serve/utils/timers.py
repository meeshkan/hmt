import datetime
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def timed(func):
    @wraps(func)
    def function_wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        # logger.info("{} call".format(func.__name__))

        res = func(*args, **kwargs)
        logger.info(
            "{} call time {}".format(
                func.__name__, (datetime.datetime.now() - start).total_seconds()
            )
        )
        return res

    return function_wrapper
