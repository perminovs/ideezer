import logging
from tempfile import NamedTemporaryFile


logger = logging.getLogger(__name__)


def save(file):
    with NamedTemporaryFile(delete=False) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)

    process(path=tmp.name)


def process(path):
    logger.info('process file: %s', path)
    # ...
    # TODO delete file
