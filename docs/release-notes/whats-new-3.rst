.. py:currentmodule:: litestar


What's changed in 3.0?
======================

This document is an overview of the changes between version **2.11.x** and **3.0**.
For a detailed list of all changes, including changes between versions leading up to the
3.0 release, consult the :doc:`/release-notes/changelog`.

.. note:: The **2.11** release line is unaffected by this change

Imports
-------

+----------------------------------------------------+------------------------------------------------------------------------+
| ``2.x``                                           | ``3.x``                                                                 |
+====================================================+========================================================================+
| **SECTION**                                                                                                                 |
+----------------------------------------------------+------------------------------------------------------------------------+
| Put your changes here from v2                         | Put your changes here from v3                                       |
+----------------------------------------------------+------------------------------------------------------------------------+


Removal of ``StaticFileConfig``
-------------------------------

The ``StaticFilesConfig`` has been removed, alongside these related parameters and
functions:

- ``Litestar.static_files_config``
- ``Litestar.url_for_static_asset``
- ``Request.url_for_static_asset``

:func:`create_static_files_router` is a drop-in replacement for ``StaticFilesConfig``,
and can simply be added to the ``route_handlers`` like any other regular handler.

Usage of ``url_for_static_assets`` should be replaced with a ``url_for("static", ...)``
call.


Implicit Optional Default Parameters
------------------------------------

In v2, if a handler was typed with an optional parameter it would be implicitly given a default value of ``None``. For
example, if the following handler is called with no query parameter, the value ``None`` would be passed in to the
handler for the ``param`` parameter:

.. code-block:: python

    @get("/")
    def my_handler(param: int | None) -> ...:
        ...

This legacy behavior originates from our history of using Pydantic v1 models to represent handler signatures. In v3, we
no longer make this implicit conversion. If you want to have a default value of ``None`` for an optional parameter, you
must explicitly set it:

.. code-block:: python

    @get("/")
    def my_handler(param: int | None = None) -> ...:
        ...


OpenAPI Controller Replaced by Plugins
--------------------------------------

In version 3.0, the OpenAPI controller pattern, deprecated in v2.8, has been removed in
favor of a more flexible plugin system.

Elimination of ``OpenAPIController`` Subclassing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Previously, users configured elements such as the root path and styling by subclassing OpenAPIController and setting it
on the ``OpenAPIConfig.openapi_controller`` attribute. As of version 3.0, this pattern has been removed. Instead, users
are required to transition to using UI plugins for configuration.

Migration Steps:

1. Remove any implementations subclassing ``OpenAPIController``.
2. Use the :attr:`OpenAPIConfig.render_plugins` attribute to configure the OpenAPI UI made available to your users.
   If no plugin is supplied, we automatically add the :class:`ScalarRenderPlugin` for the default configuration.
3. Use the :attr:`OpenAPIConfig.openapi_router` attribute for additional configuration.

See the :doc:`/usage/openapi/ui_plugins` documentation for more information on how to configure OpenAPI plugins.

Changes to Endpoint Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``OpenAPIConfig.enabled_endpoints`` attribute is no longer available in version 3.0.0. This attribute previously
enabled a set of endpoints that would serve different OpenAPI UIs. In the new version, only the ``openapi.json``
endpoint is enabled by default, alongside the ``Scalar`` UI plugin as the default.

To adapt to this change, you should explicitly configure any additional endpoints you need by properly setting up the
necessary plugins within the :attr:`OpenAPIConfig.render_plugins` parameter.

Modification to ``root_schema_site`` Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``root_schema_site`` attribute, which enabled serving a particular UI at the OpenAPI root path, has been removed in
version 3.0. The new approach automatically assigns the first :class:`OpenAPIRenderPlugin` listed in the
:attr:`OpenAPIConfig.render_plugins` list to serve at the ``/schema`` endpoint, unless a plugin has been defined with
the root path (``/``), in which case that plugin will be used.

For those previously using the ``root_schema_site`` attribute, the migration involves ensuring that the UI intended to
be served at the ``/schema`` endpoint is the first plugin listed in the :attr:`OpenAPIConfig.render_plugins`.


