Configuring schema generation
-----------------------------

OpenAPI schema generation is enabled by default. To configure it you can pass an instance of
:class:`OpenAPIConfig <.openapi.OpenAPIConfig>` to the :class:`Litestar <litestar.app.Litestar>` class using the
``openapi_config`` kwarg:

.. code-block:: python

   from litestar import Litestar
   from litestar.openapi import OpenAPIConfig

   app = Litestar(
       route_handlers=[...], openapi_config=OpenAPIConfig(title="My API", version="1.0.0")
   )



Disabling schema generation
+++++++++++++++++++++++++++

If you wish to disable schema generation and not include the schema endpoints in your API, simply pass ``None`` as the
value for ``openapi_config``:

.. code-block:: python

   from litestar import Litestar

   app = Litestar(route_handlers=[...], openapi_config=None)



Configuring schema generation on a route handler
-------------------------------------------------

By default, an `operation <https://spec.openapis.org/oas/latest.html#operation-object>`_ schema is generated for all route
handlers. You can omit a route handler from the schema by setting ``include_in_schema=False``:

.. code-block:: python

   from litestar import get


   @get(path="/some-path", include_in_schema=False)
   def my_route_handler() -> None: ...

You can also modify the generated schema for the route handler using the following kwargs:


``tags``
    A list of strings that correlate to the `tag specification <https://spec.openapis.org/oas/latest.html#tag-object>`_.

``security``:
    A list of dictionaries that correlate to the
    `security requirements specification <https://spec.openapis.org/oas/latest.html#securityRequirementObject>`_. The
    values for this key are string keyed dictionaries with the values being a list of objects.

``summary``
    Text used for the route's schema *summary* section.

``description``
    Text used for the route's schema *description* section.

``response_description``
    Text used for the route's response schema *description* section.

``operation_class``
    A subclass of :class:`Operation <.openapi.spec.operation.Operation>` which can be used to fully
    customize the `operation object <https://spec.openapis.org/oas/v3.1.0#operation-object>`_ for the handler.

``operation_id``
    A string or callable that returns a string, which servers as an identifier used for the route's schema *operationId*.

``deprecated``
    A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema. Defaults
    to ``False``.

``raises``
    A list of exception classes extending from ``litestar.HttpException``. This list should describe all
    exceptions raised within the route handler's function/method. The Litestar ``ValidationException`` will be added
    automatically for the schema if any validation is involved (e.g. there are parameters specified in the
    method/function). For custom exceptions, a `detail` class property should be defined, which will be integrated
    into the OpenAPI schema. If `detail` isn't specified and the exception's status code matches one
    from `stdlib status code <https://docs.python.org/3/library/http.html#http-status-codes>`_, a generic message
    will be applied.

``responses``
    A dictionary of additional status codes and a description of their expected content.
    The expected content should be based on a Pydantic model describing its structure. It can also include
    a description and the expected media type. For example:

.. note::

    `operation_id` will be prefixed with the method name when function is decorated with `HTTPRouteHandler` and multiple
    `http_method`. Will also be prefixed with path strings used in `Routers` and `Controllers` to make sure id is unique.

.. code-block:: python

   from datetime import datetime
   from typing import Optional

   from pydantic import BaseModel

   from litestar import get
   from litestar.openapi.datastructures import ResponseSpec


   class Item(BaseModel): ...


   class ItemNotFound(BaseModel):
       was_removed: bool
       removed_at: Optional[datetime]


   @get(
       path="/items/{pk:int}",
       responses={
           404: ResponseSpec(
               data_container=ItemNotFound, description="Item was removed or not found"
           )
       },
   )
   def retrieve_item(pk: int) -> Item: ...

You can also specify ``security`` and ``tags`` on higher level of the application, e.g. on a controller, router, or the
app instance itself. For example:

.. code-block:: python

   from litestar import Litestar, get
   from litestar.openapi import OpenAPIConfig
   from litestar.openapi.spec import Components, SecurityScheme, Tag


   @get(
       "/public",
       tags=["public"],
       security=[{}],  # this endpoint is marked as having optional security
   )
   def public_path_handler() -> dict[str, str]:
       return {"hello": "world"}


   @get("/other", tags=["internal"], security=[{"apiKey": []}])
   def internal_path_handler() -> None: ...


   app = Litestar(
       route_handlers=[public_path_handler, internal_path_handler],
       openapi_config=OpenAPIConfig(
           title="my api",
           version="1.0.0",
           tags=[
               Tag(name="public", description="This endpoint is for external users"),
               Tag(name="internal", description="This endpoint is for internal users"),
           ],
           security=[{"BearerToken": []}],
           components=Components(
               security_schemes={
                   "BearerToken": SecurityScheme(
                       type="http",
                       scheme="bearer",
                   )
               },
           ),
       ),
   )


