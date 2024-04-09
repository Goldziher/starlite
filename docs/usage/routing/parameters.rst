Parameters
===========

Path Parameters
---------------

Path :term:`parameters <parameter>` are parameters declared as part of the ``path`` component of
the URL. They are declared using a simple syntax ``{param_name:param_type}`` :

.. literalinclude:: /examples/parameters/path_parameters_1.py
    :caption: Defining a path parameter in a route handler

In the above there are two components:

1. The path :term:`parameter` is defined in the :class:`@get() <.handlers.get>` :term:`decorator`, which declares both
   the parameter's name (``user_id``) and type (:class:`int`).
2. The :term:`decorated <decorator>` function ``get_user`` defines a parameter with the same name as the
   parameter defined in the ``path`` :term:`kwarg <argument>`.

The correlation of parameter name ensures that the value of the path parameter will be injected into
the function when it is called.

Supported Path Parameter Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, the following types are supported:

* ``date``: Accepts date strings and time stamps.
* ``datetime``: Accepts date-time strings and time stamps.
* ``decimal``: Accepts decimal values and floats.
* :class:`float`: Accepts ints and floats.
* :class:`int`: Accepts ints and floats.
* :class:`path`: Accepts valid POSIX paths.
* :class:`str`: Accepts all string values.
* ``time``: Accepts time strings with optional timezone compatible with pydantic formats.
* ``timedelta``: Accepts duration strings compatible with the pydantic formats.
* ``uuid``: Accepts all uuid values.

The types declared in the path :term:`parameter` and the function do not need to match 1:1 - as long as
parameter inside the function declaration is typed with a "higher" type to which the lower type can be coerced,
this is fine. For example, consider this:

.. literalinclude:: /examples/parameters/path_parameters_2.py
    :caption: Coercing path parameters into different types

The :term:`parameter` defined inside the ``path`` :term:`kwarg <argument>` is typed as :class:`int` , because the value
passed as part of the request will be a timestamp in milliseconds without any decimals. The parameter in
the function declaration though is typed as :class:`datetime.datetime`.

This works because the int value will be passed to a pydantic model representing the function signature, which will
coerce the :class:`int` into a :class:`~datetime.datetime`.

Thus, when the function is called it will be called with a :class:`~datetime.datetime`-typed parameter.

.. note:: You only need to define the :term:`parameter` in the function declaration if it is actually used inside the
    function. If the path parameter is part of the path, but the function does not use it, it is fine to omit
    it. It will still be validated and added to the OpenAPI schema correctly.

The Parameter function
----------------------

:func:`~.params.Parameter` is a helper function wrapping a :term:`parameter` with extra information to be
added to the OpenAPI schema.

Extra validation and documentation for path params
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to add validation or enhance the OpenAPI documentation generated for a given path :term:`parameter`,
you can do so using the `the parameter function`_:

.. literalinclude:: /examples/parameters/path_parameters_3.py
    :caption: Adding extra validation and documentation to a path parameter

In the above example, :func:`~.params.Parameter` is used to restrict the value of :paramref:`~.params.Parameter.version`
to a range between 1 and 10, and then set the :paramref:`~.params.Parameter.title`,
:paramref:`~.params.Parameter.description`, :paramref:`~.params.Parameter.examples`, and
:paramref:`externalDocs <.params.Parameter.external_docs>` sections of the OpenAPI schema.

Query Parameters
----------------

Query :term:`parameters <parameter>` are defined as :term:`keyword arguments <argument>` to handler functions.
Every :term:`keyword argument <argument>` that is not otherwise specified (for example as a
:ref:`path parameter <usage/routing/parameters:path parameters>`) will be interpreted as a query parameter.

.. literalinclude:: /examples/parameters/query_params.py
    :caption: Defining query parameters in a route handler

.. admonition:: Technical details
    :class: info

    These :term:`parameters <parameter>` will be parsed from the function signature and used to generate a Pydantic model.
    This model in turn will be used to validate the parameters and generate the OpenAPI schema.

    This means that you can also use any pydantic type in the signature, and it will
    follow the same kind of validation and parsing as you would get from pydantic.

Query :term:`parameters <parameter>` come in three basic types:

- Required
- Required with a default value
- Optional with a default value

Query parameters are **required** by default. If one such a parameter has no value,
a :exc:`~.exceptions.http_exceptions.ValidationException` will be raised.

Default values
~~~~~~~~~~~~~~

In this example, ``param`` will have the value ``"hello"`` if it is not specified in the request.
If it is passed as a query :term:`parameter` however, it will be overwritten:

