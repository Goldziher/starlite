OpenAPI UI Plugins
------------------

.. versionadded:: 2.8.0

OpenAPI UI Plugins are designed to allow easy integration with your OpenAPI UI framework of choice. These plugins
facilitate the creation of interactive, user-friendly API documentation, making it easier for developers and end-users
to understand and interact with your API.

Litestar maintains and ships with UI plugins for a range of popular popular OpenAPI documentation tools:

- `Scalar <https://github.com/scalar/scalar/>`_
- `RapiDoc <https://rapidocweb.com/>`_
- `ReDoc <https://redocly.com/>`_
- `Stoplight Elements <https://stoplight.io/open-source/elements>`_
- `Swagger UI <https://swagger.io/tools/swagger-ui/>`_
- `YAML <https://yaml.org/>`_

Each plugin is easily configurable, allowing developers to customize aspects like version, paths, CSS and JavaScript
resources.


Using OpenAPI UI Plugins
------------------------

Using OpenAPI UI Plugins is as simple as importing the plugin, instantiating it, and adding it to the OpenAPIConfig.

.. tab-set::

    .. tab-item:: scalar
        :sync: scalar

        .. literalinclude:: /examples/openapi/plugins/scalar_simple.py
            :language: python

    .. tab-item:: rapidoc
        :sync: rapidoc

        .. literalinclude:: /examples/openapi/plugins/rapidoc_simple.py
            :language: python

    .. tab-item:: redoc
        :sync: redoc

        .. literalinclude:: /examples/openapi/plugins/redoc_simple.py
            :language: python

    .. tab-item:: stoplight
        :sync: stoplight

        .. literalinclude:: /examples/openapi/plugins/stoplight_simple.py
            :language: python

    .. tab-item:: swagger
        :sync: swagger

        .. literalinclude:: /examples/openapi/plugins/swagger_ui_simple.py
            :language: python

    .. tab-item:: yaml
        :sync: yaml

        .. literalinclude:: /examples/openapi/plugins/yaml_simple.py
            :language: python

    .. tab-item:: multiple

        .. literalinclude:: /examples/openapi/plugins/serving_multiple_uis.py
            :caption: Any combination of UIs can be served.
            :language: python

Configuring OpenAPI UI Plugins
------------------------------

Each plugin can be tailored to meet your unique requirements by passing options at instantiation. For full details on
each plugin's options, see the :doc:`API Reference </reference/openapi/plugins>`.

All plugins support:

- ``path``: Each plugin has its own default, e.g., ``/rapidoc`` for RapiDoc. This can be overridden to serve the UI at
  a different path.
- ``media_type``: The default media type for the plugin, typically the default is ``text/html``.
- ``favicon``: A string that should be a valid ``<link>`` tag, e.g.,
  ``<link rel="icon" href="https://example.com/favicon.ico">``.
- ``style``: A string that should be a valid ``<style>`` tag, e.g., ``<style>body { margin: 0; padding: 0; }``</style>.``

Most plugins support the following additional options:

- ``version``: The version of the UIs JS and (in some cases) CSS bundle to use. We use the ``version`` to construct the
  URL to retrieve the bundle from ``unpkg``, e.g., ``https://unpkg.com/rapidoc@<version>/dist/rapidoc-min.js``
- ``js_url``: The URL to the JS bundle. If provided, this will override the ``version`` option.
- ``css_url``: The URL to the CSS bundle. If provided, this will override the ``version`` option.

Here's some example plugin configurations:

.. tab-set::

    .. tab-item:: scalar
        :sync: scalar

        .. literalinclude:: /examples/openapi/plugins/scalar_config.py
            :language: python

    .. tab-item:: rapidoc
        :sync: rapidoc

        .. literalinclude:: /examples/openapi/plugins/rapidoc_config.py
            :language: python

    .. tab-item:: redoc
        :sync: redoc

        .. literalinclude:: /examples/openapi/plugins/redoc_config.py
            :language: python

    .. tab-item:: stoplight
        :sync: stoplight

        .. literalinclude:: /examples/openapi/plugins/stoplight_config.py
            :language: python

    .. tab-item:: swagger
        :sync: swagger

        .. literalinclude:: /examples/openapi/plugins/swagger_ui_config.py
            :language: python

