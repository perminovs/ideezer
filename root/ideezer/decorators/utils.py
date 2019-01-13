import logging
from datetime import datetime


logger = logging.getLogger(__name__)


def timeit(func):  # TODO customize disable option
    def _inner(*args, **kwargs):
        start = datetime.now()
        res = func(*args, **kwargs)
        logger.info('%s: %s', func.__name__, datetime.now() - start)
        return res
    return _inner
