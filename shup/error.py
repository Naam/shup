import logging
import sys


def die(error, *args, **kwargs):
    logging.error(*args, **kwargs)
    sys.exit(error)
