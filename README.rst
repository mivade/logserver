logserver
=========

A reusable, dependency-free log server for Python.


Features
--------

* No dependencies outside of the Python standard library
* Uses UDP for fast transmission of logs
* Server for handling aggregated logs can run independently, as a thread, or as
  as subprocess
* Includes a handler for logging to SQLite
* MIT license

Future development possibilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Adding configurable protocols (e.g., choose between TCP or UDP)
* Adding optional support for third-party libraries (e.g., ZeroMQ for
  transmitting logs, pandas/PyTables/SQLAlchemy for storing logs)


Usage with the ``multiprocessing`` module
-----------------------------------------

Example usage:

.. code-block:: python

  from multiprocessing import Process
  from logging import StreamHandler
  from logserver import run_server

  Process(target=run_server, args=(StreamHandler(),)).start()

  # do other stuff...


Running as a standalone server
------------------------------

``logserver`` can be executed as a script to run as a standalone process to
consume logs from clients:

.. code-block:: shell-session

  $ python -m logserver -f db.sqlite
