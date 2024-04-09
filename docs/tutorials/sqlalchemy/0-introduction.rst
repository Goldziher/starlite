Introduction
------------

We start with a full script that shows how you can use SQLAlchemy with Litestar. In this app, we interact with
SQLAlchemy in the manner described by the
`SQLAlchemy documentation <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm>`_, and so if you
are looking for more information about any of the SQLAlchemy code, this will be a great place to start.

You'll notice that we use a couple of Litestar features that you may not have encountered yet:

1. Management and injection of :ref:`application state <application-state>`
2. Use of a :ref:`Lifespan context manager <lifespan-context-managers>`

And we will continue to learn about other Litestar features as we work through the tutorial, such as:

1. Dependency injection
2. Plugins

The full app
============

While it may look imposing, this app only has minor behavioral differences to the previous example. It is still an app
that maintains a TODO list, that allows for adding, updating and viewing the collection of TODO items.

Don't worry if there are things in this example that you don't understand. We will cover all of the components in detail
in the following sections.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:

The differences
===============

Apart from the obvious differences due to the SQLAlchemy code, there are a few things worth mentioning from the outset.

Complexity
++++++++++

This code is undoubtedly more complex than the code we have seen so far - although a crude measure of complexity, we can
see that there are more than double the lines of code to the previous example.

Lifespan context manager
++++++++++++++++++++++++

When using a database, we need to ensure that we clean up our resources correctly. To do this, we create a context
manager called ``db_connection()`` that creates a new :class:`engine <sqlalchemy.ext.asyncio.AsyncEngine>` and disposes
of it when we are done. This context manager is added to the application's ``lifespan`` argument.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:
    :lines: 28-41,100

Database creation
+++++++++++++++++
Before we can use the database we need to make sure it exists and the tables are created as defined by the ``TodoItem``
class. This can be done by a synchronous call to ``Base.metadata.create_all`` which is invoked by ``run_sync``. If the
tables are already setup according to the model, the call does nothing.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:
    :lines: 28-41
    :emphasize-lines: 8-9

Application state
+++++++++++++++++

We see two examples of access and use of application state. The first is in the ``db_connection()`` context manager,
where we use the ``app.state`` object to store the engine.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:
    :lines: 28-41
    :emphasize-lines: 3,6

The second is by using the ``state`` keyword argument in our handler functions, so that we can access the engine in our
handlers.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:
    :lines: 69-72
    :emphasize-lines: 2,3

Serialization
+++++++++++++

Now that we are using SQLAlchemy models, Litestar cannot automatically handle (de)serialization of our data. We have
to convert the SQLAlchemy models to a type that Litestar can serialize. This example introduces two type aliases,
``TodoType`` and ``TodoCollectionType`` to help us represent this data at the boundaries of our handlers. It also
introduces the ``serialize_todo()`` to help us convert our data from the ``TodoItem`` type to a type that is
serializable by Litestar.

.. literalinclude::
    /examples/contrib/sqlalchemy/plugins/tutorial/full_app_no_plugins.py
    :language: python
    :linenos:
    :lines: 2-3,14-15,47-50,91-97
    :emphasize-lines: 3,4,6,7,10,15

Behavior
++++++++

The ``add_item()`` and ``update_item()`` routes no longer return the full collection, instead they return the item that
was added or updated. This is a minor detail change, but it is worth noting as it brings the behavior of the app closer
to what we would expect from a conventional API.

Next steps
==========

Lets start cleaning this app up a little.

One of the standout issues is that we repeat the logic to create a database session in every handler. This is
something that we can fix with dependency injection.
