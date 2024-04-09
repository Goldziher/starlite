Accessing the list
====================

Intro
-----

The first thing you'll be setting up for our app is a route handler that returns a
single TODO list. A TODO list in this case will be a list of dictionaries representing
the items on that TODO list.

.. literalinclude:: /examples/todo_app/get_list/dict.py
    :language: python
    :caption: app.py
    :linenos:


If you run the app and visit http://127.0.0.1:8000/ in your browser you'll see the
following output:

.. figure:: images/get_todo_list.png

    Suddenly, JSON


Because the ``get_list`` function has been annotated  with
``List[Dict[str, Union[str, bool]]]``, Litestar infers that you want the data returned
from it to be serialized as JSON:

.. literalinclude:: /examples/todo_app/get_list/dict.py
    :language: python
    :lineno-start: 13
    :lines: 13


Cleaning up the example with dataclasses
++++++++++++++++++++++++++++++++++++++++

To make your life a little easier, you can transform this example by using :py:mod:`dataclasses` instead of plain dictionaries:

.. tip:: For an in-depth explanation of dataclasses, you can read this excellent Real Python
    article: `Data Classes in Python 3.7+ <https://realpython.com/python-data-classes/>`_

.. literalinclude:: /examples/todo_app/get_list/dataclass.py
    :caption: app.py
    :language: python
    :linenos:


This looks a lot cleaner and has the added benefit of being able to work with
dataclasses instead of plain dictionaries. The result will still be the same: Litestar
knows how to turn these dataclasses into JSON and will do so for you automatically.

.. tip::
    In addition to dataclasses, Litestar supports many more types such as
    :class:`TypedDict <typing.TypedDict>`, :class:`NamedTuple <typing.NamedTuple>`,
    `Pydantic models <https://docs.pydantic.dev/usage/models/>`_, or
    `attrs classes <https://www.attrs.org/en/stable/>`_.


Filtering the list using query parameters
-----------------------------------------

Currently ``get_list`` will always return all items on the list, but what if you
are interested in only those items with a specific status, for example all items that
are not yet marked as *done*?

For this you can employ query parameters; to define a query parameter, all that's needed
is to add an otherwise unused parameter to the function. Litestar will recognize this
and infer that it's going to be used as a query parameter. When a request is being made,
the query parameter will be extracted from the URL, and passed to the function parameter
of the same name.


.. literalinclude:: /examples/todo_app/get_list/query_param.py
    :caption: app.py
    :language: python
    :linenos:


.. figure:: images/todos-done.png

    Visiting http://127.0.0.1:8000?done=1 will give you all the TODOs that have been
    marked as *done*


.. figure:: images/todos-not-done.png

    while http://127.0.0.1:8000?done=0 will return only those not yet done


At first glance this seems to work just fine, but you might be able to spot a problem:
If you input anything other than ``?done=1``, it would still return items not yet marked
as done. For example, ``?done=john`` gives the same result as ``?done=0``.

An easy solution for this would be to simply check if the query parameter is either
``1`` or ``0``, and return a response with an HTTP status code that indicates an
error if it's something else:

.. literalinclude:: /examples/todo_app/get_list/query_param_validate_manually.py
    :caption: app.py
    :language: python
    :linenos:

If the query parameter equals ``1``, return all items that have ``done=True``:

.. literalinclude:: /examples/todo_app/get_list/query_param_validate_manually.py
    :language: python
    :caption: app.py
    :lines: 23-24
    :dedent: 2
    :linenos:
    :lineno-start: 23


If the query parameter equals ``0``, return all items that have ``done=False``:

.. literalinclude:: /examples/todo_app/get_list/query_param_validate_manually.py
    :language: python
    :caption: app.py
    :lines: 25-26
    :dedent: 2
    :linenos:
    :lineno-start: 25

Finally, if the query parameter has any other value, an :exc:`HTTPException` will be raised.
Raising an ``HTTPException`` tells Litestar that something went wrong, and instead of
returning a normal response, it will send a response with the HTTP status code given
(``400`` in this case) and the error message supplied.

.. literalinclude:: /examples/todo_app/get_list/query_param_validate_manually.py
    :language: python
    :caption: app.py
    :lines: 27
    :dedent: 2
    :linenos:
    :lineno-start: 27


.. figure:: images/done-john.png

    Try to access http://127.0.0.1?done=john now and you will get this error message