Configuring the OpenAPI Root Path
---------------------------------

The OpenAPI root path is the path at which the OpenAPI representations are served. By default, this is ``/schema``.
This can be changed by setting the :attr:`OpenAPIConfig.path` attribute.

In the following example, we configure the OpenAPI root path to be ``/docs``:

.. literalinclude:: /examples/openapi/customize_path.py
    :language: python

This will result in any of the OpenAPI endpoints being served at ``/docs`` instead of ``/schema``, e.g.,
``/docs/openapi.json``.

Building your own OpenAPI UI Plugin
-----------------------------------

If Litestar does not have built-in support for your OpenAPI UI framework of choice, you can easily create your own
plugin by subclassing :class:`OpenAPIRenderPlugin` and implementing the :meth:`OpenAPIRenderPlugin.render` method.

To demonstrate building a custom plugin, we'll look at a plugin very similar to the :class:`ScalarRenderPlugin` that is
maintained by Litestar. Here's the finished product:

.. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python

Class definition
~~~~~~~~~~~~~~~~

The class ``ScalarRenderPlugin`` inherits from :class:`OpenAPIRenderPlugin`:

.. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 10

``__init__`` Constructor
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 11-22

We support configuration via the following arguments:

- ``version``: Specifies the version of RapiDoc to use.
- ``js_url``: Custom URL to the RapiDoc JavaScript bundle.
- ``css_url``: Custom URL to the RapiDoc CSS bundle.
- ``path``: The URL path where the RapiDoc UI will be served.
- ``**kwargs``: Captures additional arguments to pass to the superclass.

And we construct a url for the Scalar JavaScript bundle if one is not provided:

.. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 20

``render()``
~~~~~~~~~~~~

.. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 24

Finally we define the ``render`` method, which is called by Litestar to render the UI. It receives the a
:class:`Request` object and the ``openapi_schema`` as a dictionary.

Inside the ``render`` method, we construct the HTML to render the UI, and return it as a string.

- ``head``: Defines the HTML ``<head>`` section, including the title from ``openapi_schema``, any additional styles
  (``self.style``), the favicon and custom style sheet if one is provided:

  .. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 25-35

- ``body``: Constructs the HTML ``<body>``, including a link to the OpenAPI JSON, and the JavaScript bundle:

  .. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 37-43

- Finally, returns a complete HTML document (as a byte string), combining head and body.

  .. literalinclude:: /examples/openapi/plugins/custom_plugin.py
    :language: python
    :lines: 45-51

Interacting with the ``Router``
-------------------------------

An instance of :class:`Router` is used to serve the OpenAPI endpoints and is made available to plugins via the
:meth:`OpenAPIRenderPlugin.receive_router` method.

This can be used for a variety of purposes, including adding additional routes to the ``Router``.

.. literalinclude:: /examples/openapi/plugins/receive_router.py
    :language: python

OAuth2 in Swagger UI
--------------------

When using Swagger, OAuth2 settings can be configured via the :paramref:`~.openapi.plugins.SwaggerRenderPlugin.init_oauth` param of
:meth:`SwaggerRenderPlugin <litestar.openapi.plugins.SwaggerRenderPlugin.__init__>`, which can be set to a dictionary
containing the parameters described in the Swagger UI documentation for OAuth2
`here <https://swagger.io/docs/open-source-tools/swagger-ui/usage/oauth2/>`_.

With that, you can preset your clientId or enable PKCE support.

.. literalinclude:: /examples/openapi/plugins/swagger_ui_oauth.py
    :language: python

Customizing the OpenAPI UI
--------------------------

Style and behavior of the OpenAPI UI can be customized by overriding the default ``css_url`` and ``js_url`` attributes
on the render plugin class, for example:

.. literalinclude:: /examples/openapi/plugins/scalar_customized.py
    :language: python

To learn more about customizing the ``Scalar`` UI, see the `Scalar documentation <https://docs.scalar.com/>`_.

CDN and offline file support
----------------------------

Each plugin supports ``js_url`` and ``css_url`` attributes, which can be used to specify a custom URL to the JavaScript.
These can be used to serve the JavaScript and CSS from a CDN, or to serve the files from a local directory.
