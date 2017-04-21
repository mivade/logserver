import tempfile
import os.path as osp
import shutil
import logging
import logging.handlers
import warnings
from multiprocessing import Process, Event
import time

import pytest

from .util import ascii_string
from .. import run_server, get_logger, create_logger


@pytest.fixture(scope="session")
def logfile():
    path = tempfile.mkdtemp()
    filename = osp.join(path, "output.log")
    yield filename
    shutil.rmtree(path, ignore_errors=True)


def test_get_logger():
    # defaults
    name = ascii_string()
    logger = get_logger(name)
    assert isinstance(logger, logging.Logger)
    assert logger.name == name
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2
    for handler in logger.handlers:
        assert isinstance(handler, (logging.handlers.DatagramHandler, logging.StreamHandler))

    # no stream, non-default log level
    name = ascii_string()
    logger = get_logger(name, level=logging.ERROR, stream_handler=False)
    assert isinstance(logger, logging.Logger)
    assert logger.name == name
    assert logger.level == logging.ERROR
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.handlers.DatagramHandler)


def test_create_logger():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        create_logger(ascii_string())
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)


def test_run_server(logfile):
    handler = logging.FileHandler(logfile)
    handler.setFormatter(logging.Formatter("%(msg)s"))
    handlers = [handler]
    done = Event()
    ready = Event()

    server = Process(target=run_server, args=(handlers,),
                     kwargs={"done": done, "ready": ready})
    server.start()
    ready.wait()

    logger = get_logger(ascii_string(), stream_handler=False)

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
