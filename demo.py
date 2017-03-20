import time
import random
import logging
from multiprocessing import Process
import logserver
from logserver.handlers import SQLiteHandler


logger = logserver.get_logger("demo")

p = Process(target=logserver.run_server, args=[[SQLiteHandler("logs.sqlite")]])
p.start()

for _ in range(10):
    delay = random.randint(0, 10)
    logger.warning("Sleeping for %d seconds...", delay)
    time.sleep(delay)
    logger.info("Awoke!")

p.terminate()