Accessing the OpenAPI schema in code
------------------------------------

The OpenAPI schema is generated during the :class:`Litestar <litestar.app.Litestar>` app's init method. Once init is finished,
its accessible as ``app.openapi_schema``. As such you can always access it inside route handlers, dependencies, etc. by
access the request instance:

.. code-block:: python

   from litestar import Request, get


   @get(path="/")
   def my_route_handler(request: Request) -> dict:
       schema = request.app.openapi_schema
       return schema.dict()


Customizing Pydantic model schemas
----------------------------------

You can customize the OpenAPI schemas generated for pydantic models by following the guidelines in
the `Pydantic docs <https://docs.pydantic.dev/latest/usage/json_schema/>`_.

Additionally, you can affect how pydantic models are translated into OpenAPI ``components`` by settings a special dunder
attribute on the model called ``__schema_name__``:

.. literalinclude:: /examples/openapi/customize_pydantic_model_name.py
    :caption: Customize Components Example
    :language: python


The above will result in an OpenAPI schema object that looks like this:

.. code-block:: json

   {
       "openapi": "3.1.0",
       "info": {"title": "Litestar API", "version": "1.0.0"},
       "servers": [{"url": "/"}],
       "paths": {
           "/id": {
               "get": {
                   "operationId": "Retrieve Id Handler",
                   "responses": {
                       "200": {
                           "description": "Request fulfilled, document follows",
                           "headers": {},
                           "content": {
                               "application/json": {
                                   "schema": {
                                       "$ref": "#/components/schemas/IdContainer"
                                   }
                               }
                           }
                       }
                   },
                   "deprecated": false
               }
           }
       },
       "components": {
           "schemas": {
               "IdContainer": {
                   "properties": {
                       "id": {"type": "string", "format": "uuid", "title": "Id"}
                   },
                   "type": "object",
                   "required": ["id"],
                   "title": "IdContainer"
               }
           }
       }
   }

.. attention::

   If you use multiple pydantic models that use the same name in the schema, you will need to use the `__schema_name__`
   dunder to ensure each has a unique name in the schema, otherwise the schema components will be ambivalent.



Customizing ``Operation`` class
-------------------------------

You can customize the `operation object <https://spec.openapis.org/oas/v3.1.0#operation-object>`_ used for a path in
the generated OpenAPI schemas by creating a subclass of :class:`Operation <.openapi.spec.operation.Operation>`.

This option can be helpful in situations where request data needs to be manually parsed as
Litestar will not know how to create the OpenAPI operation data by default.

.. literalinclude:: /examples/openapi/customize_operation_class.py
    :caption: Customize Components Example
    :language: python


The above example will result in an OpenAPI schema object that looks like this:

.. code-block:: json

    {
        "info": { "title": "Litestar API", "version": "1.0.0" },
        "openapi": "3.0.3",
        "servers": [{ "url": "/" }],
        "paths": {
            "/": {
                "post": {
                    "tags": ["ok"],
                    "summary": "Route",
                    "description": "Requires OK, Returns OK",
                    "operationId": "Route",
                    "requestBody": {
                        "content": {
                            "text": {
                                "schema": { "type": "string", "title": "Body", "example": "OK" }
                            }
                        },
                        "description": "OK is the only accepted value",
                        "required": false
                    },
                    "responses": {
                        "201": {
                            "description": "Document created, URL follows",
                            "headers": {}
                        }
                    },
                    "deprecated": false,
                    "x-codeSamples": [
                        {
                            "lang": "Python",
                            "source": "import requests; requests.get('localhost/example')",
                            "label": "Python"
                        },
                        {
                            "lang": "cURL",
                            "source": "curl -XGET localhost/example",
                            "label": "curl"
                        }
                    ]
                }
            }
        },
        "components": { "schemas": {} }
    }

.. attention::

   OpenAPI Vendor Extension fields need to start with `x-` and should not be processed with the default field name
   converter. To work around this, Litestar will honor an `alias` field provided to the
   `dataclass.field <https://docs.python.org/3/library/dataclasses.html#dataclasses.field>`_ metadata
   when generating the field name in the schema.
