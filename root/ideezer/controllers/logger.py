import logging
from functools import partial

from django.conf import settings


__true_logger = logging.getLogger(__name__)


def log(msg, request, level):
    """ Define session from `request` and write `msg` to log with `level`
    """
    session_name = __define_session(request)
    __log(msg, session_name, level)


def __define_session(request):
    """ Extract session_name from request

    :return: `session_name` or None
    """
    try:
        return request.COOKIES.get(settings.SESSION_COOKIE_NAME, 'unauth user')
    except Exception as e:
        __true_logger.error('cannot define session_name: {}'.format(e))


def __log(msg, session_name, level):
    """ Write message to log directly
    """
    msg = '{}: {}'.format(session_name, msg) if session_name else msg
    __true_logger.log(level=level, msg=msg)


# loggers with session_name
debug = partial(log, level=logging.DEBUG)
info = partial(log, level=logging.INFO)
warning = partial(log, level=logging.WARNING)
error = partial(log, level=logging.ERROR)

# loggers without session_name (anonymous - "anms")
anms_debug = partial(__log, session_name='unknown', level=logging.DEBUG)
anms_info = partial(__log, session_name='unknown', level=logging.INFO)
anms_warning = partial(__log, session_name='unknown', level=logging.WARNING)
anms_error = partial(__log, session_name='unknown', level=logging.ERROR)
