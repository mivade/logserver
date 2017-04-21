logserver
=========

.. image:: https://travis-ci.org/mivade/logserver.svg?branch=master
    :target: https://travis-ci.org/mivade/logserver

A reusable, dependency-free log server for Python.


Features
--------

* No dependencies outside of the Python standard library
* Uses UDP for fast transmission of logs
* Server for handling aggregated logs can run independently, as a thread, or as
  as a subprocess
* Includes a convenience function for pre-configuring loggers to work with the
  server and formatting messages on STDOUT
* Includes a handler for logging to SQLite
* MIT license


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


Development
-----------

Testing requires ``pytest`` and ``pytest-cov``. To run tests:

.. code-block:: shell-session

  $ pip install -r test-requirements.txt
  $ pytest
