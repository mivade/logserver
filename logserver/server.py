import sys
import threading as th
import multiprocessing as mp
import logging
import logging.handlers
from socket import socket, AF_INET, SOCK_DGRAM
from select import select

if sys.version_info.major >= 3:
    import queue
    import pickle
else:
    import Queue as queue
    import cPickle as pickle

from . import handlers

try:
    from typing import Union
except ImportError:
    Union = None


class LogServer(object):
    """Base server for logging from multiple processes or threads."""
    def __init__(self, handlers, host, port, pipe=None, level=logging.INFO):
        self.host = host or "localhost"
        self.port = port or 9123

        self.handlers = handlers
        self.runtime_handlers = dict()
        self.level = level

        # Events are instantiated by implementations so we can choose from
        # either threaded or multiprocess varieties
        self.done = None  # type: Union[mp.Event, th.Event]
        self.ready = None  # type: Union[mp.Event, th.Event]

        self.pipe = pipe

        self._record_queue = queue.Queue()
        self._handler_queue = queue.Queue()

        self._runtime_handlers = {}

    def add_handler(self, name, handler_class, *args, **kwargs):
        """Add a new handler to the root logger.

        .. warning::

           This will replace an existing handler of the given name. It is up to
           the main process starting a log server to keep track of named
           handlers.

        :param str name: Unique name to give the handler.
        :param str handler_class: :class:`logging.Handler` class to use; must
            be found in either :mod:`logging`, :mod:`logging.handlers`, or
            :mod:`logserver.handlers`.
        :param list args: Arguments used to instantiate the handler.
        :param dict kwargs: Keyword arguments used to instantiate the handler.
        :returns: A copy of the instantiated handler.

        """
        Handler = self.get_handler_class(handler_class)
        if not issubclass(Handler, logging.Handler):
            raise TypeError(handler_class + " is not a logging.Handler")

        try:
            handler = Handler(*args, **kwargs)
            self._handler_queue.put((name, handler_class, args, kwargs))
            return handler
        except Exception as e:
            print("Unable to create handler")
            print(e)

    def remove_handler(self, name):
        """Remove a handler from the root logger.

        :param str name: Name given to the handler.

        """
        self._handler_queue.put((name,))

    @staticmethod
    def get_handler_class(name):
        """Returns the class of a handler found in the Python standard library
        or :mod:`logserver.handlers`.

        """
        if hasattr(handlers, name):
            mod = handlers
        elif hasattr(logging, name):
            mod = logging
        elif hasattr(logging.handlers, name):
            mod = logging.handlers
        else:
            raise RuntimeError("handler class not found")
        return getattr(mod, name)

    def get_logger(self, name, stream_handler=True, stream_fmt=None):
        """Return a pre-configured logger that will communicate with the log
        server. If the logger already exists, it will be returned unmodified.

        :param str name: Name of the logger.
        :param bool stream_handler: Automatically add a stream handler.
        :param stream_fmt: Format to use when ``stream_handler`` is set.

        """
        logger = logging.getLogger(name)
        logger.setLevel(self.level)

        if len(logger.handlers) > 0:
            return logger  # logger already configured

        logger.addHandler(logging.handlers.DatagramHandler(self.host, self.port))

        if stream_handler:
            if stream_fmt is None:
                stream_fmt = "[%(levelname)1.1s %(name)s:%(lineno)d %(asctime)s] %(message)s"
            handler = logging.StreamHandler()
            handler.setLevel(self.level)
            handler.setFormatter(logging.Formatter(stream_fmt))
            logger.addHandler(handler)

        return logger

    def _consumer_thread(self, logger):
        """Thread for consuming log records."""
        while not self.done.is_set():
            try:
                record = self._record_queue.get(timeout=1)
                logger.handle(record)
            except queue.Empty:
                continue

        # Finish processing any items left in the queue before quitting
        while True:
            try:
                record = self._record_queue.get_nowait()
                logger.handle(record)
            except queue.Empty:
                break

    def _socket_thread(self):
        """Thread for listening on the UDP socket."""
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host, self.port))

        while not self.done.is_set():
            try:
                socks, _, _ = select([sock], [], [], 1)
                if sock in socks:
                    length = sock.recv(4)
                    precord = sock.recv(length)
                    record = logging.makeLogRecord(pickle.loads(precord))
                    self._record_queue.put(record)
                else:
                    continue
            except:
                print("Exception!")

        sock.close()

    def _handler_thread(self, logger):
        """Thread for adding/removing handlers to the root logger."""
        while not self.done.is_set():
            try:
                msg = self._handler_queue.get(timeout=1)
                if len(msg) == 4:
                    handler =
                    logger.addHandler()
            except queue.Empty:
                pass

    def run(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)

        if len(self.handlers) == 0:
            self.handlers.append(logging.NullHandler())

        for handler in self.handlers:
            root_logger.addHandler(handler)

        threads = [
            th.Thread(target=self._socket_thread),
            th.Thread(target=self._consumer_thread, args=(root_logger,)),
            th.Thread(target=self._handler_thread, args=(root_logger,))
        ]
        for thread in threads:
            thread.start()
        [thread.join() for thread in threads]


class LogServerProcess(LogServer, mp.Process):
    def __init__(self, handlers=[], host=None, port=None, pipe=None,
                 level=logging.INFO):
        super(mp.Process, self).__init__()
        super(LogServerProcess, self).__init__(handlers, host, port, pipe, level)

        self.done = mp.Event()
        self.ready = mp.Event()


class LogServerThread(LogServer, th.Thread):
    def __init__(self, handlers=[], host=None, port=None, pipe=None,
                 level=logging.INFO):
        super(th.Thread, self).__init__()
        super(LogServerThread, self).__init__(handlers, host, port, pipe, level)

        self.done = th.Event()
        self.ready = th.Event()


if __name__ == "__main__":
    server = LogServerThread([logging.StreamHandler], "localhost", "9123")
    server.start()

    logger = server.get_logger("test")
