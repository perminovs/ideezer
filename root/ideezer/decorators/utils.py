import logging
import inspect
from datetime import datetime
from functools import wraps


logger = logging.getLogger(__name__)


def timeit(arg):
    """ Usage:

    With specify logger:

    >>> custom_logger = logging.getLogger('some_logger_name')
    >>> @timeit(custom_logger)
    >>> def func():
    >>>     ...

    or with default logger:

    >>> @timeit
    >>> def func():
    >>>     ...
    """
    if inspect.isfunction(arg):
        return _timeit(custom_logger=logger)(func=arg)

    return _timeit(custom_logger=arg)


def _timeit(custom_logger=None):
    def _deco(func):  # TODO customize disable option
        @wraps(func)
        def _inner(*args, **kwargs):
            start = datetime.now()
            res = func(*args, **kwargs)
            custom_logger.info('%s: %s', func.__name__, datetime.now() - start)
            return res
        return _inner
    return _deco
