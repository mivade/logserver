import os
import os.path as osp
import shutil
import time
import tempfile
from multiprocessing import Event, Pipe
import logging
import warnings
from uuid import uuid4

import pytest

import logserver


@pytest.fixture(scope="session")
def logfile():
    path = tempfile.mkdtemp()
    filename = osp.join(path, "output.log")
    yield filename
    shutil.rmtree(path, ignore_errors=True)


def test_server_process(logfile):
    handler = logging.FileHandler(logfile)
    handler.setFormatter(logging.Formatter("%(msg)s"))
    handlers = [handler]

    done, ready = Event(), Event()

    server = logserver.make_server_process(handlers, done=done, ready=ready)
    server.start()
    ready.wait(timeout=1)

    logger = logserver.get_logger('test', stream_handler=False)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    time.sleep(0.01)
    done.set()
    server.join()

    with open(logfile, "r") as lf:
        lines = [l.strip() for l in lf.readlines()]
    assert "debug" not in lines
    assert "info" in lines
    assert "warning" in lines
    assert "error" in lines
    assert "critical" in lines


def test_server_thread(logfile):
    done = Event()
    handler = logging.FileHandler(logfile)
    server = logserver.make_server_thread([handler], done=done)
    server.start()

    logger = logserver.get_logger('test', stream_handler=False)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    done.set()
    server.join()

    with open(logfile, "r") as lf:
        lines = [l.strip() for l in lf.readlines()]
    assert "debug" not in lines
    assert "info" in lines
    assert "warning" in lines
    assert "error" in lines
    assert "critical" in lines


def test_create_logger():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        logserver.create_logger("name")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)


def test_modify_handlers(logfile):
    path = os.path.dirname(logfile)

    pipe, child = Pipe()
    done = Event()
    thread = logserver.make_server_thread(done=done, pipe=child)
    thread.start()

    msg = logserver.CreateHandlerMessage()
    msg.name = "txt"
    msg.handler = "FileHandler"
    msg.args = [osp.join(path, "runtime.txt")]
    print(msg)
    pipe.send(msg.to_tuple())

    logger = logserver.get_logger("runtime")
    checksum = str(uuid4())
    logger.info(checksum)
    time.sleep(0.1)

    print(os.listdir(osp.dirname(logfile)))
    with open(msg.args[0], 'r') as f:
        assert checksum in f.read()


class TestCreateHandlerMessage:
    def test_not_set(self):
        msg = logserver.CreateHandlerMessage()
        with pytest.raises(AssertionError):
            msg.to_tuple()

    def test_to_tuple(self):
        msg = logserver.CreateHandlerMessage()
        msg.name = "name"
        msg.handler = "NullHandler"

        res = msg.to_tuple()
        assert isinstance(res, tuple)
        assert res[0] == msg.name
        assert res[1] == msg.handler
        assert res[2] == msg.args
        assert res[3] == msg.kwargs

    def test_from_tuple(self):
        tpl = logserver.CreateHandlerMessage.from_tuple(
            ('test', 'NullHandler', [], dict()))
        assert isinstance(tpl, logserver.CreateHandlerMessage)

        with pytest.raises(AssertionError):
            logserver.CreateHandlerMessage.from_tuple((1, 1, 1, 1))

        with pytest.raises(ValueError):
            logserver.CreateHandlerMessage.from_tuple(("one", "two"))

    def test_str(self):
        msg = logserver.CreateHandlerMessage()
        msg.name = "test"
        msg.handler = "NullHandler"
        msg.args = []
        msg.kwargs = {}

        string = str(msg)
        assert "name=test" in string
        assert "handler=NullHandler" in string
        assert "args=[]" in string
        assert "kwargs={}" in string
