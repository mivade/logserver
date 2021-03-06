"""A simple server for central log processing from multiple threads or
processes.

"""

import logging
import multiprocessing
import warnings

from .server import LogServer, LogServerProcess, LogServerThread
from ._constants import DEFAULT_FORMAT

__version__ = "0.3.1"


def run_server(handlers=[], host=None, port=None, level=logging.INFO,
               done=None, ready=None):
    """Creates a new :class:`LogServer` and starts it. This is intended as a
    target function for a thread or process and is included for backwards
    compatibility. For more flexibility, it is recommended to use
    :class:`LogServerThread` or :class:`LogServerProcess` directly.

    :param list handlers: List of log handlers to use on the server.
    :param str host: Host to bind socket to.
    :param int port: Port number to bind socket to.
    :param int level: Log level threshold.
    :param done: :class:`threading.Event` or :class:`multiprocessing.Event` to
        signal the server to stop.
    :param ready: :class:`threading.Event` or :class:`multiprocessing.Event` to
        indicate to the parent process that the server is ready.

    """
    server = LogServer(handlers, host, port, level)

    # Setting this to use the multiprocessing versions for most flexibility.
    server.done = done if done is not None else multiprocessing.Event()
    server.ready = ready if ready is not None else multiprocessing.Event()

    server.run()


def get_logger(name, host="127.0.0.1", port=9123, level=logging.INFO,
               stream_handler=True, stream_fmt=None):
    """Get or create a logger and setup appropriately. For loggers
    running outside of the main process, this must be called after the
    process has been started (i.e., in the :func:`run` method of a
    :class:`multiprocessing.Process` instance).

    :param str name: Name of the logger.
    :param str host: Host address.
    :param int port: Port.
    :param int level: Minimum log level.
    :param bool stream_handler: Add a :class:`logging.StreamHandler` to the
        logger.
    :param stream_fmt: Format to use when ``stream_handler`` is set.

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if len(logger.handlers) > 0:
        return logger  # logger already configured

    logger.addHandler(logging.handlers.DatagramHandler(host, port))

    if stream_handler:
        if stream_fmt is None:
            stream_fmt = DEFAULT_FORMAT
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(stream_fmt))
        logger.addHandler(handler)

    return logger


def create_logger(*args, **kwargs):
    warnings.warn("Using logserver.create_logger is deprecated. "
                  "Please use logserver.get_logger instead.",
                  DeprecationWarning)
    return get_logger(*args, **kwargs)
