import time
import logging
import random
from multiprocessing import Event
import logserver
from logserver.handlers import SQLiteHandler

logger = logserver.get_logger("demo", stream_handler=False)
finished, ready = Event(), Event()

handlers = [
    SQLiteHandler("logs.sqlite"),
    logging.StreamHandler()
]
server = logserver.make_server_process(handlers, done=finished, ready=ready)
server.start()

# If we don't wait for the server to finish initializing, we can lose the first
# log message.
ready.wait()

for i in range(5):
    delay = random.randint(1, 5)
    logger.warning("Iteration %d: Sleeping for %d seconds...", i, delay)
    time.sleep(delay)
    logger.info("Iteration %d: Awoke!", i)

finished.set()
server.join()