Deprecated ``app`` parameter for ``Response.to_asgi_response`` has been removed
-------------------------------------------------------------------------------

The parameter ``app`` for :meth:`~response.Response.to_asgi_response` has been removed.
If you need access to the app instance inside a custom ``to_asgi_response`` method,
replace the usages of ``app`` with ``request.app``.


Deprecated scope state utilities removed
----------------------------------------

Litestar has previously made available utilities for storing and retrieving data in the ASGI scope state. These
utilities have been removed in version 3.0.0. If you need to store data in the ASGI scope state, you should use do so
using a namespace that is unique to your application and unlikely to conflict with other applications.

The following utilities have been removed:

- ``get_litestar_scope_state``
- ``set_litestar_scope_state``
- ``delete_litestar_scope_state``


Deprecated utility function ``is_sync_or_async_generator`` removed
------------------------------------------------------------------

The utility function ``is_sync_or_async_generator`` has been removed as it is no longer used internally.

If you were relying on this utility, you can define it yourself as follows:

.. code-block:: python

    from inspect import isasyncgenfunction, isgeneratorfunction

    def is_sync_or_async_generator(obj: Any) -> bool:
        return isgeneratorfunction(obj) or isasyncgenfunction(obj)


Removal of semantic HTTP route handler classes
-----------------------------------------------

The semantic ``HTTPRouteHandler`` classes have been removed in favour of functional
decorators. ``route``, ``get``, ``post``, ``patch``, ``put``, ``head`` and ``delete``
are now all decorator functions returning :class:`~.handlers.HTTPRouteHandler`
instances.

As a result, customizing the decorators directly is not possible anymore. Instead, to
use a route handler decorator with a custom route handler class, the ``handler_class``
parameter to the decorator function can be used:

Before:

.. code-block:: python

    class my_get_handler(get):
        ... # custom handler

    @my_get_handler()
    async def handler() -> Any:
        ...

After:

.. code-block:: python

    class MyHTTPRouteHandler(HTTPRouteHandler):
        ... # custom handler


    @get(handler_class=MyHTTPRouteHandler)
    async def handler() -> Any:
        ...


Deprecated ``app`` parameter for ``Response.to_asgi_response`` has been removed
-------------------------------------------------------------------------------

The parameter ``app`` for :meth:`~response.Response.to_asgi_response` has been removed.
If you need access to the app instance inside a custom ``to_asgi_response`` method,
replace the usages of ``app`` with ``request.app``.


Removal of deprecated ``litestar.middleware.exceptions`` module and ``ExceptionHandlerMiddleware``
--------------------------------------------------------------------------------------------------

The deprecated ``litestar.middleware.exceptions`` module and the
``ExceptionHandlerMiddleware`` have been removed. Since ``ExceptionHandlerMiddleware``
has been applied automatically behind the scenes if necessary, no action is required.


Update MessagePack media type to ``application/vnd.msgpack``
------------------------------------------------------------

Change the media type of :attr:`~enums.MediaType.MESSAGEPACK` and
:attr:`~enums.RequestEncodingType.MESSAGEPACK` from ``application/x-msgpack`` to the
newly introduced official ``application/vnd.msgpack``.

https://www.iana.org/assignments/media-types/application/vnd.msgpack


Deprecated ``resolve_`` methods on route handlers
-------------------------------------------------

All ``resolve_`` methods on the route handlers
(e.g. :meth:`~litestar.handlers.HTTPRouteHandler.resolve_response_headers`) have been
deprecated and will be removed in ``4.0``. The attributes can now safely be accessed
directly (e.g. `HTTPRouteHandlers.response_headers`).


Moved routing related methods from ``Router`` to ``Litestar``
-------------------------------------------------------------

:class:`~litestar.router.Router` now only holds route handlers and configuration, while
the actual routing is done in :class:`~litestar.app.Litestar`. With this, several
methods and properties have been moved from ``Router`` to ``Litestar``:

- ``route_handler_method_map``
- ``get_route_handler_map``
- ``routes``
