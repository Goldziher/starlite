.. _logging-usage:

Logging
=======

Application and request level loggers can be configured using the :class:`~litestar.logging.config.LoggingConfig`:

.. code-block:: python

   import logging

   from litestar import Litestar, Request, get
   from litestar.logging import LoggingConfig


   @get("/")
   def my_router_handler(request: Request) -> None:
       request.logger.info("inside a request")
       return None


   logging_config = LoggingConfig(
       root={"level": "INFO", "handlers": ["queue_listener"]},
       formatters={
           "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
       },
       log_exceptions="always",
   )

   app = Litestar(route_handlers=[my_router_handler], logging_config=logging_config)

.. attention::

    Litestar configures a non-blocking ``QueueListenerHandler`` which
    is keyed as ``queue_listener`` in the logging configuration. The above example is using this handler,
    which is optimal for async applications. Make sure to use it in your own loggers as in the above example.

.. attention::

    Exceptions won't be logged by default, except in debug mode. Make sure to use ``log_exceptions="always"`` as in the
    example above to log exceptions if you need it.


Using Python standard library
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`logging <https://docs.python.org/3/howto/logging.html>`_ is Python's builtin standard logging library and can be
configured through ``LoggingConfig``.

The ``LoggingConfig.configure()`` method returns a reference to ``logging.getLogger`` which can be used to access a
logger instance. Thus, the root logger can retrieved with ``logging_config.configure()()`` as shown in the example
below:

.. code-block:: python

    import logging

    from litestar import Litestar, Request, get
    from litestar.logging import LoggingConfig

    logging_config = LoggingConfig(
        root={"level": "INFO", "handlers": ["queue_listener"]},
        formatters={
            "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        log_exceptions="always",
    )

    logger = logging_config.configure()()


    @get("/")
    def my_router_handler(request: Request) -> None:
        request.logger.info("inside a request")
        logger.info("here too")


    app = Litestar(
        route_handlers=[my_router_handler],
        logging_config=logging_config,
    )

If you want to use ``LoggingConfig`` with another format string style, you need add a key "style"

.. code-block:: python

   logging_config = LoggingConfig(
      ...
       formatters={
           "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "style": "%"}
       },
       ...
   )

The above example is the same as using logging without the litestar ``LoggingConfig``.

.. code-block:: python

    import logging

    from litestar import Litestar, Request, get
    from litestar.logging.config import LoggingConfig


    def get_logger(mod_name: str) -> logging.Logger:
        """Return logger object."""
        format = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
        logger = logging.getLogger(mod_name)
        # Writes to stdout
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(format))
        logger.addHandler(ch)
        return logger


    logger = get_logger(__name__)


    @get("/")
    def my_router_handler(request: Request) -> None:
        logger.info("logger inside a request")


    app = Litestar(
        route_handlers=[my_router_handler],
    )

Formatter like JSON string
--------------------------

* printf-style String Formatting

.. code-block:: python

   format = ('{"asctime": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}')

   ch.setFormatter(logging.Formatter(format))

* str.format() String Formatting

.. code-block:: python

   # The double bracket are an escaping construction.
   format = ('{{"asctime": "{asctime}", "name": "{name}", "level": "{levelname}", "message": "{message}" }}')

   ch.setFormatter(logging.Formatter(format, style="{"))

* string.Template String Formatting

.. code-block:: python

   format = ('{"asctime": "$asctime", "name": "$name", "level": "$levelname", "message": "$message"}')

   ch.setFormatter(logging.Formatter(format, style="$"))

Using Picologging
^^^^^^^^^^^^^^^^^

`Picologging <https://github.com/microsoft/picologging>`_ is a high performance logging library that is developed by
Microsoft. Litestar will default to using this library automatically if its installed - requiring zero configuration on
the part of the user. That is, if ``picologging`` is present the previous example will work with it automatically.

Using StructLog
^^^^^^^^^^^^^^^

`StructLog <https://www.structlog.org/en/stable/>`_ is a powerful structured-logging library. Litestar ships with a
dedicated logging plugin and config for using it:

.. code-block:: python

   from litestar import Litestar, Request, get
   from litestar.plugins.structlog import StructlogPlugin


   @get("/")
   def my_router_handler(request: Request) -> None:
       request.logger.info("inside a request")
       return None


   structlog_plugin = StructlogPlugin()

   app = Litestar(route_handlers=[my_router_handler], plugins=[StructlogPlugin()])

Subclass Logging Configs
^^^^^^^^^^^^^^^^^^^^^^^^

You can easily create you own ``LoggingConfig`` class by subclassing
:class:`BaseLoggingConfig <.logging.config.BaseLoggingConfig>` and implementing the ``configure`` method.
