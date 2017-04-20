import logging
import logging.handlers
import pytest

from ..handlers import SQLiteHandler
from ..server import LogServer, LogServerProcess, LogServerThread


class TestLogServer:
    def test_get_handler_class(self):
        with pytest.raises(RuntimeError):
            LogServer.get_handler_class("DoesntExist")

        cls = LogServer.get_handler_class("SQLiteHandler")
        assert issubclass(cls, SQLiteHandler)

        cls = LogServer.get_handler_class("StreamHandler")
        assert issubclass(cls, logging.StreamHandler)

        cls = LogServer.get_handler_class("DatagramHandler")
        assert issubclass(cls, logging.handlers.DatagramHandler)