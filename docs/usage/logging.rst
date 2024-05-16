Logging
=======

Application and request level loggers can be configured using the :class:`~litestar.logging.config.LoggingConfig`:

.. literalinclude:: /examples/logging/logging_base.py
    :caption: Base logging example
    :language: python


.. attention::

    Litestar configures a non-blocking ``QueueListenerHandler`` which
    is keyed as ``queue_listener`` in the logging configuration. The above example is using this handler,
    which is optimal for async applications. Make sure to use it in your own loggers as in the above example.



Standard Library Logging (Manual Configuration)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`logging <https://docs.python.org/3/howto/logging.html>`_ is Python's builtin standard logging library and can be integrated with `LoggingConfig` as the `root` logging. By using `logging_config()()` you can build a `logger` to be used around your project.

.. literalinclude:: /examples/logging/logging_standard_library.py
    :caption: Standard Library Logging (manual)
    :language: python


The above example is the same as using logging without the litestar LoggingConfig.

.. literalinclude:: /examples/logging/logging_litestar_logging_config.py
    :caption: Standard Library Logging (LoggingCondig)
    :language: python


Using Picologging
^^^^^^^^^^^^^^^^^

`Picologging <https://github.com/microsoft/picologging>`_ is a high performance logging library that is developed by
Microsoft. Litestar will default to using this library automatically if its installed - requiring zero configuration on
the part of the user. That is, if ``picologging`` is present the previous example will work with it automatically.

Using StructLog
^^^^^^^^^^^^^^^

`StructLog <https://www.structlog.org/en/stable/>`_ is a powerful structured-logging library. Litestar ships with a dedicated
logging plugin and config for using it:

.. literalinclude:: /examples/logging/logging_structlog.py
    :caption: Logging with structlog
    :language: python


Subclass Logging Configs
^^^^^^^^^^^^^^^^^^^^^^^^

You can easily create you own ``LoggingConfig`` class by subclassing
:class:`BaseLoggingConfig <.logging.config.BaseLoggingConfig>` and implementing the ``configure`` method.