Now we've got that out of the way, but your code has grown to be quite complex for such
a simple task. You're probably thinking
`"there must be a better way!" <https://www.youtube.com/watch?t=566&v=p33CVV29OG8>`_,
and there is! Instead of doing these things manually, you can also just let Litestar
handle them for you!


Converting and validating query parameters
++++++++++++++++++++++++++++++++++++++++++

As mentioned earlier, type annotations can be used for more than static type checking
in Litestar; they can also define and configure behaviour. In this case, you can get
Litestar to convert the query parameter to a boolean value, matching the values of the
``TodoItem.done`` attribute, and in the same step validate it, returning error responses
for you should the supplied value not be a valid boolean.

.. literalinclude:: /examples/todo_app/get_list/query_param_validate.py
    :language: python
    :caption: app.py
    :linenos:


.. figure:: images/done-john-2.png

    Browse to http://127.0.0.1:8000?done=john from our earlier example, and you will see it now
    results in this descriptive error message


**What's happening here?**

Since :class:`bool` is being used as the type annotation for the ``done`` parameter,
Litestar will try to convert the value into a :class:`bool` first. Since ``john``
(arguably) is not a representation of a boolean value, it will return an error response
instead.

.. literalinclude:: /examples/todo_app/get_list/query_param_validate.py
    :language: python
    :caption: app.py
    :lines: 21
    :linenos:
    :lineno-start: 21

.. tip::
    It is important to note that this conversion is not the result of calling
    :class:`bool` on the raw value. ``bool("john")`` would be :obj:`True`, since Python
    considers all non-empty strings to be truthy.

    Litestar however supports customary boolean representation commonly used in the HTTP
    world; ``true`` and ``1`` are both converted to :obj:`True`, while ``false``
    and ``0`` are converted to be :obj:`False`.


If the conversion is successful however, ``done`` is now a :class:`bool`, which can then
be compared against the ``TodoItem.done`` attribute:

.. literalinclude:: /examples/todo_app/get_list/query_param_validate.py
    :language: python
    :caption: app.py
    :lines: 22
    :dedent: 2
    :linenos:
    :lineno-start: 22


.. seealso::

    * :ref:`Routing - Parameters - Type coercion <usage/routing/parameters:type coercion>`


Making the query parameter optional
+++++++++++++++++++++++++++++++++++

There is one problem left to solve though, and that is, what happens when you want to
get **all** items, done or not, and omit the query parameter?

.. figure:: images/missing-query.png

    Omitting the ``?done`` query parameter will result in an error

Because the query parameter has been defined as ``done: bool`` without giving it a
default value, it will be treated as a required parameter - just like a regular function
parameter. If instead you want this to be optional, a default value needs to be
supplied.


.. literalinclude:: /examples/todo_app/get_list/query_param_default.py
    :language: python
    :caption: app.py
    :linenos:


.. figure:: images/get_todo_list.png

    Browsing to http://localhost:8000 once more, you will now see it does not return an error if the
    query parameter is omitted


.. tip::
    In this instance, the default has been set to :obj:`None`, since we don't want to do
    any filtering if no ``done`` status is specified. If instead you wanted to only
    display not-done items by default, you could set the value to :obj:`False` instead.


.. seealso::

    * :ref:`Routing - Parameters - Query Parameters <usage/routing/parameters:query parameters>`


Interactive documentation
--------------------------

So far we have explored our TODO application by navigating to it manually, but there is
another way: Litestar comes with interactive API documentation, which is generated for
you automatically. All you need to do is run your app (``litestar run``) and visit
http://127.0.0.1:8000/schema/swagger

.. figure:: images/swagger-get.png

    The route handler set up earlier will show up in the interactive documentation


This documentation not only gives an overview of the API you have constructed, but also
allows you to send requests to it.

.. figure:: images/swagger-get-example-request.png

    Executing the same requests we did earlier


.. note::
    This is made possible by `Swagger <https://swagger.io/>`_ and
    `OpenAPI <https://www.openapis.org/>`_. Litestar generates an OpenAPI schema based
    on the route handlers, which can then be used by Swagger to set up the interactive
    documentation.

.. tip::
    In addition to Swagger, Litestar serves the documentation from the generated
    OpenAPI schema with `ReDoc <https://redocly.com/>`_ and
    `Stoplight Elements <https://stoplight.io/open-source/elements/>`_. You can browse
    to http://127.0.0.1:8000/schema/redoc and http://127.0.0.1:8000/schema/elements to
    view each, respectively.