.. literalinclude:: /examples/parameters/query_params_default.py
    :caption: Defining a default value for a query parameter

Optional :term:`parameters <parameter>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of only setting a default value, it is also possible to make a query parameter entirely optional.

Here, we give a default value of ``None`` , but still declare the type of the query parameter
to be a :class:`string <str>`. This means that this parameter is not required.

If it is given, it has to be a :class:`string <str>`.
If it is not given, it will have a default value of ``None``

.. literalinclude:: /examples/parameters/query_params_optional.py
    :caption: Defining an optional query parameter

Type coercion
-------------

It is possible to coerce query :term:`parameters <parameter>` into different types.
A query starts out as a :class:`string <str>`, but its values can be parsed into all kinds of types.

Since this is done by Pydantic, everything that works there will work for query parameters as well.

.. literalinclude:: /examples/parameters/query_params_types.py
    :caption: Coercing query parameters into different types

Alternative names and constraints
---------------------------------

Sometimes you might want to "remap" query :term:`parameters <parameter>` to allow a different name in the URL
than what is being used in the handler function. This can be done by making use of :func:`~.params.Parameter`.

.. literalinclude:: /examples/parameters/query_params_remap.py
    :caption: Remapping query parameters to different names

Here, we remap from ``snake_case`` in the handler function to ``camelCase`` in the URL.
This means that for the URL ``http://127.0.0.1:8000?camelCase=foo`` , the value of ``camelCase``
will be used for the value of the ``snake_case`` parameter.

:func:`~.params.Parameter` also allows us to define additional constraints:

.. literalinclude:: /examples/parameters/query_params_constraints.py
    :caption: Constraints on query parameters

In this case, ``param`` is validated to be an *integer larger than 5*.

Header and Cookie Parameters
----------------------------

Unlike *Query* :term:`parameters <parameter>`, *Header* and *Cookie* parameters have to be
declared using `the parameter function`_ , for example:

.. literalinclude:: /examples/parameters/header_and_cookie_parameters.py
    :caption: Defining header and cookie parameters

As you can see in the above, header parameters are declared using the ``header``
:term:`kwargs <argument>` and cookie parameters using the ``cookie`` :term:`kwarg <argument>`.
Aside form this difference they work the same as query parameters.

Layered Parameters
------------------

As part of Litestar's :ref:`layered architecture <usage/applications:layered architecture>`, you can declare
:term:`parameters <parameter>` not only as part of individual route handler functions, but also on other layers
of the application:

.. literalinclude:: /examples/parameters/layered_parameters.py
    :caption: Declaring parameters on different layers of the application

In the above we declare :term:`parameters <parameter>` on the :class:`Litestar app <.app.Litestar>`,
:class:`router <.router.Router>`, and :class:`controller <.controller.Controller>` layers in addition to those
declared in the route handler. Now, examine these more closely.

* ``app_param`` is a cookie parameter with the key ``special-cookie``. We type it as :class:`str` by passing
  this as an arg to the :func:`~.params.Parameter` function. This is required for us to get typing in the OpenAPI doc.
  Additionally, this parameter is assumed to be required because it is not explicitly set as ``False`` on
  :paramref:`~.params.Parameter.required`.

  This is important because the route handler function does not declare a parameter called ``app_param`` at all,
  but it will still require this param to be sent as part of the request of validation will fail.

* ``router_param`` is a header parameter with the key ``MyHeader``. Because it is set as ``False`` on
  :paramref:`~.params.Parameter.required`, it will not fail validation if not present unless explicitly declared by a
  route handler - and in this case it is.

  Thus, it is actually required for the router handler function that declares it as an :class:`str` and not an
  ``str | None``. If a :class:`string <str>` value is provided, it will be tested against the provided regex.
* ``controller_param`` is a query param with the key ``controller_param``. It has an :paramref:`~.params.Parameter.lt`
  set to ``100`` defined on the controller, which means the provided value must be less than 100.

  Yet the route handler re-declares it with an :paramref:`~.params.Parameter.lt` set to ``50``,
  which means for the route handler this value must be less than 50.
* ``local_param`` is a route handler local :ref:`query parameter <usage/routing/parameters:query parameters>`, and
  ``path_param`` is a :ref:`path parameter <usage/routing/parameters:path parameters>`.

.. note:: You cannot declare path :term:`parameters <parameter>` in different application layers. The reason for this
    is to ensure simplicity - otherwise parameter resolution becomes very difficult to do correctly.
