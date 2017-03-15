logserver
=========

A reusable, dependency-free log server.

This utilizes UDP for fast transmission of log events between processes or
threads and supports SQLite for archival.


Usage with the ``multiprocessing`` module
-----------------------------------------

Example usage::

  from multiprocessing import Process
  from logging import StreamHandler
  from logserver import run_server

  Process(target=run_server, args=(StreamHandler(),)).start()

  # do other stuff...


Running as a standalone server
------------------------------

``logserver`` can be executed as a script to run as a standalone process to
consume logs from clients::

  python -m logserver -f db.sqlite
