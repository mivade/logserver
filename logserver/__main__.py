from argparse import ArgumentParser
import logging
from .server import log_server
from .handlers import SQLiteHandler


parser = ArgumentParser(
    description="Run a standalone log server using a SQLite database.")
parser.add_argument("-p", "--port", default=9123, help="Port to listen on")
parser.add_argument("-f", "--filename", default="logs.sqlite",
                    help="SQLite filename")
args = parser.parse_args()

handlers = [logging.StreamHandler(), SQLiteHandler(args.filename)]

print("Listening for logs to handle on port", args.port)
server = log_server(handlers, port=args.port)
