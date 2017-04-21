import os.path as osp
import shutil
import logging
import logging.handlers
import tempfile
from uuid import uuid4
import time

import pytest

from .util import ascii_string
from ..handlers import SQLiteHandler
from ..server import LogServer, LogServerProcess, LogServerThread


@pytest.fixture
def server_process():
    p = LogServerProcess()
    yield p
    p.stop()
    p.join(timeout=1)
    if p.exitcode != 0:
        p.terminate()


@pytest.fixture
def server_thread():
    thread = LogServerThread()
    yield thread
    thread.stop()
    thread.join(timeout=1)


@pytest.fixture
def temp_file():
    directory = tempfile.mkdtemp()
    filename = osp.abspath(osp.join(directory, "log.log"))
    yield filename
    shutil.rmtree(directory, ignore_errors=True)


class TestLogServer:
    def test_get_handler_class(self):
        with pytest.raises(RuntimeError):
            LogServer.get_handler_class("DoesntExist")

        with pytest.raises(TypeError):
            LogServer.get_handler_class("Logger")

        cls = LogServer.get_handler_class("SQLiteHandler")
        assert issubclass(cls, SQLiteHandler)

        cls = LogServer.get_handler_class("StreamHandler")
        assert issubclass(cls, logging.StreamHandler)

        cls = LogServer.get_handler_class("DatagramHandler")
        assert issubclass(cls, logging.handlers.DatagramHandler)

    def test_get_logger(self):
        server = LogServer()
        name = ascii_string()
        logger = server.get_logger(name)
        assert isinstance(logger, logging.Logger)
        assert logger.name == name

        # should have DatagramHandler and StreamHandler
        assert len(logger.handlers) == 2

        # once configured, shouldn't add more handlers
        logger = server.get_logger(ascii_string())
        assert len(logger.handlers) == 2

        # don't add a stream handler
        logger = server.get_logger(ascii_string(), stream_handler=False)
        assert len(logger.handlers) == 1

    def test_add_remove_handler(self):
        server = LogServer()

        handler = server.add_handler("test", "StreamHandler")
        assert isinstance(handler, logging.Handler)

        server.remove_handler("test")


def test_process_log_server(server_process, temp_file):
    server_process.start()
    assert server_process.ready.wait(timeout=1) is not None
    server_process.add_handler("test", "FileHandler", temp_file)

    logger = server_process.get_logger("test", stream_handler=False)
    uuid = str(uuid4())
    time.sleep(0.05)
    logger.info(uuid)
    time.sleep(0.05)

    with open(temp_file, 'r') as f:
        assert uuid in f.read()

    server_process.remove_handler("test")

    server_process.stop()
    server_process.join(timeout=1)


def test_threaded_log_server(server_thread, temp_file):
    server_thread.start()
    assert server_thread.ready.wait(timeout=1) is not None
    server_thread.add_handler("test", "FileHandler", temp_file)

    logger = server_thread.get_logger(ascii_string(), stream_handler=False)
    uuid = str(uuid4())
    time.sleep(0.05)
    logger.info(uuid)
    time.sleep(0.05)

    with open(temp_file, 'r') as f:
        assert uuid in f.read()

    server_thread.remove_handler("test")

    server_thread.stop()
    server_thread.join(timeout=1)
