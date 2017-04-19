from __future__ import print_function

import sys
import logging
import logging.handlers
from logging.handlers import DatagramHandler
from multiprocessing import Process, Event
from threading import Thread
import warnings

if sys.version_info.major < 3:
    import SocketServer as socketserver
    import cPickle as pickle
    from Queue import Queue, Empty
else:
    import socketserver
    import pickle
    from queue import Queue, Empty


__version__ = "0.3.dev0"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9123

# Default format to use with StreamHandlers
_FORMAT = "[%(levelname)1.1s %(name)s:%(lineno)d %(asctime)s] %(message)s"


def run_server(handlers=[], host=DEFAULT_HOST, port=DEFAULT_PORT, done=None,
               ready=None, pipe=None, level=logging.INFO):
    """Target for a thread or process to run a server to aggregate and record
    all log messages to disk.

    Log handlers can be added on the fly by passing the `pipe` keyword argument.
    Since instances of log handlers are not picklable, it is therefore necessary
    to send a tuple of the following form to add a new handler::

        (name, HandlerClass, args, kwargs)

    where ``name`` is a name to give the handler (so it can later be removed),
    ``HandlerClass`` is a log handler class found in the `logging` or
    `logging.handlers` modules, and ``args`` and ``kwargs`` are those
    required for instantiating the handler class. To remove the handler, simply
    send a length-1 tuple ``(name,)``.

    :param list handlers: List of log handlers to use. If not given, only a
        :class:`logging.NullHandler` will be used.
    :param str host: Host to bind to.
    :param int port: Port number to bind to.
    :param Event done: An event used to signal the process to stop.
    :param Event ready: Event used to communicate that the server is ready.
    :param multiprocessing.Connection pipe: Use to instruct the server to add or
        remove log handlers on the fly.
    :param int level: Minimum log level.

    """
    queue = Queue()

    if done is None:
        done = Event()

    if ready is None:
        ready = Event()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Add permanent handlers
    if len(handlers) == 0:
        handlers.append(logging.NullHandler())
    for handler in handlers:
        handler.setLevel(level)
        root_logger.addHandler(handler)

    # Stores handlers to be added or removed later
    runtime_handlers = dict()

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
        """Log record consumer thread."""
        while not done.is_set():
            try:
                record = queue.get(timeout=1)
                root_logger.handle(record)
            except Empty:
                continue

        # Finish processing any items left in the queue before quitting
        while True:
            try:
                record = queue.get_nowait()
                root_logger.handle(record)
            except Empty:
                break

        server.shutdown()

    def modify_handlers(pipe):
        """Thread target to listen for handlers to add/remove."""
        while not done.is_set():
            if not pipe.poll(1):
                continue

            try:
                msg = pipe.recv()
                if not isinstance(msg, (tuple, list)):
                    print("Invalid message encountered")
                    continue
                if len(msg) not in (1, 4):
                    print("Invalid message length")
                    continue
            except EOFError:
                continue

            name = msg[0]

            try:
                # User wants to remove a handler
                handler = runtime_handlers.pop(name)
                root_logger.removeHandler(handler)
            except KeyError:
                # User wants to add a handler
                if len(msg) != 4:
                    print("Need a tuple of length 4 to create a new handler: "
                          "(name, HandlerClass, args, kwargs)")
                    continue

                # Get handler class from logging or logging.handlers
                try:
                    handler_class = getattr(logging, msg[1])
                except AttributeError:
                    if not hasattr(logging.handlers, msg[1]):
                        print(msg[1], "not in logging or logging.handlers")
                        continue
                    else:
                        handler_class = getattr(logging.handlers, msg[1])

                # Try to instantiate the logger and add it
                try:
                    handler = handler_class(*msg[2], **msg[3])
                    root_logger.addHandler(handler)
                except Exception as e:
                    print("Error instantiating handler:", str(e))
                    continue

    consumer = Thread(target=consume, name="log_consumer")
    consumer.start()

    if len(runtime_handlers) != 0:
        modifier = Thread(target=modify_handlers, name="handler_modifier")
        modifier.start()

    ready.set()

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


def make_server_thread(*args, **kwargs):
    """Identical to :func:`make_server_process` only returns a :class:`Thread`
    instance instead.

    """
    t = Thread(target=run_server, args=args, name="logserver", kwargs=kwargs)
    return t


def get_logger(name, host=DEFAULT_HOST, port=DEFAULT_PORT, level=logging.INFO,
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


def create_logger(*args, **kwargs):
    warnings.warn("Using logserver.create_logger is deprecated. "
                  "Please use logserver.get_logger instead.",
                  DeprecationWarning)
    return get_logger(*args, **kwargs)
