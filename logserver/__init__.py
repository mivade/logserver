import logging
from logging.handlers import DatagramHandler
from multiprocessing import Process, Event
from threading import Thread
import sys

if sys.version_info.major < 3:
    import SocketServer as socketserver
    import cPickle as pickle
    from Queue import Queue, Empty
else:
    import socketserver
    import pickle
    from queue import Queue, Empty


__version__ = "0.2.dev"


# Default format to use with StreamHandlers
_FORMAT = "[%(levelname)1.1s %(name)s:%(lineno)d %(asctime)s] %(message)s"


def run_server(handlers=[], host="127.0.0.1", port=9123, done=None, queue=None,
               level=logging.INFO):
    """Target for a thread or process to run a server to aggregate and record
    all log messages to disk.

    :param list handlers: List of log handlers to use. If not given, only a
        :class:`logging.NullHandler` will be used.
    :param str host: Host to bind to.
    :param int port: Port number to bind to.
    :param Event done: An event used to signal the process to stop.
    :param queue: A queue to use or None to create a new one.
    :param int level: Minimum log level.

    """
    if queue is None:
        queue = Queue()

    if done is None:
        done = Event()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if len(handlers) == 0:
        handlers.append(logging.NullHandler())

    for handler in handlers:
        handler.setLevel(level)
        root_logger.addHandler(handler)

    class Handler(socketserver.DatagramRequestHandler):
        def handle(self):
            try:
                # It is mostly undocumented, but there are 4 bytes which give
                # the length of the pickled LogRecord.
                _ = self.rfile.read(4)
                msg = self.rfile.read()
                queue.put(logging.makeLogRecord(pickle.loads(msg)))
            except:
                print("Error reading log record!")

    server = socketserver.ThreadingUDPServer((host, port), Handler)

    def consume():
        while not done.is_set():
            try:
                record = queue.get(timeout=1)
                root_logger.handle(record)
            except Empty:
                continue
        server.shutdown()

    consumer = Thread(target=consume, name="log_consumer")
    consumer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        done.set()


def make_server_process(*args, **kwargs):
    """Returns a :class:`Process` instance that calls :func:`run_server` when
    started. Paramters are the same as thos of :func:`run_server`

    """
    p = Process(target=run_server, args=args, name="logserver", kwargs=kwargs)
    return p


def get_logger(name, host="127.0.0.1", port=9123, level=logging.INFO,
               stream_handler=True, stream_fmt=_FORMAT):
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

    logger.addHandler(DatagramHandler(host, port))

    if stream_handler:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(stream_fmt))
        logger.addHandler(handler)

    return logger

create_logger = get_logger
