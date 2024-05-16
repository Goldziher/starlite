Application basics
==================

First steps
------------

Before we start building our TODO application, let us start with the basics.


Install Litestar
++++++++++++++++

To install Litestar, run ``pip install 'litestar[standard]'``. This will install Litestar
as well as `uvicorn <https://www.uvicorn.org/>`_ -  a web server to serve your application.

.. note::
    You can use any ASGI-capable web server, but this tutorial will use - and Litestar
    recommends - Uvicorn.


Hello, world!
+++++++++++++

The most basic application you can implement - and a classic one at that - is of course
one that prints ``"Hello, world!"``:


.. literalinclude:: /examples/todo_app/hello_world.py
    :language: python
    :caption: app.py


Now save the contents of this example in a file called ``app.py`` and type
``litestar run`` in your terminal. This will serve the application locally on your
machine. Now visit http://127.0.0.1:8000/ in your browser:

.. image:: images/hello_world.png


Now that we have a working application, let us examine how we got here in a bit more detail.


Route handlers
---------------

Route handlers tell your Litestar application what to do when it gets a request.
They are named this way because they typically handle a single URL path (or *route*),
which is the part of the URL that's specific to your application. In our current
example, the only route handler we have is for ``hello_world``, and it is using the
``/`` path.

.. tip::
    For example, if your application has a route for handling requests to the ``/home``
    URL path, you would create a route handler function that would be called when a
    request to that path is received.

The first argument to the route handler is the *path*, which in this example has been
set to ``/``. This means that the function ``hello_world`` will be called when a request
is being made to the ``/`` path of your application. The name of the handler decorator
- ``get`` - refers to the HTTP method to which you want to respond. Using ``get`` tells
Litestar that you only want to use this function when a ``GET`` request is being made.


.. literalinclude:: /examples/todo_app/hello_world.py
    :language: python
    :emphasize-lines: 4
    :linenos:


.. note::

    The syntax used in this example (the ``@get`` notation) is called a decorator. It's
    a function that takes another function as its argument (in this case ``hello_world``)
    and replaces it with the return value of the decorator function.
    Without the decorator, the example would look like this:

    .. literalinclude:: /examples/todo_app/hello_world_2.py
        :language: python


    For an in-depth explanation of decorators, you can read this excellent Real Python
    article: `Primer on Python Decorators <https://realpython.com/primer-on-python-decorators/>`_


.. seealso::

    * :doc:`/usage/routing/handlers`


Type annotations
----------------

Type annotations play an important role in a Litestar application. They tell Litestar
how you want your data to behave, and what you intend to do with it.


.. literalinclude:: /examples/todo_app/hello_world.py
    :language: python
    :emphasize-lines: 5
    :linenos:


In this example, the ``hello_world`` function has a return annotation of ``-> str``.
This means that it will return a :class:`string <str>`, and lets Litestar know that
you would like to send the return value as-is.

.. note::
    While type annotations by default don't have any influence on runtime behaviour,
    Litestar uses them for many things, for example to validate incoming request data.

    If you are using a static type checker - such as
    `mypy <https://mypy.readthedocs.io/en/stable/>`_ or
    `pyright <https://microsoft.github.io/pyright/#/>`_ - this has the added benefit of
    making your applications easy to check and more type-safe.



Applications
------------

After a route handler has been defined, it needs to be registered with an application
in order to start serving requests. The application is an instance of the
:class:`Litestar <litestar.app.Litestar>` class. This is the entry point for everything,
and can be used to register previously defined route handlers by passing a list of them
as the first argument:

.. literalinclude:: /examples/todo_app/hello_world.py
    :language: python
    :emphasize-lines: 9
    :linenos:


.. seealso::

    * :doc:`/usage/applications`



Running the application
-----------------------

The last step is to actually run the application. Litestar does not include its own HTTP
server, but instead makes use of the
`ASGI protocol <https://asgi.readthedocs.io>`_, which is a protocol Python objects can
use in order to interact with application servers like
`uvicorn <https://www.uvicorn.org/>`_ that actually implement the HTTP protocol and
handle it for you.

If you installed Litestar with ``pip install litestar[standard]``, this will have
included *uvicorn*, as well as the Litestar CLI. The CLI provides a convenient wrapper
around uvicorn, allowing you to easily run applications without the need for much
configuration.

When you run ``litestar run``, it will recognise the ``app.py`` file and the
``Litestar`` instance within it without the need to specify this manually.

.. tip::
    You can start the server in "reload mode", which will reload the application each
    time you have made a change to the file. For this, simply pass the ``--reload``
    flag as a command line argument: ``litestar run --reload``.


.. seealso::

    * :doc:`/usage/cli`
