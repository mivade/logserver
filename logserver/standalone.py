from argparse import ArgumentParser
import logging
from . import run_server
from .handlers import SQLiteHandler


def main():
    """Entry point for running a standalone log server using a SQLite log
    handler. Launch with::

        python -m logserver

    """
    parser = ArgumentParser(
        description="Run a standalone log server using a SQLite database.")
    parser.add_argument("-p", "--port", default=9123, help="Port to listen on")
    parser.add_argument("-t", "--table", default="logs",
                        help="Name of table to store logs in")
    parser.add_argument("-f", "--filename", default="logs.sqlite",
                        help="SQLite filename")
    args = parser.parse_args()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        "[%(levelname)1.1s %(name)s %(asctime)s] %(msg)s"))

    handlers = [
        stream_handler,
        SQLiteHandler(args.filename, args.table)
    ]

    print("Listening for logs to handle on port", args.port)
    run_server(handlers, port=args.port)
