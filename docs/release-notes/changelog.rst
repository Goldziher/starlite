:orphan:

2.x Changelog
=============

.. changelog:: 2.8.1
    :date: 2024-04-08

    .. change:: ASGI lifespan msg after lifespan context exception
        :type: bugfix
        :pr: 3315

        An exception raised within an asgi lifespan context manager would result in a "lifespan.startup.failed" message

        This PR modifies `ASGIRouter.lifespan()` so that it sends a shutdown failure message if we've already confirmed
        startup.

    .. change:: Fix when pydantic==1.10 is installed
        :type: bugfix
        :pr: 3335
        :issue: 3334

        This PR fixes a bug introduced in #3296 where it failed to take into account that the `pydantic_v2` variable could be `Empty`.

    .. change:: OpenAPI router and controller on same app.
        :type: bugfix
        :pr: 3338
        :issue: 3337

        Fixes an `ImproperlyConfiguredException` where an app that explicitly registers an `OpenAPIController` on the application, and implicitly uses the OpenAPI router via the `OpenAPIConfig` object. This was caused by the two different handlers being given the same name as defined in `litestar.constants`.

        PR adds a distinct name for use by the handler that serves `openapi.json` on the controller.

.. changelog:: 2.8.0
    :date: 2024-04-05

    .. change:: Unique schema names for nested models (#3134)
        :type: bugfix
        :pr: 3136
        :issue: 3134

        Fixes an issue where nested models beyond the ``max_nested_depth`` would not have
        unique schema names in the OpenAPI documentation. The fix appends the nested
        model's name to the ``unique_name`` to differentiate it from the parent model.

    .. change:: Add ``path`` parameter to Litestar application class
        :type: feature
        :pr: 3314

        Exposes :paramref:`~.app.Litestar.parameter` at :class:`~.app.Litestar` application class level

    .. change:: Remove duplicate ``rich-click`` config options
        :type: bugfix
        :pr: 3274

        Removes duplicate config options from click cli

    .. change:: Fix Pydantic ``json_schema_extra`` examples.
        :type: bugfix
        :pr: 3281
        :issue: 3277

        Fixes a regression introduced in ``2.7.0`` where an example for a field provided in Pydantic's
        ``Field.json_schema_extra`` would cause an error.

    .. change:: Set default on schema from :class:`~.typing.FieldDefinition`
        :type: bugfix
        :pr: 3280
        :issue: 3278

        Consider the following:

        .. code-block:: python

            def get_foo(foo_id: int = 10) -> None:
                ...

        In such cases, no :class:`~.params.KwargDefinition` is created since there is no metadata provided via
        ``Annotated``. The default is still parsed, and set on the generated ``FieldDefinition``,
        however the ``SchemaCreator`` currently only considers defaults that are set on ``KwargDefinition``.

        So in such cases, we should fallback to the default set on the ``FieldDefinition`` if there is a valid
        default value.

    .. change:: Custom types cause serialisation error in exception response with non-JSON media-type
        :type: bugfix
        :pr: 3284
        :issue: 3192

        Fixes a bug when using a non-JSON media type (e.g., ``text/plain``),
        :class:`~.exceptions.http_exceptions.ValidationException`'s would not get serialized properly because they
        would ignore custom ``type_encoders``.

    .. change:: Ensure default values are always represented in schema for dataclasses and :class:`msgspec.Struct`\ s
        :type: bugfix
        :pr: 3285
        :issue: 3201

        Fixes a bug that would prevent default values for dataclasses and ``msgspec.Struct`` s to be included in the
        OpenAPI schema.

    .. change:: Pydantic v2 error handling/serialization when for non-Pydantic exceptions
        :type: bugfix
        :pr: 3286
        :issue: 2365

        Fixes a bug that would cause a :exc:`TypeError` when non-Pydantic errors are raised during Pydantic's
        validation process while using DTOs.

    .. change:: Fix OpenAPI schema generation for paths with path parameters of different types on the same path
        :type: bugfix
        :pr: 3293
        :issue: 2700

        Fixes a bug that would cause no OpenAPI schema to be generated for paths with path
        parameters that only differ on the path parameter type, such as ``/{param:int}``
        and ``/{param:str}``. This was caused by an internal representation issue in
        Litestar's routing system.

    .. change:: Document unconsumed path parameters
        :type: bugfix
        :pr: 3295
        :issue: 3290

        Fixes a bug where path parameters not consumed by route handlers would not be included in the OpenAPI schema.

        This could/would not include the ``{param}`` in the schema, yet it is still required to be passed
        when calling the path.

    .. change:: Allow for console output to be silenced
        :type: feature
        :pr: 3180

        Introduces optional environment variables that allow customizing the "Application" name displayed
        in the console output and suppressing the initial ``from_env`` or the ``Rich`` info table at startup.

        Provides flexibility in tailoring the console output to better integrate Litestar into larger applications
        or CLIs.

    .. change:: Add flash plugin
        :type: feature
        :pr: 3145
        :issue: 1455

        Adds a flash plugin akin to Django or Flask that uses the request state

    .. change:: Use memoized :paramref:`~.handlers.HTTPRouteHandler.request_class` and :paramref:`~.handlers.HTTPRouteHandler.response_class` values
        :type: feature
        :pr: 3205

        Uses memoized ``request_class`` and ``response_class`` values

    .. change:: Enable codegen backend by default
        :type: feature
        :pr: 3215

        Enables the codegen backend for DTOs introduced in https://github.com/litestar-org/litestar/pull/2388 by default.

    .. change:: Added precedence of CLI parameters over envs
        :type: feature
        :pr: 3190
        :issue: 3188

        Adds precedence of CLI parameters over environment variables.
        Before this change, environment variables would take precedence over CLI parameters.

        Since CLI parameters are more explicit and are set by the user,
        they should take precedence over environment variables.

    .. change:: Only print when terminal is ``TTY`` enabled
        :type: feature
        :pr: 3219

        Sets ``LITESTAR_QUIET_CONSOLE`` and ``LITESTAR_APP_NAME`` in the autodiscovery function.
        Also prevents the tabular console output from printing when the terminal is not ``TTY``

    .. change:: Support ``schema_extra`` in :class:`~.openapi.spec.parameter.Parameter` and `Body`
        :type: feature
        :pr: 3204

        Introduces a way to modify the generated OpenAPI spec by adding a ``schema_extra`` parameter to the
        Parameter and Body classes. The ``schema_extra`` parameter accepts a ``dict[str, Any]`` where the keys correspond
        to the keyword parameter names in Schema, and the values are used to override items in the
        generated Schema object.

        Provides a convenient way to customize the OpenAPI documentation for inbound parameters.

    .. change:: Add :class:`typing.TypeVar` expansion
        :type: feature
        :pr: 3242

        Adds a method for TypeVar expansion on registration
        This allows the use of generic route handler and generic controller without relying on forward references.

    .. change:: Add ``LITESTAR_`` prefix before ``WEB_CONCURRENCY`` env option
        :type: feature
        :pr: 3227

        Adds ``LITESTAR_`` prefix before the ``WEB_CONCURRENCY`` environment option

    .. change:: Warn about ambiguous default values in parameter specifications
        :type: feature
        :pr: 3283

        As discussed in https://github.com/litestar-org/litestar/pull/3280#issuecomment-2026878325,
        we want to warn about, and eventually disallow specifying parameter defaults in two places.

        To achieve this, 2 warnings are added:

        - A deprecation warning if a default is specified when using
          ``Annotated``: ``param: Annotated[int, Parameter(..., default=1)]`` instead of
          ``param: Annotated[int, Parameter(...)] = 1``
        - An additional warning in the above case if two default values are specified which do not match in value:
          ``param: Annotated[int, Parameter(..., default=1)] = 2``

        In a future version, the first one should result in an exception at startup, preventing both of these scenarios.

    .. change:: Support declaring :class:`~.dto.field.DTOField` via ``Annotated``
        :type: feature
        :pr: 3289
        :issue: 2351

        Deprecates passing :class:`~.dto.field.DTOField` via ``[pydantic]`` extra.

    .. change:: Add "TRACE" to HttpMethod enum
        :type: feature
        :pr: 3294

        Adds the ``TRACE`` HTTP method to :class:`~.enums.HttpMethod` enum

    .. change:: Pydantic DTO non-instantiable types
        :type: feature
        :pr: 3296

        Simplifies the type that is applied to DTO transfer models for certain Pydantic field types.
        It addresses ``JsonValue``, ``EmailStr``, ``IPvAnyAddress``/``IPvAnyNetwork``/``IPvAnyInterface`` types by
        using appropriate :term:`type annotations <annotation>` on the transfer models to ensure compatibility with
        :doc:`msgspec:index` serialization and deserialization.

.. changelog:: 2.7.1
    :date: 2024-03-22

    .. change:: replace TestClient.__enter__ return type with Self
        :type: bugfix
        :pr: 3194

        ``TestClient.__enter__`` and ``AsyncTestClient.__enter__`` return ``Self``.
        If you inherit ``TestClient``, its ``__enter__`` method should return derived class's instance
        unless override the method. ``Self`` is a more flexible return type.

    .. change:: use the full path for fetching openapi.json
        :type: bugfix
        :pr: 3196
        :issue: 3047

        This specifies the ``spec-url`` and ``apiDescriptionUrl`` of Rapidoc, and Stoplight Elements as absolute
        paths relative to the root of the site.

        This ensures that both of the send the request for the JSON of the OpenAPI schema to the right endpoint.

    .. change:: JSON schema ``examples`` were OpenAPI formatted
        :type: bugfix
        :pr: 3224
        :issue: 2849

        The generated ``examples`` in *JSON schema* objects were formatted as:

        .. code-block:: json

            "examples": {
              "some-id": {
                "description": "Lorem ipsum",
                "value": "the real beef"
              }
           }

        However, above is OpenAPI example format, and must not be used in JSON schema
        objects. Schema objects follow different formatting:

        .. code-block:: json

            "examples": [
              "the real beef"
           ]

        * Explained in `APIs You Won't Hate blog post <https://medium.com/apis-you-wont-hate/openapi-v3-1-and-json-schema-2019-09-6862cf3db959>`_.
        * `Schema objects spec <https://spec.openapis.org/oas/v3.1.0#schema-object>`_
        * `OpenAPI example format spec <https://spec.openapis.org/oas/v3.1.0#example-object>`_.

        This is referenced at least from parameters, media types and components.

        The technical change here is to define ``Schema.examples`` as ``list[Any]`` instead
        of ``list[Example]``. Examples can and must still be defined as ``list[Example]``
        for OpenAPI objects (e.g. ``Parameter``, ``Body``) but for JSON schema ``examples``
        the code now internally generates/converts ``list[Any]`` format instead.

        Extra confusion here comes from the OpenAPI 3.0 vs OpenAPI 3.1 difference.
        OpenAPI 3.0 only allowed ``example`` (singular) field in schema objects.
        OpenAPI 3.1 supports the full JSON schema 2020-12 spec and so ``examples`` array
        in schema objects.

        Both ``example`` and ``examples`` seem to be supported, though the former is marked
        as deprecated in the latest specs.

        This can be tested over at https://editor-next.swagger.io by loading up the
        OpenAPI 3.1 Pet store example. Then add ``examples`` in ``components.schemas.Pet``
        using the both ways and see the Swagger UI only render the example once it's
        properly formatted (it ignores is otherwise).

    .. change:: queue_listener handler for Python >= 3.12
        :type: bugfix
        :pr: 3185
        :issue: 2954

        - Fix the ``queue_listener`` handler for Python 3.12

        Python 3.12 introduced a new way to configure ``QueueHandler`` and ``QueueListener`` via
        ``logging.config.dictConfig()``. As described in the
        `logging documentation <https://docs.python.org/3/library/logging.config.html#configuring-queuehandler-and-queuelistener>`_.

        The listener still needs to be started & stopped, as previously.
        To do so, we've introduced ``LoggingQueueListener``.

        And as stated in the doc:
        * Any custom queue handler and listener classes will need to be defined with the same initialization signatures
        as `QueueHandler <https://docs.python.org/3/library/logging.handlers.html#logging.handlers.QueueHandler>`_ and
        `QueueListener <https://docs.python.org/3/library/logging.handlers.html#logging.handlers.QueueListener>`_.

    .. change:: extend openapi meta collected from domain models
        :type: bugfix
        :pr: 3237
        :issue: 3232

        :class:`~litestar.typing.FieldDefinition` s pack any OpenAPI metadata onto a ``KwargDefinition`` instance when
        types are parsed from domain models.

        When we produce a DTO type, we transfer this meta from the `KwargDefinition` to a `msgspec.Meta` instance,
        however so far this has only included constraints, not attributes such as descriptions, examples and title.

        This change ensures that we transfer the openapi meta for the complete intersection of fields that exist on b
        oth `KwargDefinition` and `Meta`.

    .. change:: kwarg ambiguity exc msg for path params
        :type: bugfix
        :pr: 3261

        Fixes the way we construct the exception message when there is a kwarg ambiguity detected for path parameters.

.. changelog:: 2.7.0
    :date: 2024-03-10

    .. change:: missing cors headers in response
        :type: bugfix
        :pr: 3179
        :issue: 3178

        Set CORS Middleware headers as per spec.
        Addresses issues outlined on https://github.com/litestar-org/litestar/issues/3178

    .. change:: sending empty data in sse in js client
        :type: bugfix
        :pr: 3176

        Fix an issue with SSE where JavaScript clients fail to receive an event without data.
        The `spec <https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream>`_ is
        not clear in whether or not an event without data is ok.
        Considering the EventSource "client" is not ok with it, and that it's so easy DX-wise to make the mistake not
        explicitly sending it, this change fixes it by defaulting to the empty-string

    .. change:: Support ``ResponseSpec(..., examples=[...])``
        :type: feature
        :pr: 3100
        :issue: 3068

        Allow defining custom examples for the responses via ``ResponseSpec``.
        The examples set this way are always generated locally, for each response:
        Examples that go within the schema definition cannot be set by this.

        .. code-block:: json

            {
            "paths": {
                "/": {
                "get": {
                    "responses": {
                    "200": {
                        "content": {
                        "application/json": {
                            "schema": {},
                            "examples": "..."}}
                        }}
                    }}
                }
            }


    .. change:: support "+json"-suffixed response media types
        :type: feature
        :pr: 3096
        :issue: 3088

        Automatically encode responses with media type of the form ``application/<something>+json`` as json.

    .. change:: Allow reusable ``Router`` instances
        :type: feature
        :pr: 3103
        :issue: 3012

        It was not possible to re-attach a router instance once it was attached. This
        makes that possible.

        The router instance now gets deepcopied when it's registered to another router.

        The application startup performance gets a hit here, but the same approach is
        already used for controllers and handlers, so this only harmonizes the
        implementation.

    .. change:: only display path in ``ValidationException``\ s
        :type: feature
        :pr: 3064
        :issue: 3061

        Fix an issue where ``ValidationException`` exposes the full URL in the error response, leaking internal IP(s) or other similar infra related information.

    .. change:: expose ``request_class`` to other layers
        :type: feature
        :pr: 3125

        Expose ``request_class`` to other layers

    .. change:: expose ``websocket_class``
        :type: feature
        :pr: 3152

        Expose ``websocket_class`` to other layers

    .. change:: Add ``type_decoders`` to Router and route handlers
        :type: feature
        :pr: 3153

        Add ``type_decoders`` to ``__init__`` method for handler, routers and decorators to keep consistency with ``type_encoders`` parameter

    .. change:: Pass ``type_decoders`` in ``WebsocketListenerRouteHandler``
        :type: feature
        :pr: 3162

        Pass ``type_decoders`` to parent's ``__init__`` in ``WebsocketListenerRouteHandler`` init, otherwise ``type_decoders`` will be ``None``
        replace params order in docs, ``__init__`` (`decoders` before `encoders`)

    .. change:: 3116 enhancement session middleware
        :type: feature
        :pr: 3127
        :issue: 3116

        For server side sessions, the session id is now generated before the route handler. Thus, on first visit, a session id will be available inside the route handler's scope instead of afterwards
        A new abstract method ``get_session_id`` was added to ``BaseSessionBackend`` since this method will be called for both ClientSideSessions and ServerSideSessions. Only for ServerSideSessions it will return an actual id.
        Using ``request.set_session(...)`` will return the session id for ServerSideSessions and None for ClientSideSessions
        The session auth MiddlewareWrapper now refers to the Session Middleware via the configured backend, instead of it being hardcoded

    .. change:: make random seed for openapi example generation configurable
        :type: feature
        :pr: 3166

        Allow random seed used for generating the examples in the OpenAPI schema (when ``create_examples`` is set to ``True``) to be configured by the user.
        This is related to https://github.com/litestar-org/litestar/issues/3059 however whether this change is enough to close that issue or not is not confirmed.

    .. change:: generate openapi components schemas in a deterministic order
        :type: feature
        :pr: 3172

        Ensure that the insertion into the ``Components.schemas`` dictionary of the OpenAPI spec will be in alphabetical order (based on the normalized name of the ``Schema``).


.. changelog:: 2.6.3
    :date: 2024-03-04

    .. change:: Pydantic V1 schema generation for PrivateAttr in GenericModel
        :type: bugfix
        :pr: 3161
        :issue: 3150

        Fixes a bug that caused a ``NameError`` when a Pydantic V1 ``GenericModel`` has a private attribute of which the type annotation cannot be resolved at the time of schema generation.


.. changelog:: 2.6.2
    :date: 2024/03/02

    .. change:: DTO msgspec meta constraints not being included in transfer model
        :type: bugfix
        :pr: 3113
        :issue: 3026

        Fix an issue where msgspec constraints set in ``msgspec.Meta`` would not be
        honoured by the DTO.

        In the given example, the ``min_length=3`` constraint would be ignored by the
        model generated by ``MsgspecDTO``.

        .. code-block:: python

            from typing import Annotated

            import msgspec
            from litestar import post, Litestar
            from litestar.dto import MsgspecDTO

            class Request(msgspec.Struct):
                foo: Annotated[str, msgspec.Meta(min_length=3)]

            @post("/example/", dto=MsgspecDTO[Request])
            async def example(data: Request) -> Request:
                return data

        Constraints like these are now transferred.

        Two things to note are:

        - For DTOs with ``DTOConfig(partial=True)`` we cannot transfer the length
          constraints as they are only supported on fields that as subtypes of ``str``,
          ``bytes`` or a collection type, but ``partial=True`` sets all fields as
          ``T | UNSET``
        - For the ``PiccoloDTO``, fields which are not required will also drop the
          length constraints. A warning about this will be raised here.

    .. change:: Missing control header for static files
        :type: bugfix
        :pr: 3131
        :issue: 3129

        Fix an issue where a ``cache_control`` that is set on a router created by
        ``create_static_files_router`` wasn't passed to the generated handler

    .. change:: Fix OpenAPI schema generation for Pydantic v2 constrained ``Secret`` types
        :type: bugfix
        :pr: 3149
        :issue: 3148

        Fix schema generation for ``pydantic.SecretStr`` and ``pydantic.SecretBytes``
        which, when constrained, would not be recognised as such with Pydantic V2 since
        they're not subtypes of their respective bases anymore.

    .. change:: Fix OpenAPI schema generation for Pydantic private attributes
        :type: bugfix
        :pr: 3151
        :issue: 3150

        Fix a bug that caused a :exc:`NameError` when trying to resolve forward
        references in Pydantic private fields.

        Although private fields were respected excluded from the schema, it was still
        attempted to extract their type annotation. This was fixed by not relying on
        ``typing.get_type_hints`` to get the type information, but instead using
        Pydantic's own APIs, allowing us to only extract information about the types of
        relevant fields.

    .. change:: OpenAPI description not set for UUID based path parameters in OpenAPI
        :type: bugfix
        :pr: 3118
        :issue: 2967

        Resolved a bug where the description was not set for UUID-based path
        parameters in OpenAPI due to the reason mentioned in the issue.

    .. change:: Fix ``RedisStore`` client created with ``with_client`` unclosed
        :type: bugfix
        :pr: 3111
        :issue: 3083

        Fix a bug where, when a :class:`~litestar.stores.redis.RedisStore` was created
        with the :meth:`~litestar.stores.redis.RedisStore.with_client` method, that
        client wasn't closed explicitly


.. changelog:: 2.6.1
    :date: 2024/02/14

    .. change:: SQLAlchemy: Use `IntegrityError` instead of deprecated `ConflictError`
        :type: bugfix
        :pr: 3094

        Updated the repository to return ``IntegrityError`` instead of the now
        deprecated ``ConflictError``

    .. change:: Remove usage of deprecated `static_files` property
        :type: bugfix
        :pr: 3087

        Remove the usage of the deprecated ``Litestar.static_files_config`` in
        ``Litestar.__init__``.

    .. change:: Sessions: Fix cookie naming for short cookies
        :type: bugfix
        :pr: 3095
        :issue: 3090

        Previously, cookie names always had a suffix of the form ``"-{i}"`` appended to
        them. With this change, the suffix is omitted if the cookie is short enough
        (< 4 KB) to not be split into multiple chunks.

    .. change:: Static files: Fix path resolution for windows
        :type: bugfix
        :pr: 3102

        Fix an issue with the path resolution on Windows introduced in
        https://github.com/litestar-org/litestar/pull/2960 that would lead to 404s

    .. change:: Fix logging middleware with structlog causes application to return a ``500`` when request body is malformed
        :type: bugfix
        :pr: 3109
        :issue: 3063

        Gracefully handle malformed request bodies during parsing when using structlog;
        Instead of erroring out and returning a ``500``, the raw body is now being used
        when an error occurs during parsing

    .. change:: OpenAPI: Generate correct response schema for ``ResponseSpec(None)``
        :type: bugfix
        :pr: 3098
        :issue: 3069

        Explicitly declaring ``responses={...: ResponseSpec(None)}`` used to generate
        OpenAPI a ``content`` property, when it should be omitted.

    .. change:: Prevent exception handlers from extracting details from non-Litestar exceptions
        :type: bugfix
        :pr: 3106
        :issue: 3082

        Fix a bug where exception classes that had a ``status_code`` attribute would be
        treated as Litestar exceptions and details from them would be extracted and
        added to the exception response.

.. changelog:: 2.6.0
    :date: 2024/02/06

    .. change:: Enable disabling configuring ``root`` logger within ``LoggingConfig``
        :type: feature
        :pr: 2969

        The option :attr:`~litestar.logging.config.LoggingConfig.configure_root_logger` was
        added to :class:`~litestar.logging.config.LoggingConfig` attribute. It is enabled by
        default to not implement a breaking change.

        When set to ``False`` the ``root`` logger will not be modified for ``logging``
        or ``picologging`` loggers.

    .. change:: Simplified static file handling and enhancements
        :type: feature
        :pr: 2960
        :issue: 2629

        Static file serving has been implemented with regular route handlers instead of
        a specialised ASGI app. At the moment, this is complementary to the usage of
        :class:`~litestar.static_files.StaticFilesConfig` to maintain backwards
        compatibility.

        This achieves a few things:

        - Fixes https://github.com/litestar-org/litestar/issues/2629
        - Circumvents special casing needed in the routing logic for the static files app
        - Removes the need for a ``static_files_config`` attribute on the app
        - Removes the need for a special :meth:`~litestar.app.Litestar.url_for_static_asset`
          method on the app since `route_reverse` can be used instead

        Additionally:

        - Most router options can now be passed to the
          :func:`~litestar.static_files.create_static_files_router`, allowing further
          customisation
        - A new ``resolve_symlinks`` flag has been added, defaulting to ``True`` to keep
          backwards compatibility

        **Usage**

        Instead of

        .. code-block:: python

            app = Litestar(
                static_files_config=[StaticFilesConfig(path="/static", directories=["some_dir"])]
            )


        You can now simply use

        .. code-block:: python

            app = Litestar(
                route_handlers=[
                    create_static_files_router(path="/static", directories=["some_dir"])
                ]
            )

        .. seealso::
            :doc:`/usage/static-files`


    .. change:: Exclude Piccolo ORM columns with ``secret=True`` from ``PydanticDTO`` output
        :type: feature
        :pr: 3030

        For Piccolo columns with ``secret=True`` set, corresponding ``PydanticDTO``
        attributes will be marked as ``WRITE_ONLY`` to prevent the column being included
        in ``return_dto``


    .. change:: Allow discovering registered plugins by their fully qualified name
        :type: feature
        :pr: 3027

        `PluginRegistryPluginRegistry`` now supports retrieving a plugin by its fully
        qualified name.


    .. change:: Support externally typed classes as dependency providers
        :type: feature
        :pr: 3066
        :issue: 2979

        - Implement a new :class:`~litestar.plugins.DIPlugin` class that allows the
          generation of signatures for arbitrary types where their signature cannot be
          extracted from the type's ``__init__`` method
        - Implement ``DIPlugin``\ s for Pydantic and Msgspec to allow using their
          respective modelled types as dependency providers. These plugins will be
          registered by default

    .. change:: Add structlog plugin
        :type: feature
        :pr: 2943

        A Structlog plugin to make it easier to configure structlog in a single place.

        The plugin:

        - Detects if a logger has ``setLevel`` before calling
        - Set even message name to be init-cap
        - Add ``set_level`` interface to config
        - Allows structlog printer to detect if console is TTY enabled. If so, a
          Struglog color formatter with Rich traceback printer is used
        - Auto-configures stdlib logger to use the structlog logger

    .. change:: Add reload-include and reload-exclude to CLI run command
        :type: feature
        :pr: 2973
        :issue: 2875

        The options ``reload-exclude`` and ``reload-include`` were added to the CLI
        ``run`` command to explicitly in-/exclude specific paths from the reloading
        watcher.


.. changelog:: 2.5.5
    :date: 2024/02/04

    .. change:: Fix scope ``state`` key handling
        :type: bugfix
        :pr: 3070

        Fix a regression introduced in #2751 that would wrongfully assume the ``state``
        key is always present within the ASGI Scope. This is *only* the case when the
        Litestar root application is invoked first, since we enforce such a key there,
        but the presence of that key is not actually guaranteed by the ASGI spec and
        some servers, such as hypercorn, do not provide it.


.. changelog:: 2.5.4
    :date: 2024/01/31

    .. change:: Handle ``KeyError`` when `root_path` is not present in ASGI scope
        :type: bugfix
        :pr: 3051

        Nginx Unit ASGI server does not set "root_path" in the ASGI scope, which is
        expected as part of the changes done in #3039. This PR fixes the assumption that
        the key is always present and instead tries to optionally retrieve it.

        .. code-block::

            KeyError on GET /
            'root_path'

    .. change:: ServerSentEvent typing error
        :type: bugfix
        :pr: 3048

        fixes small typing error:

        .. code-block::

            error: Argument 1 to "ServerSentEvent" has incompatible type "AsyncIterable[ServerSentEventMessage]"; expected "str | bytes | Iterable[str | bytes] | Iterator[str | bytes] | AsyncIterable[str | bytes] | AsyncIterator[str | bytes]"  [arg-type]

        inside ``test_sse`` there was a ``Any`` I changed to trigger the test then solved it.


.. changelog:: 2.5.3
    :date: 2024/01/29

    .. change:: Handle diverging ASGI ``root_path`` behaviour
        :type: bugfix
        :pr: 3039
        :issue: 3041

        Uvicorn `0.26.0 <https://github.com/encode/uvicorn/releases/tag/0.26.0>`_
        introduced a breaking change in its handling of the ASGI ``root_path`` behaviour,
        which, while adhering to the spec, diverges from the interpretation of other
        ASGI servers of this aspect of the spec (e.g. hypercorn and daphne do not follow
        uvicorn's interpretation as of today). A fix was introduced that ensures
        consistent behaviour of applications in any case.

.. changelog:: 2.5.2
    :date: 2024/01/27

    .. change:: Ensure ``MultiDict`` and ``ImmutableMultiDict`` copy methods return the instance's type
        :type: bugfix
        :pr: 3009
        :issue: 2549

        Ensure :class:`~litestar.datastructures.MultiDict` and
        :class:`~litestar.datastructures.ImmutableMultiDict` copy methods return a new
        instance of ``MultiDict`` and ``ImmutableMultiDict``. Previously, these would
        return a :class:`multidict.MultiDict` instance.

    .. change:: Ensure ``exceptiongroup`` is installed on Python 3.11
        :type: bugfix
        :pr: 3035
        :issue: 3029

        Add the `exceptiongroup <https://github.com/agronholm/exceptiongroup>`_ package
        as a required dependency on Python ``<3.11`` (previously ``<3.10``) as a
        backport of `Exception Groups <https://docs.python.org/3/library/exceptions.html#exception-groups>`_


.. changelog:: 2.5.1
    :date: 2024/01/18

    .. change:: Fix OpenAPI schema generation for Union of multiple ``msgspec.Struct``\ s and ``None``
        :type: bugfix
        :pr: 2982
        :issue: 2971

        The following code would raise a :exc:`TypeError`

        .. code-block:: python

            import msgspec

            from litestar import get
            from litestar.testing import create_test_client


            class StructA(msgspec.Struct):
                pass


            class StructB(msgspec.Struct):
                pass


            @get("/")
            async def handler() -> StructA | StructB | None:
                return StructA()


    .. change:: Fix misleading error message for missing dependencies provide by a package extra
        :type: bugfix
        :pr: 2921

        Ensure that :exc:`MissingDependencyException` includes the correct name of the
        package to install if the package name differs from the Litestar package extra.
        (e.g. ``pip install litestar[jinja]`` vs ``pip install jinja2``). Previously the
        exception assumed the same name for both the package and package-extra name.


    .. change:: Fix OpenAPI schema file upload schema types for swagger
        :type: bugfix
        :pr: 2745
        :issue: 2628

        - Always set ``format`` as ``binary``
        - Fix schema for swagger with multiple files, which requires the type of the
          request body schema to be ``object`` with ``properties`` instead of a schema
          of type ``array`` and ``items``.



.. changelog:: 2.5.0
    :date: 2024/01/06

    .. change:: Fix serialization of custom types in exception responses
        :type: bugfix
        :issue: 2867
        :pr: 2941

        Fix a bug that would lead to a :exc:`SerializationException` when custom types
        were present in an exception response handled by the built-in exception
        handlers.

        .. code-block:: python

            class Foo:
                pass


            @get()
            def handler() -> None:
                raise ValidationException(extra={"foo": Foo("bar")})


            app = Litestar(route_handlers=[handler], type_encoders={Foo: lambda foo: "foo"})

        The cause was that, in examples like the one shown above, ``type_encoders``
        were not resolved properly from all layers by the exception handling middleware,
        causing the serializer to throw an exception for an unknown type.

    .. change:: Fix SSE reverting to default ``event_type`` after 1st message
        :type: bugfix
        :pr: 2888
        :issue: 2877

        The ``event_type`` set within an SSE returned from a handler would revert back
        to a default after the first message sent:

        .. code-block:: python

            @get("/stream")
            async def stream(self) -> ServerSentEvent:
                async def gen() -> AsyncGenerator[str, None]:
                    c = 0
                    while True:
                        yield f"<div>{c}</div>\n"
                        c += 1

                return ServerSentEvent(gen(), event_type="my_event")

        In this example, the event type would only be ``my_event`` for the first
        message, and fall back to a default afterwards. The implementation has been
        fixed and will now continue sending the set event type for all messages.

    .. change:: Correctly handle single file upload validation when multiple files are specified
        :type: bugfix
        :pr: 2950
        :issue: 2939

        Uploading a single file when the validation target allowed multiple would cause
        a :exc:`ValidationException`:

        .. code-block:: python

            class FileUpload(Struct):
                files: list[UploadFile]


            @post(path="/")
            async def upload_files_object(
                data: Annotated[FileUpload, Body(media_type=RequestEncodingType.MULTI_PART)]
            ) -> list[str]:
                pass


        This could would only allow for 2 or more files to be sent, and otherwise throw
        an exception.

    .. change:: Fix trailing messages after unsubscribe in channels
        :type: bugfix
        :pr: 2894

        Fix a bug that would allow some channels backend to receive messages from a
        channel it just unsubscribed from, for a short period of time, due to how the
        different brokers handle unsubscribes.

        .. code-block:: python

            await backend.subscribe(["foo", "bar"])  # subscribe to two channels
            await backend.publish(
                b"something", ["foo"]
            )  # publish a message to a channel we're subscribed to

            # start the stream after publishing. Depending on the backend
            # the previously published message might be in the stream
            event_generator = backend.stream_events()

            # unsubscribe from the channel we previously published to
            await backend.unsubscribe(["foo"])

            # this should block, as we expect messages from channels
            # we unsubscribed from to not appear in the stream anymore
            print(anext(event_generator))

        Backends affected by this were in-memory, Redis PubSub and asyncpg. The Redis
        stream and psycopg backends were not affected.

    .. change:: Postgres channels backends
        :type: feature
        :pr: 2803

        Two new channel backends were added to bring Postgres support:

        :class:`~litestar.channels.backends.asyncpg.AsyncPgChannelsBackend`, using the
        `asyncpg <https://magicstack.github.io/asyncpg/current/>`_ driver and
        :class:`~litestar.channels.backends.psycopg.PsycoPgChannelsBackend` using the
        `psycopg3 <https://www.psycopg.org/psycopg3/docs/>`_ async driver.

        .. seealso::
            :doc:`/usage/channels`


    .. change:: Add ``--schema`` and ``--exclude`` option to ``litestar route`` CLI command
        :type: feature
        :pr: 2886

        Two new options were added to the ``litestar route`` CLI command:

        - ``--schema``, to include the routes serving OpenAPI schema and docs
        - ``--exclude`` to exclude routes matching a specified pattern

        .. seealso::
            :ref:`usage/cli:routes`

    .. change:: Improve performance of threaded synchronous execution
        :type: misc
        :pr: 2937

        Performance of threaded synchronous code was improved by using the async
        library's native threading helpers instead of anyio. On asyncio,
        :meth:`asyncio.loop.run_in_executor` is now used and on trio
        :func:`trio.to_thread.run_sync`.

        Beneficiaries of these performance improvements are:

        - Synchronous route handlers making use of ``sync_to_thread=True``
        - Synchronous dependency providers making use of ``sync_to_thread=True``
        - Synchronous SSE generators
        - :class:`~litestar.stores.file.FileStore`
        - Large file uploads where the ``max_spool_size`` is exceeded and the spooled
          temporary file has been rolled to disk
        - :class:`~litestar.response.file.File` and
          :class:`~litestar.response.file.ASGIFileResponse`


.. changelog:: 2.4.5
    :date: 2023/12/23

    .. change:: Fix validation of  empty payload data with default values
        :type: bugfix
        :issue: 2902
        :pr: 2903

        Prior to this fix, a handler like:

        .. code-block:: python

            @post(path="/", sync_to_thread=False)
            def test(data: str = "abc") -> dict:
                return {"foo": data}

        ``$ curl localhost:8000 -X POST``

        would return a client error like:

        .. code-block:: bash

            {"status_code":400,"detail":"Validation failed for POST http://localhost:8000/","extra":[{"message":"Expected `str`, got `null`","key":"data","source":"body"}]}

    .. change:: Support for returning ``Response[None]`` with a ``204`` status code from a handler
        :type: bugfix
        :pr: 2915
        :issue: 2914

        Returning a ``Response[None]`` from a route handler for a response with a
        ``204`` now works as expected without resulting in an
        :exc:`ImproperlyConfiguredException`

    .. change:: Fix error message of ``get_logger_placeholder()``
        :type: bugfix
        :pr: 2919

        Using a method on
        :attr:`Request.logger <litestar.connection.ASGIConnection.logger>` when not
        setting a ``logging_config`` on the application would result in a non-descriptive
        :exc:`TypeError`. An :exc:`ImproperlyConfiguredException` with an explanation is
        now raised instead.


.. changelog:: 2.4.4
    :date: 2023/12/13

    .. change:: Support non-valid identifier as serialization target name
        :type: bugfix
        :pr: 2850
        :issue: 2845

        Fix a bug where DTOs would raise a ``TypeError: __slots__ must be identifiers``
        during serialization, if a non-valid identifier (such as ``field-name``)was used
        for field renaming.

    .. change:: Fix regression signature validation for DTO validated types
        :type: bugfix
        :pr: 2854
        :issue: 2149

        Fix a regression introduced in ``2.0.0rc1`` that would cause data validated by
        the DTO to be validated again by the signature model.

    .. change:: Fix regression in OpenAPI schema key names
        :type: bugfix
        :pr: 2841
        :issue: 2804

        Fix a regression introduced in ``2.4.0`` regarding the naming of OpenAPI schema
        keys, in which a change was introduced to the way that keys for the OpenAPI
        components/schemas objects were calculated to address the possibility of name
        collisions.

        This behaviour was reverted for the case where a name has no collision, and now
        only introduces extended keys for the case where there are multiple objects with
        the same name, a case which would previously result in an exception.

    .. change:: Fix regression in OpenAPI handling of routes with multiple handlers
        :type: bugfix
        :pr: 2864
        :issue: 2863

        Fix a regression introduced in ``2.4.3`` causing two routes registered with the
        same path, but different methods to break OpenAPI schema generation due to both
        of them having the same value for operation ID.

    .. change:: Fix OpenAPI schema generation for recursive models
        :type: bugfix
        :pr: 2869
        :issue: 2429

        Fix an issue that would lead to a :exc:`RecursionError` when including nested
        models in the OpenAPI schema.


.. changelog:: 2.4.3
    :date: 2023/12/07

    .. change:: Fix OpenAPI schema for ``Literal | None`` unions
        :type: bugfix
        :issue: 2812
        :pr: 2818

        Fix a bug where an incorrect OpenAPI schema was generated generated when any
        ``Literal | None``-union was present in an annotation.

        For example

        .. code-block:: python

            type: Literal["sink", "source"] | None

        would generate

        .. code-block:: json

            {
              "name": "type",
              "in": "query",
              "schema": {
                "type": "string",
                "enum": [ "sink", "source", null ]
              }
            }

    .. change:: Fix advanced-alchemy 0.6.0 compatibility issue with ``touch_updated_timestamp``
        :type: bugfix
        :pr: 2843

        Fix an incorrect import for ``touch_updated_timestamp`` of Advanced Alchemy,
        introduced in Advanced-Alchemy version 0.6.0.

.. changelog:: 2.4.2
    :date: 2023/12/02

    .. change:: Fix OpenAPI handling of parameters with duplicated names
        :type: bugfix
        :issue: 2662
        :pr: 2788

        Fix a bug where schema generation would consider two parameters with the same
        name but declared in different places (eg., header, cookie) as an error.

    .. change:: Fix late failure where ``DTOData`` is used without a DTO
        :type: bugfix
        :issue: 2779
        :pr: 2789

        Fix an issue where a handler would be allowed to be registered with a
        ``DTOData`` annotation without having a DTO defined, which would result in a
        runtime exception. In cases like these, a configuration error is now raised
        during startup.

    .. change:: Correctly propagate camelCase names on OpenAPI schema
        :type: bugfix
        :pr: 2800

        Fix a bug where OpenAPI schema fields would be inappropriately propagated as
        camelCase where they should have been snake_case

    .. change:: Fix error handling in event handler stream
        :type: bugfix
        :pr: 2810, 2814

        Fix a class of errors that could result in the event listener stream being
        terminated when an exception occurred within an event listener. Errors in
        event listeners are now not propagated anymore but handled by the backend and
        logged instead.

    .. change:: Fix OpenAPI schema for Pydantic computed fields
        :type: bugfix
        :pr: 2797
        :issue: 2792

        Add support for including computed fields in schemas generated from Pydantic
        models.

.. changelog:: 2.4.1
    :date: 2023/11/28

    .. change:: Fix circular import when importing from ``litestar.security.jwt``
        :type: bugfix
        :pr: 2784
        :issue: 2782

        An :exc:`ImportError` was raised when trying to import from ``litestar.security.jwt``. This was fixed
        by removing the imports from the deprecated ``litestar.contrib.jwt`` within ``litesetar.security.jwt``.

    .. change:: Raise config error when generator dependencies are cached
        :type: bugfix
        :pr: 2780
        :issue: 2771

        Previously, an :exc:`InternalServerError` was raised when attempting to use
        `use_cache=True` with generator dependencies. This will now raise a configuration
        error during application startup.

.. changelog:: 2.4.0
    :date: 2023/11/27

    .. change:: Fix ``HTTPException`` handling during concurrent dependency resolving
        :type: bugfix
        :pr: 2596
        :issue: 2594

        An issue was fixed that would lead to :exc:`HTTPExceptions` not being re-raised
        properly when they occurred within the resolution of nested dependencies during
        the request lifecycle.

    .. change:: Fix OpenAPI examples format
        :type: bugfix
        :pr: 2660
        :issue: 2272

        Fix the OpenAPI examples format by removing the wrapping object.

        Before the change, for a given model

        .. code-block:: python

            @dataclass
            class Foo:
                foo: int

        The following example would be generated:

        .. code-block:: json

            {
                "description": "Example value",
                "value": {
                    "foo": 7906
                }
            }

        After the fix, this is now:

        .. code-block:: json

                {
                    "foo": 7906
                }

    .. change:: Fix CLI plugin commands not showing up in command list
        :type: bugfix
        :pr: 2441

        Fix a bug where commands registered by CLI plugins were available, but would not
        show up in the commands list

    .. change:: Fix missing ``write-only`` mark in ``dto_field()`` signature
        :type: bugfix
        :pr: 2684

        Fix the missing ``write-only`` string literal in the ``mark`` parameter of
        :func:`~litestar.dto.field.dto_field`

    .. change:: Fix OpenAPI schemas incorrectly flagged as duplicates
        :type: bugfix
        :pr: 2475
        :issue: 2471

        Fix an issue that would lead to OpenAPI schemas being incorrectly considered
        duplicates, resulting in an :exc:`ImproperlyConfiguredException` being raised.

    .. change:: Fix Pydantic URL type support in OpenAPI and serialization
        :type: bugfix
        :pr: 2701
        :issue: 2664

        Add missing support for Pydantic's URL types (``AnyUrl`` and its descendants)
        for both serialization and OpenAPI schema generation. These types were only
        partially supported previously; Serialization support was lacking for v1 and v2,
        and OpenAPI support was missing for v2.

    .. change:: Fix incorrect ``ValidationException`` message when multiple errors were encountered
        :type: bugfix
        :pr: 2716
        :issue: 2714

        Fix a bug where :exc:`ValidationException` could contain duplicated messages in
        ``extra`` field, when multiple errors were encountered during validation

    .. change:: Fix DTO renaming renames all fields of the same name in nested DTOs
        :type: bugfix
        :pr: 2764
        :issue: 2721

        Fix an issue with nested field renaming in DTOs that would lead to all fields
        with a given name to be renamed in a nested structure.

        In the below example, both ``Foo.id`` and ``Bar.id`` would have been renamed to
        ``foo_id``

        .. code-block:: python

            from dataclasses import dataclass


            @dataclass
            class Bar:
                id: str


            @dataclass
            class Foo:
                id: str
                bar: Bar


            FooDTO = DataclassDTO[Annotated[Foo, DTOConfig(rename_fields={"id": "foo_id"})]]

    .. change:: Fix handling of DTO objects nested in mappings
        :type: bugfix
        :pr: 2775
        :issue: 2737

        Fix a bug where DTOs nested in a :class:`~typing.Mapping` type would fail to
        serialize correctly.

    .. change:: Fix inconsistent sequence union parameter errors
        :type: bugfix
        :pr: 2776
        :issue: 2600

        Fix a bug where unions of collection types would result in different errors
        depending on whether the union included :obj:`None` or not.

    .. change:: Fix graceful handling of WebSocket disconnect in channels WebSockets handlers
        :type: bugfix
        :pr: 2691

        Fix the behaviour of WebSocket disconnect handling within the WebSocket handlers
        provided by :doc:`channels </usage/channels>`, that would sometimes lead to
        a ``RuntimeError: Unexpected ASGI message 'websocket.close', after sending 'websocket.close'.``
        exception being raised upon the closing of a WebSocket connection.


    .. change:: Add ``server_lifespan`` hook
        :type: feature
        :pr: 2658

        A new ``server_lifespan`` hook is now available on :class:`~litestar.app.Litestar`.
        This hook works similar to the regular ``lifespan`` context manager, with the
        difference being is that it is only called once for the entire server lifespan,
        not for each application startup phase. Note that these only differ when running
        with an ASGI server that's using multiple worker processes.

    .. change:: Allow rendering templates directly from strings
        :type: feature
        :pr: 2689
        :issue: 2687

        A new ``template_string`` parameter was added to :class:`~litestar.template.Template`,
        allowing to render templates directly from strings.

        .. seealso::
            :ref:`usage/templating:Template Files vs. Strings`

    .. change:: Support nested DTO field renaming
        :type: feature
        :pr: 2764
        :issue: 2721

        Using similar semantics as for exclusion/inclusion, nested DTO fields can now
        also be renamed:

        .. code-block:: python

            from dataclasses import dataclass


            @dataclass
            class Bar:
                id: str


            @dataclass
            class Foo:
                id: str
                bars: list[Bar]


            FooDTO = DataclassDTO[Annotated[Foo, DTOConfig(rename_fields={"bars.0.id": "bar_id"})]]


.. changelog:: 2.3.2
    :date: 2023/11/06

    .. change:: Fix recursion error when re-using the path of a route handler for static files
        :type: bugfix
        :pr: 2630
        :issue: 2629

        A regression was fixed that would cause a recursion error when the path of a
        static files host was reused for a route handler with a different HTTP method.

        .. code-block:: python

            from litestar import Litestar
            from litestar import post
            from litestar.static_files import StaticFilesConfig


            @post("/uploads")
            async def handler() -> None:
                pass


            app = Litestar(
                [handler],
                static_files_config=[
                    StaticFilesConfig(directories=["uploads"], path="/uploads"),
                ],
            )


.. changelog:: 2.3.1
    :date: 2023/11/04

    .. change:: CLI: Fix not providing SSL certfiles breaks uvicorn command when using reload or multiple workers
        :type: bugfix
        :pr: 2616
        :issue: 2613

        Fix an issue where not providing the ``--ssl-certfile`` and ``--ssl-keyfile``
        options to the ``litestar run`` command would cause a :exc:`FileNotFoundError`
        in uvicorn, when used together with the ``--reload``, ``--web-concurrency``
        options.


.. changelog:: 2.3.0
    :date: 2023/11/02

    .. change:: Python 3.12 support
        :type: feature
        :pr: 2396
        :issue: 1862

        Python 3.12 is now fully supported and tested.

    .. change:: New layered parameter ``signature_types``
        :type: feature
        :pr: 2422

        Types in this collection are added to ``signature_namespace`` using the type's
        ``__name__`` attribute.
        This provides a nicer interface when adding names to the signature namespace
        w ithout modifying the type name, e.g.: ``signature_namespace={"Model": Model}``
        is equivalent to ``signature_types=[Model]``.

        The implementation makes it an error to supply a type in ``signature_types``
        that has a value for ``__name__`` already in the signature namespace.

        It will also throw an error if an item in ``signature_types`` has no
        ``__name__`` attribute.

    .. change:: Added RapiDoc for OpenAPI schema visualisation
        :type: feature
        :pr: 2522

        Add support for using `RapiDoc <https://github.com/rapi-doc/RapiDoc>`_ for
        OpenAPI schema visualisation.

    .. change:: Support Pydantic 1 & 2 within the same application
        :type: feature
        :pr: 2487

        Added support for Pydantic 1 & 2 within the same application by integrating with
        Pydantic's backwards compatibility layer:

        .. code-block:: python

            from litestar import get
            from pydantic.v1 import BaseModel as BaseModelV1
            from pydantic import BaseModel


            class V1Foo(BaseModelV1):
                bar: str


            class V2Foo(BaseModel):
                bar: str


            @get("/1")
            def foo_v1(data: V1Foo) -> V1Foo:
                return data


            @get("/2")
            def foo_v2(data: V2Foo) -> V2Foo:
                return data

    .. change:: Add ``ResponseCacheConfig.cache_response_filter`` to allow filtering responses eligible for caching
        :type: feature
        :pr: 2537
        :issue: 2501

        ``ResponseCacheConfig.cache_response_filter`` is predicate called by the
        response cache middleware that discriminates whether a response should be
        cached, or not.


    .. change:: SSL support and self-signed certificates for CLI
        :type: feature
        :pr: 2554
        :issue: 2335

        Add support for SSL and generating self-signed certificates to the CLI.

        For this, three new arguments were added to the CLI's ``run`` command:

        - ``--ssl-certfile``
        - ``--ssl-keyfile``
        - ``--create-self-signed-cert``

        The ``--ssl-certfile`` and `--ssl-keyfile` flags are passed to uvicorn when
        using ``litestar run``. Uvicorn requires both to be passed (or neither) but
        additional validation was added to generate a more user friendly CLI errors.

        The other SSL-related flags (like password or CA) were not added (yet). See
        `uvicorn CLI docs <https://www.uvicorn.org/#command-line-options>`_

        **Generating of a self-signed certificate**

        One more CLI flag was added (``--create-devcert``) that uses the
        ``cryptography`` module to generate a self-signed development certificate. Both
        of the previous flags must be passed when using this flag. Then the following
        logic is used:

        - If both files already exists, they are used and nothing is generated
        - If neither file exists, the dev cert and key are generated
        - If only one file exists, it is ambiguous what to do so an exception is raised

    .. change:: Use custom request class when given during exception handling
        :type: bugfix
        :pr: 2444
        :issue: 2399

        When a custom ``request_class`` is provided, it will now be used while returning
        an error response

    .. change:: Fix missing OpenAPI schema for generic response type annotations
        :type: bugfix
        :pr: 2463
        :issue: 2383

        OpenAPI schemas are now correctly generated when a response type annotation
        contains a generic type such as

        .. code-block:: python

            from msgspec import Struct
            from litestar import Litestar, get, Response
            from typing import TypeVar, Generic, Optional

            T = TypeVar("T")


            class ResponseStruct(Struct, Generic[T]):
                code: int
                data: Optional[T]


            @get("/")
            def test_handler() -> Response[ResponseStruct[str]]:
                return Response(
                    ResponseStruct(code=200, data="Hello World"),
                )

    .. change:: Fix rendering of OpenAPI examples
        :type: bugfix
        :pr: 2509
        :issue: 2494

        An issue was fixed where OpenAPI examples would be rendered as

        .. code-block:: json

            {
              "parameters": [
                {
                  "schema": {
                    "type": "string",
                    "examples": [
                      {
                        "summary": "example summary",
                        "value": "example value"
                      }
                    ]
                  }
                }
              ]
            }

        instead of

        .. code-block:: json

            {
              "parameters": [
                {
                  "schema": {
                    "type": "string"
                  },
                  "examples": {
                    "example1": {
                      "summary": "example summary"
                      "value": "example value"
                    }
                  }
                }
              ]
            }

    .. change:: Fix non UTF-8 handling when logging requests
        :type: bugfix
        :issue: 2529
        :pr: 2530

        When structlog is not installed, the request body would not get parsed and shown
        as a byte sequence. Instead, it was serialized into a string with the assumption
        that it is valid UTF-8. This was fixed by decoding the bytes with
        ``backslashreplace`` before displaying them.

    .. change:: Fix ``ExceptionHandler`` typing to properly support ``Exception`` subclasses
        :type: bugfix
        :issue: 2520
        :pr: 2533

        Fix the typing for ``ExceptionHandler`` to support subclasses of ``Exception``,
        such that code like this will type check properly:

        .. code-block:: python

            from litestar import Litestar, Request, Response


            class CustomException(Exception): ...


            def handle_exc(req: Request, exc: CustomException) -> Response: ...

    .. change:: Fix OpenAPI schema generation for variable length tuples
        :type: bugfix
        :issue: 2460
        :pr: 2552

        Fix a bug where an annotation such as ``tuple[str, ...]`` would cause a
        ``TypeError: '<' not supported between instances of 'NoneType' and 'OpenAPIType')``.

    .. change:: Fix channels performance issue when polling with no subscribers in ``arbitrary_channels_allowed`` mode
        :type: bugfix
        :pr: 2547

        Fix a bug that would cause high CPU loads while idling when using a
        ``ChannelsPlugin`` with the ``arbitrary_channels_allowed`` enabled and while no
        subscriptions for any channel were active.

    .. change:: Fix CLI schema export for non-serializable types when using ``create_examples=True``
        :type: bugfix
        :pr: 2581
        :issue: 2575

        When trying to export a schema via the
        ``litestar schema openapi --output schema.json`` making use of a non-JSON
        serializable type, would result in an encoding error because the standard
        library JSON serializer was used. This has been fixed by using Litestar's own
        JSON encoder, enabling the serialization of all types supplied by the schema.

    .. change:: Fix OpenAPI schema generation for ``Literal`` and ``Enum`` unions with ``None``
        :type: bugfix
        :pr: 2550
        :issue: 2546

        Existing behavior was to make the schema for every type that is a union with
        ``None`` a ``"one_of"`` schema, that includes ``OpenAPIType.NULL`` in the
        ``"one_of"`` types.

        When a ``Literal`` or ``Enum`` type is in a union with ``None``, this behavior
        is not desirable, as we want to have ``null`` available in the list of available
        options on the type's schema.

        This was fixed by modifying ``Literal`` and ``Enum`` schema generation so that i
        t can be identified that the types are in a union with ``None``, allowing
        ``null`` to be included in ``Schema.enum`` values.

    .. change:: Fix cache overrides when using same route with different handlers
        :type: bugfix
        :pr: 2592
        :issue: 2573, 2588

        A bug was fixed that would cause the cache for routes being overwritten by a
        route handler on that same route with a different HTTP method.



.. changelog:: 2.2.0
    :date: 2023/10/12

    .. change:: Fix implicit conversion of objects to ``bool`` in debug response
        :type: bugfix
        :pr: 2384
        :issue: 2381

        The exception handler middleware would, when in debug mode, implicitly call an
        object's :meth:`__bool__ <object.__bool__>`, which would lead to errors if that
        object overloaded the operator, for example if the object in question was a
        SQLAlchemy element.

    .. change:: Correctly re-export filters and exceptions from ``advanced-alchemy``
        :type: bugfix
        :pr: 2360
        :issue: 2358

        Some re-exports of filter and exception types from ``advanced-alchemy`` were
        missing, causing various issues when ``advanced-alchemy`` was installed, but
        Litestar would still use its own version of these classes.

    .. change:: Re-add ``create_engine`` method to SQLAlchemy configs
        :type: bugfix
        :pr: 2382

        The ``create_engine`` method was removed in an ``advanced-alchemy`` releases.
        This was addresses by re-adding it to the versions provided by Litestar.

    .. change:: Fix ``before_request`` modifies route handler signature
        :type: bugfix
        :pr: 2391
        :issue: 2368

        The ``before_request`` would modify the return annotation of associated
        route handlers to conform with its own return type annotation, which would cause
        issues and unexpected behaviour when that annotation was not compatible with the
        original one.

        This was fixed by not having the ``before_request`` handler modify the
        route handler's signature. Users are now expected to ensure that values returned
        from a ``before_request`` handler conform to the return type annotation of the
        route handler.

    .. change:: Ensure compression is applied before caching when using compression middleware
        :type: bugfix
        :pr: 2393
        :issue: 1301

        A previous limitation was removed that would apply compression from the
        :class:`~litestar.middleware.compression.CompressionMiddleware` only *after* a
        response was restored from the cache, resulting in unnecessary repeated
        computation and increased size of the stored response.

        This was due to caching being handled on the response layer, where a response
        object would be pickled, restored upon a cache hit and then re-sent, including
        all middlewares.

        The new implementation now instead applies caching on the ASGI level; Individual
        messages sent to the ``send`` callable are cached, and later re-sent. This
        process ensures that the compression middleware has been applied before, and
        will be skipped when re-sending a cached response.

        In addition, this increases performance and reduces storage size even in cases
        where no compression is applied because the slow and inefficient pickle format
        can be avoided.

    .. change:: Fix implicit JSON parsing of URL encoded data
        :type: bugfix
        :pr: 2394

        A process was removed where Litestar would implicitly attempt to parse parts of
        URL encoded data as JSON. This was originally added to provide some performance
        boosts when that data was in fact meant to be JSON, but turned out to be too
        fragile.

        Regular data conversion / validation is unaffected by this.

    .. change:: CLI enabled by default
        :type: feature
        :pr: 2346
        :issue: 2318

        The CLI and all its dependencies are now included by default, to enable a better
        and more consistent developer experience out of the box.

        The previous ``litestar[cli]`` extra is still available for backwards
        compatibility, but as of ``2.2.0`` it is without effect.

    .. change:: Customization of Pydantic integration via ``PydanticPlugin``
        :type: feature
        :pr: 2404
        :issue: 2373

        A new :class:`~litestar.contrib.pydantic.PydanticPlugin` has been added, which
        can be used to configure Pydantic behaviour. Currently it supports setting a
        ``prefer_alias`` option, which will pass the ``by_alias=True`` flag to Pydantic
        when exporting models, as well as generate schemas accordingly.

    .. change:: Add ``/schema/openapi.yml`` to the available schema paths
        :type: feature
        :pr: 2411

        The YAML version of the OpenAPI schema is now available under
        ``/schema/openapi.yml`` in addition to ``/schema/openapi.yaml``.

    .. change:: Add experimental DTO codegen backend
        :type: feature
        :pr: 2388

        A new DTO backend was introduced which speeds up the transfer process by
        generating optimized Python code ahead of time. Testing shows that the new
        backend is between 2.5 and 5 times faster depending on the operation and data
        provided.

        The new backend can be enabled globally for all DTOs by passing the appropriate
        feature flag to the Litestar application:

        .. code-block:: python

            from litestar import Litestar
            from litestar.config.app import ExperimentalFeatures

            app = Litestar(experimental_features=[ExperimentalFeatures.DTO_CODEGEN])

        .. seealso::
            For more information see
            :ref:`usage/dto/0-basic-use:Improving performance with the codegen backend`


    .. change:: Improved error messages for missing required parameters
        :type: feature
        :pr: 2418

        Error messages for missing required parameters will now also contain the source
        of the expected parameter:

        Before:

        .. code-block:: json

            {
              "status_code": 400,
              "detail": "Missing required parameter foo for url http://testerver.local"
            }


        After:

        .. code-block:: json

            {
              "status_code": 400,
              "detail": "Missing required header parameter 'foo' for url http://testerver.local"
            }


.. changelog:: 2.1.1
    :date: 2023/09/24

    .. change:: Fix ``DeprecationWarning`` raised by ``Response.to_asgi_response``
        :type: bugfix
        :pr: 2364

        :meth:`~litestar.response.Response.to_asgi_response` was passing a
        non-:obj:`None` default value (``[]``) to ``ASGIResponse`` for
        ``encoded_headers``, resulting in a :exc:`DeprecationWarning` being raised.
        This was fixed by leaving the default value as :obj:`None`.


.. changelog:: 2.1.0
    :date: 2023/09/23

    `View the full changelog <https://github.com/litestar-org/litestar/compare/v2.0.0...v2.1.0x>`_

    .. change:: Make ``302`` the default ``status_code`` for redirect responses
        :type: feature
        :pr: 2189
        :issue: 2138

        Make ``302`` the default ``status_code`` for redirect responses

    .. change:: Add :meth:`include_in_schema` option for all layers
        :type: feature
        :pr: 2295
        :issue: 2267

        Adds the :meth:`include_in_schema` option to all layers, allowing to include/exclude
        specific routes from the generated OpenAPI schema.

    .. change:: Deprecate parameter ``app`` of ``Response.to_asgi_response``
        :type: feature
        :pr: 2268
        :issue: 2217

        Adds deprecation warning for unused ``app`` parameter of ``to_asgi_response`` as
        it is unused and redundant due to ``request.app`` being available.

    .. change:: Authentication: Add parameters to set the JWT ``extras`` field
        :type: feature
        :pr: 2313

        Adds ``token_extras`` to both :func:`BaseJWTAuth.login` and :meth:`BaseJWTAuth.create_token` methods,
        to allow the definition of the ``extras`` JWT field.

    .. change:: Templating: Add possibility to customize Jinja environment
        :type: feature
        :pr: 2195
        :issue: 965

        Adds the ability to pass a custom Jinja2 ``Environment`` or Mako ``TemplateLookup`` by providing a
        dedicated class method.

    .. change:: Add support for `minjinja <https://github.com/mitsuhiko/minijinja>`_
        :type: feature
        :pr: 2250

        Adds support for MiniJinja, a minimal Jinja2 implementation.

        .. seealso:: :doc:`/usage/templating`

    .. change:: SQLAlchemy: Exclude implicit fields for SQLAlchemy DTO
        :type: feature
        :pr: 2170

        :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>` can now be
        configured using a separate config object. This can be set using both
        class inheritance and `Annotated <https://docs.python.org/3/library/typing.html#typing.Annotated>`_:

        .. code-block:: python
            :caption: :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>` can now be configured using a separate config object using ``config`` object.

            class MyModelDTO(SQLAlchemyDTO[MyModel]):
                config = SQLAlchemyDTOConfig()

        or

        .. code-block:: python
            :caption: :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>` can now be configured using a separate config object using ``Annotated``.

             MyModelDTO = SQLAlchemyDTO[Annotated[MyModel, SQLAlchemyDTOConfig()]]

        The new configuration currently accepts a single attribute which is ``include_implicit_fields`` that has
        a default value of ``True``. If set to to ``False``, all implicitly mapped columns will be hidden
        from the ``DTO``. If set to ``hybrid-only``, then hybrid properties will be shown but not other
        implicit columns.

        Finally, implicit columns that are marked with ``Mark.READ_ONLY`` or ``Mark.WRITE_ONLY``
        will always be shown regardless of the value of ``include_implicit_fields``.

    .. change:: SQLAlchemy: Allow repository functions to be filtered by expressions
        :type: feature
        :pr: 2265

        Enhances the SQLALchemy repository so that you can more easily pass in complex ``where`` expressions into the repository functions.

        .. tip:: Without this, you have to override the ``statement`` parameter and it separates the where conditions from the filters and the ``kwargs``.

        Allows usage of this syntax:

        .. code-block:: python

            locations, total_count = await model_service.list_and_count(
                ST_DWithin(UniqueLocation.location, geog, 1000), account_id=str(account_id)
            )

        instead of the previous method of overriding the ``statement``:

        .. code-block:: python

            locations, total_count = await model_service.list_and_count(
                statement=select(Model).where(ST_DWithin(UniqueLocation.location, geog, 1000)),
                account_id=str(account_id),
            )

    .. change:: SQLAlchemy: Use :func:`lambda_stmt <sqlalchemy.sql.expression.lambda_stmt>` in the repository
        :type: feature
        :pr: 2179

        Converts the repository to use :func:`lambda_stmt <sqlalchemy.sql.expression.lambda_stmt>`
        instead of the normal ``select``

    .. change:: SQLAlchemy: Swap to the `advanced_alchemy <https://docs.advanced-alchemy.jolt.rs>`_ implementations
        :type: feature
        :pr: 2312

        Swaps the internal SQLAlchemy repository to use the external
        `advanced_alchemy <https://docs.advanced-alchemy.jolt.rs>`_ library implementations

    .. change:: Remove usages of deprecated ``ExceptionHandlerMiddleware`` ``debug`` parameter
        :type: bugfix
        :pr: 2192

        Removes leftover usages of deprecated ``ExceptionHandlerMiddleware`` debug parameter.

    .. change:: DTOs: Raise :class:`ValidationException` when Pydantic validation fails
        :type: bugfix
        :pr: 2204
        :issue: 2190

         Ensures that when the Pydantic validation fails in the Pydantic DTO,
         a :class:`ValidationException` is raised with the extras set to the errors given by Pydantic.

    .. change:: Set the max width of the console to 80
        :type: bugfix
        :pr: 2244

        Sets the max width of the console to 80, to prevent the output from being
        wrapped.

    .. change:: Handling of optional path parameters
        :type: bugfix
        :pr: 2224
        :issue: 2222

        Resolves an issue where optional path parameters caused a 500 error to be raised.

    .. change:: Use os.replace instead of shutil.move for renaming files
        :type: bugfix
        :pr: 2223

        Change to using :func:`os.replace` instead of :func:`shutil.move` for renaming files, to
        ensure atomicity.

    .. change:: Exception detail attribute
        :type: bugfix
        :pr: 2231

        Set correctly the detail attribute on :class:`LitestarException` and :class:`HTTPException`
        regardless of whether it's passed positionally or by name.

    .. change:: Filters not available in ``exists()``
        :type: bugfix
        :pr: 2228
        :issue: 2221

        Fixes :meth:`exists` method for SQLAlchemy sync and async.

    .. change:: Add Pydantic types to SQLAlchemy registry only if Pydantic is installed
        :type: bugfix
        :pr: 2252

        Allows importing from ``litestar.contrib.sqlalchemy.base`` even if Pydantic is not installed.

    .. change:: Don't add content type for responses that don't have a body
        :type: bugfix
        :pr: 2263
        :issue: 2106

        Ensures that the ``content-type`` header is not added for responses that do not have a
        body such as responses with status code ``204 (No Content)``.

    .. change:: ``SQLAlchemyPlugin`` refactored
        :type: bugfix
        :pr: 2269

        Changes the way the ``SQLAlchemyPlugin`` to now append the other plugins instead of the
        inheritance that was previously used. This makes using the ``plugins.get`` function work as expected.

    .. change:: Ensure ``app-dir`` is appended to path during autodiscovery
        :type: bugfix
        :pr: 2277
        :issue: 2266

        Fixes a bug which caused the ``--app-dir`` option to the Litestar CLI to not be propagated during autodiscovery.

    .. change:: Set content length header by default
        :type: bugfix
        :pr: 2271

        Sets the ``content-length`` header by default even if the length of the body is ``0``.

    .. change:: Incorrect handling of mutable headers in :class:`ASGIResponse`
        :type: bugfix
        :pr: 2308
        :issue: 2196

        Update :class:`ASGIResponse`, :class:`Response` and friends to address a few issues related to headers:

        - If ``encoded_headers`` were passed in at any point, they were mutated within responses, leading to a growing list of headers with every response
        - While mutating ``encoded_headers``, the checks performed to assert a value was (not) already present, headers were not treated case-insensitive
        - Unnecessary work was performed while converting cookies / headers into an encoded headers list

        This was fixed by:

        - Removing the use of and deprecate ``encoded_headers``
        - Handling headers on :class:`ASGIResponse` with :class:`MutableScopeHeaders`, which allows for case-insensitive membership tests, ``.setdefault`` operations, etc.

    .. change:: Adds missing ORM registry export
        :type: bugfix
        :pr: 2316

        Adds an export that was overlooked for the base repo

    .. change:: Discrepancy in ``attrs``, ``msgspec`` and ``Pydantic`` for multi-part forms
        :type: bugfix
        :pr: 2280
        :issue: 2278

        Resolves issue in ``attrs``, ``msgspec`` and Pydantic for multi-part forms

    .. change:: Set proper default for ``exclude_http_methods`` in auth middleware
        :type: bugfix
        :pr: 2325
        :issue: 2205

        Sets ``OPTIONS`` as the default value for ``exclude_http_methods`` in the base authentication middleware class.

.. changelog:: 2.0.0
    :date: 2023/08/19

    .. change:: Regression | Missing ``media_type`` information to error responses
        :type: bugfix
        :pr: 2131
        :issue: 2024

        Fixed a regression that caused error responses to be sent using a mismatched
        media type, e.g. an error response from a ``text/html`` endpoint would be sent
        as JSON.

    .. change:: Regression | ``Litestar.debug`` does not propagate to exception handling middleware
        :type: bugfix
        :pr: 2153
        :issue: 2147

        Fixed a regression where setting ``Litestar.debug`` would not propagate to the
        exception handler middleware, resulting in exception responses always being sent
        using the initial debug value.

    .. change:: Static files not being served if a route handler with the same base path was registered
        :type: bugfix
        :pr: 2154

        Fixed a bug that would result in a ``404 - Not Found`` when requesting a static
        file where the :attr:`~litestar.static_files.StaticFilesConfig.path` was also
        used by a route handler.

    .. change:: HTMX: Missing default values for ``receive`` and ``send`` parameters of ``HTMXRequest``
        :type: bugfix
        :pr: 2145

        Add missing default values for the ``receive`` and ``send`` parameters of
        :class:`~litestar.contrib.htmx.request.HTMXRequest`.

    .. change:: DTO: Excluded attributes accessed during transfer
        :type: bugfix
        :pr: 2127
        :issue: 2125

        Fix the behaviour of DTOs such that they will no longer access fields that have
        been included. This behaviour would previously cause issues when these
        attributes were either costly or impossible to access (e.g. lazy loaded
        relationships of a SQLAlchemy model).

    .. change:: DTO | Regression: ``DTOData.create_instance`` ignores renaming
        :type: bugfix
        :pr: 2144

        Fix a regression where calling
        :meth:`~litestar.dto.data_structures.DTOData.create_instance` would ignore the
        renaming settings of fields.

    .. change:: OpenAPI | Regression: Response schema for files and streams set ``application/octet-stream`` as ``contentEncoding`` instead of ``contentMediaType``
        :type: bugfix
        :pr: 2130

        Fix a regression that would set ``application/octet-stream`` as the ``contentEncoding``
        instead of ``contentMediaType`` in the response schema of
        :class:`~litestar.response.File` :class:`~litestar.response.Stream`.

    .. change:: OpenAPI | Regression: Response schema diverges from ``prefer_alias`` setting for Pydantic models
        :type: bugfix
        :pr: 2150

        Fix a regression that made the response schema use ``prefer_alias=True``,
        diverging from how Pydantic models are exported by default.

    .. change:: OpenAPI | Regression: Examples not being generated deterministically
        :type: bugfix
        :pr: 2161

        Fix a regression that made generated examples non-deterministic, caused by a
        misconfiguration of the random seeding.

    .. change:: SQLAlchemy repository: Handling of dialects not supporting JSON
        :type: bugfix
        :pr: 2139
        :issue: 2137

        Fix a bug where SQLAlchemy would raise a :exc:`TypeError` when using a dialect
        that does not support JSON with the SQLAlchemy repositories.

    .. change:: JWT | Regression: ``OPTIONS`` and ``HEAD`` being authenticated by default
        :type: bugfix
        :pr: 2160

        Fix a regression that would make
        ``litestar.contrib.jwt.JWTAuthenticationMiddleware`` authenticate
        ``OPTIONS`` and ``HEAD`` requests by default.

    .. change:: SessionAuth | Regression: ``OPTIONS`` and ``HEAD`` being authenticated by default
        :type: bugfix
        :pr: 2182

        Fix a regression that would make
        :class:`~litestar.security.session_auth.middleware.SessionAuthMiddleware` authenticate
        ``OPTIONS`` and ``HEAD`` requests by default.

.. changelog:: 2.0.0rc1
    :date: 2023/08/05

    .. change:: Support for server-sent-events
        :type: feature
        :pr: 2035
        :issue: 1185

        Support for `Server-sent events <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>` has been
        added with the :class:`ServerSentEvent <.response.ServerSentEvent>`:

        .. code-block:: python

            async def my_generator() -> AsyncGenerator[bytes, None]:
                count = 0
                while count < 10:
                    await sleep(0.01)
                    count += 1
                    yield str(count)


            @get(path="/count")
            def sse_handler() -> ServerSentEvent:
                return ServerSentEvent(my_generator())

        .. seealso::
            :ref:`Server Sent Events <usage/responses:Server Sent Event Responses>`


    .. change:: SQLAlchemy repository: allow specifying ``id_attribute`` per method
        :type: feature
        :pr: 2052

        The following methods now accept an ``id_attribute`` argument, allowing to
        specify an alternative value to the models primary key:

        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.delete``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.delete_many``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.get``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.update``

        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.delete``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.delete_many``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.get``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.update``

    .. change:: SQLAlchemy repository: New ``upsert_many`` method
        :type: feature
        :pr: 2056

        A new method ``upsert_many`` has been added to the SQLAlchemy repositories,
        providing equivalent functionality to the ``upsert`` method for multiple
        model instances.

        .. seealso::
            ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.upsert_many``
            ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.upsert_many``

    .. change:: SQLAlchemy repository: New filters: ``OnBeforeAfter``, ``NotInCollectionFilter`` and ``NotInSearchFilter``
        :type: feature
        :pr: 2057

        The following filters have been added to the SQLAlchemy repositories:

        ``litestar.contrib.repository.filters.OnBeforeAfter``

            Allowing to filter :class:`datetime.datetime` columns

        ``litestar.contrib.repository.filters.NotInCollectionFilter``

            Allowing to filter using a ``WHERE ... NOT IN (...)`` clause

        ``litestar.contrib.repository.filters.NotInSearchFilter``

            Allowing to filter using a `WHERE field_name NOT LIKE '%' || :value || '%'`` clause

    .. change:: SQLAlchemy repository: Configurable chunk sizing for ``delete_many``
        :type: feature
        :pr: 2061

        The repository now accepts a ``chunk_size`` parameter, determining the maximum
        amount of parameters in an ``IN`` statement before it gets chunked.

        This is currently only used in the ``delete_many`` method.


    .. change:: SQLAlchemy repository: Support InstrumentedAttribute for attribute columns
        :type: feature
        :pr: 2054

        Support :class:`~sqlalchemy.orm.InstrumentedAttribute` for in the repository's
        ``id_attribute``, and the following methods:


        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.delete``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.delete_many``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.get``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.update``

        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.delete``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.delete_many``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.get``
        - ``~litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository.update``

    .. change:: OpenAPI: Support callable ``operation_id`` on route handlers
        :type: feature
        :pr: 2078

        Route handlers may be passed a callable to ``operation_id`` to create the
        OpenAPI operation ID.

    .. change:: Run event listeners concurrently
        :type: feature
        :pr: 2096

        :doc:`/usage/events` now run concurrently inside a task group.

    .. change:: Support extending the CLI with plugins
        :type: feature
        :pr: 2066

        A new plugin protocol :class:`~litestar.plugins.CLIPluginProtocol` has been
        added that can be used to extend the Litestar CLI.

        .. seealso::
            :ref:`usage/cli:Using a plugin`

    .. change:: DTO: Support renamed fields in ``DTOData`` and ``create_instance``
        :type: bugfix
        :pr: 2065

        A bug was fixed that would cause field renaming to be skipped within
        :class:`~litestar.dto.data_structures.DTOData` and
        :meth:`~litestar.dto.data_structures.DTOData.create_instance`.

    .. change:: SQLAlchemy repository: Fix ``health_check`` for oracle
        :type: bugfix
        :pr: 2060

        The emitted statement for oracle has been changed to ``SELECT 1 FROM DUAL``.

    .. change:: Fix serialization of empty strings in multipart form
        :type: bugfix
        :pr: 2044

        A bug was fixed that would cause a validation error to be raised for empty
        strings during multipart form decoding.

    .. change:: Use debug mode by default in test clients
        :type: misc
        :pr: 2113

        The test clients will now default to ``debug=True`` instead of ``debug=None``.

    .. change:: Removal of deprecated ``partial`` module
        :type: misc
        :pr:  2113
        :breaking:

        The deprecated ``litestar.partial`` has been removed. It can be replaced with
        DTOs, making use of the :class:`~litestar.dto.config.DTOConfig` option
        ``partial=True``.

    .. change:: Removal of deprecated ``dto/factory`` module
        :type: misc
        :pr: 2114
        :breaking:

        The deprecated module ``litestar.dto.factory`` has been removed.

    .. change:: Removal of deprecated ``contrib/msgspec`` module
        :type: misc
        :pr: 2114
        :breaking:

        The deprecated module ``litestar.contrib.msgspec`` has been removed.


.. changelog:: 2.0.0beta4
    :date: 2023/07/21

    .. change:: Fix extra package dependencies
        :type: bugfix
        :pr: 2029

        A workaround for a
        `bug in poetry <https://github.com/python-poetry/poetry/issues/4401>`_ that
        caused development / extra dependencies to be installed alongside the package
        has been added.

.. changelog:: 2.0.0beta3
    :date: 2023/07/20

    .. change:: :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>`: column/relationship type inference
        :type: feature
        :pr: 1879
        :issue: 1853

        If type annotations aren't available for a given column/relationship, they may
        be inferred from the mapped object.

        For columns, the :attr:`~sqlalchemy.engine.interfaces.ReflectedColumn.type`\ 's
        :attr:`~sqlalchemy.types.TypeEngine.python_type` will be used as the type of the
        column, and the :attr:`~sqlalchemy.engine.interfaces.ReflectedColumn.nullable`
        property to determine if the field should have a :obj:`None` union.

        For relationships, where the ``RelationshipProperty.direction`` is
        :attr:`~sqlalchemy.orm.RelationshipDirection.ONETOMANY` or
        :attr:`~sqlalchemy.orm.RelationshipDirection.MANYTOMANY`,
        ``RelationshipProperty.collection_class`` and
        ``RelationshipProperty.mapper.class_`` are used to construct an annotation for
        the collection.

        For one-to-one relationships, ``RelationshipProperty.mapper.class_`` is used to
        get the type annotation, and will be made a union with :obj:`None` if all of the
        foreign key columns are nullable.

    .. change:: DTO: Piccolo ORM
        :type: feature
        :pr: 1896

        Add support for piccolo ORM with the
        :class:`~litestar.contrib.piccolo.PiccoloDTO`.

    .. change:: OpenAPI: Allow setting ``OpenAPIController.path`` from ```OpenAPIConfig``
        :type: feature
        :pr: 1886

        :attr:`~litestar.openapi.OpenAPIConfig.path` has been added, which can be used
        to set the ``path`` for :class:`~litestar.openapi.OpenAPIController` directly,
        without needing to create a custom instance of it.

        If ``path`` is set in both :class:`~litestar.openapi.OpenAPIConfig` and
        :class:`~litestar.openapi.OpenAPIController`, the path set on the controller
        will take precedence.

    .. change:: SQLAlchemy repository: ``auto_commit``, ``auto_expunge`` and ``auto_refresh`` options
        :type: feature
        :pr: 1900

        .. currentmodule:: litestar.contrib.sqlalchemy.repository

        Three new parameters have been added to the repository and various methods:

        ``auto_commit``
            When this :obj:`True`, the session will
            :meth:`~sqlalchemy.orm.Session.commit` instead of
            :meth:`~sqlalchemy.orm.Session.flush` before returning.

            Available in:

            - ``~SQLAlchemyAsyncRepository.add``
            - ``~SQLAlchemyAsyncRepository.add_many``
            - ``~SQLAlchemyAsyncRepository.delete``
            - ``~SQLAlchemyAsyncRepository.delete_many``
            - ``~SQLAlchemyAsyncRepository.get_or_create``
            - ``~SQLAlchemyAsyncRepository.update``
            - ``~SQLAlchemyAsyncRepository.update_many``
            - ``~SQLAlchemyAsyncRepository.upsert``

            (and their sync equivalents)

        ``auto_refresh``
            When :obj:`True`, the session will execute
            :meth:`~sqlalchemy.orm.Session.refresh` objects before returning.

            Available in:

            - ``~SQLAlchemyAsyncRepository.add``
            - ``~SQLAlchemyAsyncRepository.get_or_create``
            - ``~SQLAlchemyAsyncRepository.update``
            - ``~SQLAlchemyAsyncRepository.upsert``

            (and their sync equivalents)


        ``auto_expunge``
            When this is :obj:`True`, the session will execute
            :meth:`~sqlalchemy.orm.Session.expunge` all objects before returning.

            Available in:

            - ``~SQLAlchemyAsyncRepository.add``
            - ``~SQLAlchemyAsyncRepository.add_many``
            - ``~SQLAlchemyAsyncRepository.delete``
            - ``~SQLAlchemyAsyncRepository.delete_many``
            - ``~SQLAlchemyAsyncRepository.get``
            - ``~SQLAlchemyAsyncRepository.get_one``
            - ``~SQLAlchemyAsyncRepository.get_one_or_none``
            - ``~SQLAlchemyAsyncRepository.get_or_create``
            - ``~SQLAlchemyAsyncRepository.update``
            - ``~SQLAlchemyAsyncRepository.update_many``
            - ``~SQLAlchemyAsyncRepository.list``
            - ``~SQLAlchemyAsyncRepository.upsert``

            (and their sync equivalents)

    .. change:: Include path name in ``ImproperlyConfiguredException`` message for missing param types
        :type: feature
        :pr: 1935

        The message of a :exc:`ImproperlyConfiguredException` raised when a path
        parameter is missing a type now contains the name of the path.

    .. change:: DTO: New ``include`` parameter added to ``DTOConfig``
        :type: feature
        :pr: 1950

        :attr:`~litestar.dto.config.DTOConfig.include` has been added to
        :class:`~litestar.dto.config.DTOConfig`, providing a counterpart to
        :attr:`~litestar.dto.config.DTOConfig.exclude`.

        If ``include`` is provided, only those fields specified within it will be
        included.

    .. change:: ``AbstractDTOFactory`` moved to ``dto.factory.base``
        :type: misc
        :breaking:
        :pr: 1950

        :class:`~litestar.dto.base_factory.AbstractDTOFactory` has moved from
        ``litestar.dto.factory.abc`` to ``litestar.dto.factory.base``.

    .. change:: SQLAlchemy repository: Rename ``_sentinel`` column to ``sa_orm_sentinel``
        :type: misc
        :breaking:
        :pr: 1933


        The ``_sentinel`` column of
        ``~litestar.contrib.sqlalchemy.base.UUIDPrimaryKey`` has been renamed to
        ``sa_orm_sentinel``, to support Spanner, which does not support tables starting
        with ``_``.

    .. change:: SQLAlchemy repository: Fix audit columns defaulting to app startup time
        :type: bugfix
        :pr: 1894

        A bug was fixed where
        ``~litestar.contrib.sqlalchemy.base.AuditColumns.created_at`` and
        ``~litestar.contrib.sqlalchemy.base.AuditColumns.updated_at`` would default
        to the :class:`~datetime.datetime` at initialization time, instead of the time
        of the update.

    .. change:: :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>`: Fix handling of ``Sequence`` with defaults
        :type: bugfix
        :pr: 1883
        :issue: 1851

        Fixes handling of columns defined with
        `Sequence <https://docs.sqlalchemy.org/en/20/core/defaults.html#defining-sequences>`_
        default values.

        The SQLAlchemy default value for a :class:`~sqlalchemy.schema.Column` will be
        ignored when it is a :class:`~sqlalchemy.schema.Sequence` object. This is
        because the SQLAlchemy sequence types represent server generated values, and
        there is no way for us to generate a reasonable default value for that field
        from it without making a database query, which is not possible deserialization.

    .. change:: Allow JSON as redirect response
        :type: bugfix
        :pr: 1908

        Enables using redirect responses with a JSON media type.

    .. change:: DTO / OpenAPI: Fix detection of required fields for Pydantic and msgspec DTOs
        :type: bugfix
        :pr: 1946

        A bug was fixed that would lead to fields of a Pydantic model or msgspec Structs
        being marked as "not required" in the generated OpenAPI schema when used with
        DTOs.

    .. change:: Replace ``Header``, ``CacheControlHeader`` and ``ETag`` Pydantic models with dataclasses
        :type: misc
        :pr: 1917
        :breaking:

        As part of the removal of Pydantic as a hard dependency, the header models
        :class:`~litestar.datastructures.Header`,
        :class:`~litestar.datastructures.CacheControlHeader` and
        :class:`~litestar.datastructures.ETag` have been replaced with dataclasses.


        .. note::
            Although marked breaking, this change should not affect usage unless you
            relied on these being Pydantic models in some way.

    .. change:: Pydantic as an optional dependency
        :breaking:
        :pr: 1963
        :type: misc

        As of this release, Pydantic is no longer a required dependency of Litestar.
        It is still supported in the same capacity as before, but Litestar itself does
        not depend on it anymore in its internals.

    .. change:: Pydantic 2 support
        :type: feature
        :pr: 1956

        Pydantic 2 is now supported alongside Pydantic 1.

    .. change:: Deprecation of  ``partial`` module
        :type: misc
        :pr: 2002

        The ``litestar.partial`` and ``litestar.partial.Partial`` have been
        deprecated and will be removed in a future release. Users are advised to upgrade
        to DTOs, making use of the :class:`~litestar.dto.config.DTOConfig` option
        ``partial=True``.


.. changelog:: 2.0.0beta2
    :date: 2023/06/24

    .. change:: Support ``annotated-types``
        :type: feature
        :pr: 1847

        Extended support for the
        `annotated-types <https://pypi.org/project/annotated-types>`_ library is now
        available.

    .. change:: Increased verbosity of validation error response keys
        :type: feature
        :pr: 1774
        :breaking:

        The keys in validation error responses now include the full path to the field
        where the originated.

        An optional ``source`` key has been added, signifying whether the value is from
        the body, a cookie, a header, or a query param.

        .. code-block:: json
            :caption: before

            {
              "status_code": 400,
              "detail": "Validation failed for POST http://localhost:8000/some-route",
              "extra": [
                {"key": "int_param", "message": "value is not a valid integer"},
                {"key": "int_header", "message": "value is not a valid integer"},
                {"key": "int_cookie", "message": "value is not a valid integer"},
                {"key": "my_value", "message": "value is not a valid integer"}
              ]
            }

        .. code-block:: json
            :caption: after

            {
              "status_code": 400,
              "detail": "Validation failed for POST http://localhost:8000/some-route",
              "extra": [
                {"key": "child.my_value", "message": "value is not a valid integer", "source": "body"},
                {"key": "int_param", "message": "value is not a valid integer", "source": "query"},
                {"key": "int_header", "message": "value is not a valid integer", "source": "header"},
                {"key": "int_cookie", "message": "value is not a valid integer", "source": "cookie"},
              ]
            }

    .. change:: ``TestClient`` default timeout
        :type: feature
        :pr: 1840
        :breaking:

        A ``timeout`` parameter was added to

        - :class:`~litestar.testing.TestClient`
        - :class:`~litestar.testing.AsyncTestClient`
        - :class:`~litestar.testing.create_test_client`
        - :class:`~litestar.testing.create_async_test_client`

        The value is passed down to the underlying HTTPX client and serves as a default
        timeout for all requests.

    .. change:: SQLAlchemy DTO: Explicit error messages when type annotations for a column are missing
        :type: feature
        :pr: 1852

        Replace the nondescript :exc:`KeyError` raised when a SQLAlchemy DTO is
        constructed from a model that is missing a type annotation for an included
        column with an :exc:`ImproperlyConfiguredException`, including an explicit error
        message, pointing at the potential cause.

    .. change:: Remove exception details from Internal Server Error responses
        :type: bugfix
        :pr: 1857
        :issue: 1856

        Error responses with a ``500`` status code will now always use
        `"Internal Server Error"` as default detail.

    .. change:: Pydantic v1 regex validation
        :type: bugfix
        :pr: 1865
        :issue: 1860

        A regression has been fixed in the Pydantic signature model logic, which was
        caused by the renaming of ``regex`` to ``pattern``, which would lead to the
        :attr:`~litestar.params.KwargDefinition.pattern` not being validated.


.. changelog:: 2.0.0beta1
    :date: 2023/06/16

    .. change:: Expose ``ParsedType`` as public API
        :type: feature
        :pr: 1677 1567

        Expose the previously private :class:`litestar.typing.ParsedType`. This is
        mainly indented for usage with
        :meth:`litestar.plugins.SerializationPluginProtocol.supports_type`

    .. change:: Improved debugging capabilities
        :type: feature
        :pr: 1742

        - A new ``pdb_on_exception`` parameter was added to
          :class:`~litestar.app.Litestar`. When set to ``True``, Litestar will drop into
          a the Python debugger when an exception occurs. It defaults to ``None``
        - When ``pdb_on_exception`` is ``None``, setting the environment variable
          ``LITESTAR_PDB=1`` can be used to enable this behaviour
        - When using the CLI, passing the ``--pdb`` flag to the ``run`` command will
          temporarily set the environment variable ``LITESTAR_PDB=1``

    .. change:: OpenAPI: Add `operation_class` argument to HTTP route handlers
        :type: feature
        :pr: 1732

        The ``operation_class`` argument was added to
        :class:`~litestar.handlers.HTTPRouteHandler` and the corresponding decorators,
        allowing to override the :class:`~litestar.openapi.spec.Operation` class, to
        enable further customization of the generated OpenAPI schema.

    .. change:: OpenAPI: Support nested ``Literal`` annotations
        :type: feature
        :pr: 1829

        Support nested :class:`typing.Literal` annotations by flattening them into
        a single ``Literal``.

    .. change:: CLI: Add ``--reload-dir`` option to ``run`` command
        :type: feature
        :pr: 1689

        A new ``--reload-dir`` option was added to the ``litestar run`` command. When
        used, ``--reload`` is implied, and the server will watch for changes in the
        given directory.

    .. change:: Allow extra attributes on JWTs via ``extras`` attribute
        :type: feature
        :pr: 1695

        Add the ``litestar.contrib.jwt.Token.extras`` attribute, containing extra
        attributes found on the JWT.

    .. change:: Add default modes for ``Websocket.iter_json`` and ``WebSocket.iter_data``
        :type: feature
        :pr: 1733

        Add a default ``mode`` for :meth:`~litestar.connection.WebSocket.iter_json` and
        :meth:`~litestar.connection.WebSocket.iter_data`, with a value of ``text``.

    .. change:: SQLAlchemy repository: Synchronous repositories
        :type: feature
        :pr: 1683

        Add a new synchronous repository base class:
        ``litestar.contrib.sqlalchemy.repository.SQLAlchemySyncRepository``,
        which offer the same functionality as its asynchronous counterpart while
        operating on a synchronous :class:`sqlalchemy.orm.Session`.

    .. change:: SQLAlchemy repository: Oracle Database support
        :type: feature
        :pr: 1694

        Add support for Oracle Database via
        `oracledb <https://oracle.github.io/python-oracledb/>`_.

    .. change:: SQLAlchemy repository: DuckDB support
        :type: feature
        :pr: 1744

        Add support for `DuckDB <https://duckdb.org/>`_.

    .. change:: SQLAlchemy repository: Google Spanner support
        :type: feature
        :pr: 1744

        Add support for `Google Spanner <https://cloud.google.com/spanner>`_.

    .. change:: SQLAlchemy repository: JSON check constraint for Oracle Database
        :type: feature
        :pr: 1780

        When using the :class:`litestar.contrib.sqlalchemy.types.JsonB` type with an
        Oracle Database engine, a JSON check constraint will be created for that
        column.

    .. change:: SQLAlchemy repository: Remove ``created`` and ``updated`` columns
        :type: feature
        :pr: 1816
        :breaking:

        The ``created`` and ``updated`` columns have been superseded by
        ``created_at`` and ``updated_at`` respectively, to prevent name clashes.


    .. change:: SQLAlchemy repository: Add timezone aware type
        :type: feature
        :pr: 1816
        :breaking:

        A new timezone aware type ``litestar.contrib.sqlalchemy.types.DateTimeUTC``
        has been added, which enforces UTC timestamps stored in the database.

    .. change:: SQLAlchemy repository: Exclude unloaded columns in ``to_dict``
        :type: feature
        :pr: 1802

        When exporting models using the
        ``~litestar.contrib.sqlalchemy.base.CommonTableAttributes.to_dict`` method,
        unloaded columns will now always be excluded. This prevents implicit I/O via
        lazy loading, and errors when using an asynchronous session.

    .. change:: DTOs: Nested keyword arguments in ``.create_instance()``
        :type: feature
        :pr: 1741
        :issue: 1727

        The
        :meth:`DTOData.create_instance <litestar.dto.factory.DTOData.create_instance>`
        method now supports providing values for arbitrarily nested data via kwargs
        using a double-underscore syntax, for example
        ``data.create_instance(foo__bar="baz")``.

        .. seealso::
            :ref:`usage/dto/1-abstract-dto:Providing values for nested data`

    .. change:: DTOs: Hybrid properties and association proxies in
        :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>`
        :type: feature
        :pr: 1754 1776

        The :class:`SQLAlchemyDTO (Advanced Alchemy) <advanced_alchemy.extensions.litestar.dto.SQLAlchemyDTO>`
        now supports `hybrid attribute <https://docs.sqlalchemy.org/en/20/orm/extensions/hybrid.html>`_
        and `associationproxy <https://docs.sqlalchemy.org/en/20/orm/extensions/associationproxy.html>`_.

        The generated field will be marked read-only.

    .. change:: DTOs: Transfer to generic collection types
        :type: feature
        :pr: 1764
        :issue: 1763

        DTOs can now be wrapped in generic collection types such as
        :class:`typing.Sequence`. These will be substituted with a concrete and
        instantiable type at run time, e.g. in the case of ``Sequence`` a :class:`list`.

    .. change:: DTOs: Data transfer for non-generic builtin collection annotations
        :type: feature
        :pr: 1799

        Non-parametrized generics in annotations (e.g. ``a: dict``) will now be inferred
        as being parametrized with ``Any``. ``a: dict`` is then equivalent to
        ``a: dict[Any, Any]``.

    .. change:: DTOs: Exclude leading underscore fields by default
        :type: feature
        :pr: 1777
        :issue: 1768
        :breaking:

        Leading underscore fields will not be excluded by default. This behaviour can be
        configured with the newly introduced
        :attr:`~litestar.dto.factory.DTOConfig.underscore_fields_private` configuration
        value, which defaults to ``True``.

    .. change:: DTOs: Msgspec and Pydantic DTO factory implementation
        :type: feature
        :pr: 1712
        :issue: 1531, 1532

        DTO factories for `msgspec <https://jcristharif.com/msgspec/>`_ and
        `Pydantic <https://docs.pydantic.dev/latest/>`_ have been added:

        - :class:`~litestar.contrib.msgspec.MsgspecDTO`
        - :class:`~litestar.contrib.pydantic.PydanticDTO`

    .. change:: DTOs: Arbitrary generic wrappers
        :pr: 1801
        :issue: 1631, 1798

        When a handler returns a type that is not supported by the DTO, but:

        - the return type is generic
        - it has a generic type argument that is supported by the dto
        - the type argument maps to an attribute on the return type

        the DTO operations will be performed on the data retrieved from that attribute
        of the instance returned from the handler, and return the instance.

        The constraints are:

        - the type returned from the handler must be a type that litestar can
          natively encode
        - the annotation of the attribute that holds the data must be a type that DTOs
          can otherwise manage

        .. code-block:: python

            from dataclasses import dataclass
            from typing import Generic, List, TypeVar

            from typing_extensions import Annotated

            from litestar import Litestar, get
            from litestar.dto import DTOConfig
            from litestar.dto.factory.dataclass_factory import DataclassDTO


            @dataclass
            class User:
                name: str
                age: int


            T = TypeVar("T")
            V = TypeVar("V")


            @dataclass
            class Wrapped(Generic[T, V]):
                data: List[T]
                other: V


            @get(dto=DataclassDTO[Annotated[User, DTOConfig(exclude={"age"})]])
            def handler() -> Wrapped[User, int]:
                return Wrapped(
                    data=[User(name="John", age=42), User(name="Jane", age=43)],
                    other=2,
                )


            app = Litestar(route_handlers=[handler])

            # GET "/": {"data": [{"name": "John"}, {"name": "Jane"}], "other": 2}

    .. change:: Store and reuse state `deep_copy` directive when copying state
        :type: bugfix
        :issue: 1674
        :pr: 1678

        App state can be created using ``deep_copy=False``, however state would still be
        deep copied for dependency injection.

        This was fixed memoizing the value of ``deep_copy`` when state is created, and
        reusing it on subsequent copies.

    .. change:: ``ParsedType.is_subclass_of(X)`` ``True`` for union if all union types are subtypes of ``X``
        :type: bugfix
        :pr: 1690
        :issue: 1652

        When :class:`~litestar.typing.ParsedType` was introduced,
        :meth:`~litestar.typing.ParsedType.is_subclass_of` any union was deliberately
        left to return ``False`` with the intention of waiting for some use-cases to
        arrive.

        This behaviour was changed to address an issue where a handler may be typed to
        return a union of multiple response types; If all response types are
        :class:`~litestar.response.Response` subtypes then the correct response handler
        will now be applied.

    .. change:: Inconsistent template autoescape behavior
        :type: bugfix
        :pr: 1718
        :issue: 1699

        The mako template engine now defaults to autoescaping expressions, making it
        consistent with config of Jinja template engine.

    .. change:: Missing ``ChannelsPlugin`` in signature namespace population
        :type: bugfix
        :pr: 1719
        :issue: 1691

        The :class:`~litestar.channels.plugin.ChannelsPlugin` has been added to the
        signature namespace, fixing an issue where using
        ``from __future__ import annotations`` or stringized annotations would lead to
        a :exc:`NameError`, if the plugin was not added to the signatured namespace
        manually.

    .. change:: Gzip middleware not sending small streaming responses
        :type: bugfix
        :pr: 1723
        :issue: 1681

        A bug was fixed that would cause smaller streaming responses to not be sent at
        all when the :class:`~litestar.middleware.compression.CompressionMiddleware` was
        used with ``gzip``.

    .. change:: Premature transfer to nested models with `DTOData`
        :type: bugfix
        :pr: 1731
        :issue: 1726

        An issue was fixed where data that should be transferred to builtin types on
        instantiation of :class:`~litestar.dto.factory.DTOData` was being instantiated
        into a model type for nested models.

    .. change:: Incorrect ``sync_to_thread`` usage warnings for generator dependencies
        :type: bugfix
        :pr: 1716 1740
        :issue: 1711

        A bug was fixed that caused incorrect warnings about missing ``sync_to_thread``
        usage were issues when asynchronous generators were being used as dependencies.

    .. change:: Dependency injection custom dependencies in ``WebSocketListener``
        :type: bugfix
        :pr: 1807
        :issue: 1762

        An issue was resolved that would cause failures when dependency injection was
        being used with custom dependencies (that is, injection of things other than
        ``state``, ``query``, path parameters, etc.) within a
        :class:`~litestar.handlers.WebsocketListener`.

    .. change:: OpenAPI schema for ``Dict[K, V]`` ignores generic
        :type: bugfix
        :pr: 1828
        :issue: 1795

        An issue with the OpenAPI schema generation was fixed that would lead to generic
        arguments to :class:`dict` being ignored.

        An type like ``dict[str, int]`` now correctly renders as
        ``{"type": "object", "additionalProperties": { "type": "integer" }}``.

    .. change:: ``WebSocketTestSession`` not timing out without when connection is not accepted
        :type: bugfix
        :pr: 1696

        A bug was fixed that caused :class:`~litestar.testing.WebSocketTestSession` to
        block indefinitely when if :meth:`~litestar.connection.WebSocket.accept` was
        never called, ignoring the ``timeout`` parameter.

    .. change:: SQLAlchemy repository: Fix alembic migrations generated for models using ``GUID``
        :type: bugfix
        :pr: 1676

        Migrations generated for models with a
        ``~litestar.contrib.sqlalchemy.types.GUID`` type would erroneously add a
        ``length=16`` on the input.  Since this parameter is not defined in the type's
        the ``__init__`` method. This was fixed by adding the appropriate parameter to
        the type's signature.

    .. change:: Remove ``state`` parameter from ``AfterExceptionHookHandler`` and ``BeforeMessageSendHookHandler``
        :type: misc
        :pr: 1739
        :breaking:

        Remove the ``state`` parameter from ``AfterExceptionHookHandler`` and
        ``BeforeMessageSendHookHandler``.

        ``AfterExceptionHookHandler``\ s will have to be updated from

        .. code-block:: python

            async def after_exception_handler(
                exc: Exception, scope: Scope, state: State
            ) -> None: ...

        to

        .. code-block:: python

            async def after_exception_handler(exc: Exception, scope: Scope) -> None: ...

        The state can still be accessed like so:

        .. code-block:: python

            async def after_exception_handler(exc: Exception, scope: Scope) -> None:
                state = scope["app"].state


        ``BeforeMessageSendHookHandler``\ s will have to be updated from

        .. code-block:: python

            async def before_send_hook_handler(
                message: Message, state: State, scope: Scope
            ) -> None: ...


        to

        .. code-block:: python

            async def before_send_hook_handler(message: Message, scope: Scope) -> None: ...

        where state can be accessed in the same manner:

        .. code-block:: python

            async def before_send_hook_handler(message: Message, scope: Scope) -> None:
                state = scope["app"].state

    .. change:: Removal of ``dto.exceptions`` module
        :pr: 1773
        :breaking:

        The module ``dto.exceptions`` has been removed, since it was not used anymore
        internally by the DTO implementations, and superseded by standard exceptions.


    .. change:: ``BaseRouteHandler`` no longer generic
        :pr: 1819
        :breaking:

        :class:`~litestar.handlers.BaseRouteHandler` was originally made generic to
        support proper typing of the ``ownership_layers`` property, but the same effect
        can now be achieved using :class:`typing.Self`.

    .. change:: Deprecation of ``Litestar`` parameter ``preferred_validation_backend``
        :pr: 1810
        :breaking:

        The following changes have been made regarding the
        ``preferred_validation_backend``:

        - The ``preferred_validation_backend`` parameter of
          :class:`~litestar.app.Litestar` has been renamed to
          ``_preferred_validation_backend`` and deprecated. It will be removed
          completely in a future version.
        - The ``Litestar.preferred_validation_backend`` attribute has been made private
        - The ``preferred_validation_backend`` attribute has been removed from
          :class:`~litestar.config.app.AppConfig`

        In addition, the logic for selecting a signature validation backend has been
        simplified as follows: If the preferred backend is set to ``attrs``, or the
        signature contains attrs types, ``attrs`` is selected. In all other cases,
        Pydantic will be used.

    .. change:: ``Response.get_serializer`` moved to ``serialization.get_serializer``
        :pr: 1820
        :breaking:


        The ``Response.get_serializer()`` method has been removed in favor of the
        :func:`~litestar.serialization.get_serializer` function.

        In the previous :class:`~litestar.response.Response` implementation,
        ``get_serializer()`` was called on the response inside the response's
        ``__init__``, and the merging of class-level ``type_encoders`` with the
        ``Response``\ 's ``type_encoders`` occurred inside its ``get_serializer``
        method.

        In the current version of ``Response``, the response body is not encoded until
        after the response object has been returned from the handler, and it is
        converted into a low-level :class:`~litestar.response.base.ASGIResponse` object.
        Due to this, there is still opportunity for the handler layer resolved
        ``type_encoders`` object to be merged with the ``Response`` defined
        ``type_encoders``, making the merge inside the ``Response`` no longer necessary.

        In addition, the separate ``get_serializer`` function greatly simplifies the
        interaction between middlewares and serializers, allowing to retrieve one
        independently from a ``Response``.

    .. change:: Remove response containers and introduce ``ASGIResponse``
        :pr: 1790
        :breaking:

        Response Containers were wrapper classes used to indicate the type of response
        returned by a handler, for example ``File``, ``Redirect``, ``Template`` and
        ``Stream`` types. These types abstracted the interface of responses from the
        underlying response itself.

        Response containers have been removed and their functionality largely merged with
        that of :class:`~litestar.response.Response`. The predefined response containers
        still exist functionally, as subclasses of
        :class:`Response <.response.Response>` and are now located within the
        :mod:`litestar.response` module.
        In addition to the functionality of Response containers, they now also feature
        all of the response's functionality, such as methods to add headers and cookies.

        The :class:`~litestar.response.Response` class now only serves as a wrapper and
        context object, and does not handle the data sending part, which has been
        delegated to a newly introduced
        :class:`ASGIResponse <.response.base.ASGIResponse>`. This type (and its
        subclasses) represent the response as an immutable object and are used
        internally by Litestar to perform the I/O operations of the response. These can
        be created and returned from handlers like any other ASGI application, however
        they are low-level, and lack the utility of the higher-level response types.



.. changelog:: 2.0.0alpha7
    :date: 2023/05/14

    .. change:: Warn about sync callables in route handlers and dependencies without an explicit ``sync_to_thread`` value
        :type: feature
        :pr: 1648 1655

        A warning will now be raised when a synchronous callable is being used in an
        :class:`~.handlers.HTTPRouteHandler` or :class:`~.di.Provide`, without setting
        ``sync_to_thread``. This is to ensure that synchronous callables are handled
        properly, and to prevent accidentally using callables which might block the main
        thread.

        This warning can be turned off globally by setting the environment variable
        ``LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD=0``.

        .. seealso::
            :doc:`/topics/sync-vs-async`


    .. change:: Warn about ``sync_to_thread`` with async callables
        :type: feature
        :pr: 1664

        A warning will be raised when ``sync_to_thread`` is being used in
        :class:`~.handlers.HTTPRouteHandler` or :class:`~.di.Provide` with an
        asynchronous callable, as this will have no effect.

        This warning can be turned off globally by setting the environment variable
        ``LITESTAR_WARN_SYNC_TO_THREAD_WITH_ASYNC=0``.


    .. change:: WebSockets: Dependencies in listener hooks
        :type: feature
        :pr: 1647

        Dependencies can now be used in the
        :class:`~litestar.handlers.websocket_listener` hooks
        ``on_accept``, ``on_disconnect`` and the ``connection_lifespan`` context
        manager. The ``socket`` parameter is therefore also not mandatory anymore in
        those callables.

    .. change:: Declaring dependencies without ``Provide``
        :type: feature
        :pr: 1647

        Dependencies can now be declared without using :class:`~litestar.di.Provide`.
        The callables can be passed directly to the ``dependencies`` dictionary.


    .. change:: Add ``DTOData`` to receive unstructured but validated DTO data
        :type: feature
        :pr: 1650

        :class:`~litestar.dto.factory.DTOData` is a datastructure for interacting with
        DTO validated data in its unstructured form.

        This utility is to support the case where the amount of data that is available
        from the client request is not complete enough to instantiate an instance of the
        model that would otherwise be injected.


    .. change:: Partial DTOs
        :type: feature
        :pr: 1651

        Add a ``partial`` flag to :class:`~litestar.dto.factory.DTOConfig`, making all
        DTO fields options. Subsequently, any unset values will be filtered when
        extracting data from transfer models.

        This allows for example to use a to handle PATCH requests more easily.


    .. change:: SQLAlchemy repository: ``psycopg`` asyncio support
        :type: feature
        :pr: 1657

        Async `psycopg <https://www.psycopg.org/>`_ is now officially supported and
        tested for the SQLAlchemy repository.

    .. change:: SQLAlchemy repository: ``BigIntPrimaryKey`` mixin
        :type: feature
        :pr: 1657

        ``~litestar.contrib.sqlalchemy.base.BigIntPrimaryKey`` mixin, providing a
        ``BigInt`` primary key column, with a fallback to ``Integer`` for sqlite.

    .. change:: SQLAlchemy repository: Store GUIDs as binary on databases that don't have a native GUID type
        :type: feature
        :pr: 1657

        On databases without native support for GUIDs,
        ``~litestar.contrib.sqlalchemy.types.GUID`` will now fall back to
        ``BINARY(16)``.

    .. change:: Application lifespan context managers
        :type: feature
        :pr: 1635

        A new ``lifespan`` argument has been added to :class:`~litestar.app.Litestar`,
        accepting an asynchronous context manager, wrapping the lifespan of the
        application. It will be entered with the startup phase and exited on shutdown,
        providing functionality equal to the ``on_startup`` and ``on_shutdown`` hooks.

    .. change:: Unify application lifespan hooks: Remove ``before_`` and ``after_``
        :breaking:
        :type: feature
        :pr: 1663

        The following application lifespan hooks have been removed:

        - ``before_startup``
        - ``after_startup``
        - ``before_shutdown``
        - ``after_shutdown``

        The remaining hooks ``on_startup`` and ``on_shutdown`` will now receive as their
        optional first argument the :class:`~litestar.app.Litestar` application instead
        of the application's state.

    .. change:: Trio-compatible event emitter
        :type: feature
        :pr: 1666

        The default :class:`~litestar.events.emitter.SimpleEventEmitter` is now
        compatible with `trio <https://trio.readthedocs.io/en/stable/>`_.


    .. change:: OpenAPI: Support ``msgspec.Meta``
        :type: feature
        :pr: 1669

        :class:`msgspec.Meta` is now fully supported for OpenAPI schema generation.

    .. change:: OpenAPI: Support Pydantic ``FieldInfo``
        :type: feature
        :pr: 1670
        :issue: 1541

        Pydantic's ``FieldInfo`` (``regex``, ``gt``, ``title``, etc.) now have full
        support for OpenAPI schema generation.

    .. change:: OpenAPI: Fix name collision in DTO models
        :type: bugfix
        :pr: 1649
        :issue: 1643

        A bug was fixed that would lead to name collisions in the OpenAPI schema when
        using DTOs with the same class name. DTOs now include a short 8 byte random
        string in their generated name to prevent this.

    .. change:: Fix validated attrs model being injected as a dictionary
        :type: bugfix
        :pr: 1668
        :issue: 1643

        A bug was fixed that would lead to an attrs model used to validate a route
        handler's ``data`` not being injected itself but as a dictionary representation.


    .. change:: Validate unknown media types
        :breaking:
        :type: bugfix
        :pr: 1671
        :issue: 1446

        An unknown media type in places where Litestar can't infer the type from the
        return annotation, an :exc:`ImproperlyConfiguredException` will now be raised.


.. changelog:: 2.0.0alpha6
    :date: 2023/05/09

    .. change:: Relax typing of ``**kwargs`` in ``ASGIConnection.url_for``
        :type: bugfix
        :pr: 1610

        Change the typing of the ``**kwargs`` in
        :meth:`ASGIConnection.url_for <litestar.connection.ASGIConnection.url_for>` from
        ``dict[str, Any]`` to ``Any``


    .. change:: Fix: Using ``websocket_listener`` in controller causes ``TypeError``
        :type: bugfix
        :pr: 1627
        :issue: 1615

        A bug was fixed that would cause a type error when using a
        :class:`websocket_listener <litestar.handlers.websocket_listener>`
        in a ``Controller``

    .. change:: Add ``connection_accept_handler`` to ``websocket_listener``
        :type: feature
        :pr: 1572
        :issue: 1571

        Add a new ``connection_accept_handler`` parameter to
        :class:`websocket_listener <litestar.handlers.websocket_listener>`,
        which can be used to customize how a connection is accepted, for example to
        add headers or subprotocols

    .. change:: Testing: Add ``block`` and ``timeout`` parameters to ``WebSocketTestSession`` receive methods
        :type: feature
        :pr: 1593

        Two parameters, ``block`` and ``timeout`` have been added to the following methods:

        - :meth:`receive <litestar.testing.WebSocketTestSession.receive>`
        - :meth:`receive_text <litestar.testing.WebSocketTestSession.receive_text>`
        - :meth:`receive_bytes <litestar.testing.WebSocketTestSession.receive_bytes>`
        - :meth:`receive_json <litestar.testing.WebSocketTestSession.receive_json>`

    .. change:: CLI: Add ``--app-dir`` option to root command
        :type: feature
        :pr: 1506

        The ``--app-dir`` option was added to the root CLI command, allowing to set the
        run applications from a path that's not the current working directory.


    .. change:: WebSockets: Data iterators
        :type: feature
        :pr: 1626

        Two new methods were added to the :class:`WebSocket <litestar.connection.WebSocket>`
        connection, which allow to continuously receive data and iterate over it:

        - :meth:`iter_data <litestar.connection.WebSocket.iter_data>`
        - :meth:`iter_json <litestar.connection.WebSocket.iter_json>`


    .. change:: WebSockets: MessagePack support
        :type: feature
        :pr: 1626

        Add support for `MessagePack <https://msgpack.org/index.html>`_ to the
        :class:`WebSocket <litestar.connection.WebSocket>` connection.

        Three new methods have been added for handling MessagePack:

        - :meth:`send_msgpack <litestar.connection.WebSocket.send_msgpack>`
        - :meth:`receive_msgpack <litestar.connection.WebSocket.receive_msgpack>`
        - :meth:`iter_msgpack <litestar.connection.WebSocket.iter_msgpack>`

        In addition, two MessagePack related methods were added to
        :class:`WebSocketTestSession <litestar.testing.WebSocketTestSession>`:

        - :meth:`send_msgpack <litestar.testing.WebSocketTestSession.send_msgpack>`
        - :meth:`receive_msgpack <litestar.testing.WebSocketTestSession.receive_msgpack>`

    .. change:: SQLAlchemy repository: Add support for sentinel column
        :type: feature
        :pr: 1603

        This change adds support for ``sentinel column`` feature added in ``sqlalchemy``
        2.0.10. Without it, there are certain cases where ``add_many`` raises an
        exception.

        The ``_sentinel`` value added to the declarative base should be excluded from
        normal select operations automatically and is excluded in the ``to_dict``
        methods.

    .. change:: DTO: Alias generator for field names
        :type: feature
        :pr: 1590

        A new argument ``rename_strategy`` has been added to the :class:`DTOConfig <litestar.dto.factory.DTOConfig>`,
        allowing to remap field names with strategies such as "camelize".

    .. change:: DTO: Nested field exclusion
        :type: feature
        :pr: 1596
        :issue: 1197

        This feature adds support for excluding nested model fields using dot-notation,
        e.g., ``"a.b"`` excludes field ``b`` from nested model field ``a``

    .. change:: WebSockets: Managing a socket's lifespan using a context manager in websocket listeners
        :type: feature
        :pr: 1625

        Changes the way a socket's lifespan - accepting the connection and calling the
        appropriate event hooks - to use a context manager.

        The ``connection_lifespan`` argument was added to the
        :class:`WebSocketListener <litestar.handlers.websocket_listener>`, which accepts
        an asynchronous context manager, which can be used to handle the lifespan of
        the socket.

    .. change:: New module: Channels
        :type: feature
        :pr: 1587

        A new module :doc:`channels </usage/channels>` has been added: A general purpose
        event streaming library, which can for example be used to broadcast messages
        via WebSockets.

    .. change:: DTO: Undocumented ``dto.factory.backends`` has been made private
        :breaking:
        :type: misc
        :pr: 1589

        The undocumented ``dto.factory.backends`` module has been made private



.. changelog:: 2.0.0alpha5

    .. change:: Pass template context to HTMX template response
        :type: feature
        :pr: 1488

        Pass the template context to the :class:`Template <litestar.response_containers.Template>` returned by
        :class:`htmx.Response <litestar.contrib.htmx.response>`.


    .. change:: OpenAPI support for attrs and msgspec classes
        :type: feature
        :pr: 1487

        Support OpenAPI schema generation for `attrs <https://www.attrs.org>`_ classes and
        `msgspec <https://jcristharif.com/msgspec/>`_ ``Struct``\ s.

    .. change:: SQLAlchemy repository: Add ``ModelProtocol``
        :type: feature
        :pr: 1503

        Add a new class ``contrib.sqlalchemy.base.ModelProtocol``, serving as a generic model base type, allowing to
        specify custom base classes while preserving typing information

    .. change:: SQLAlchemy repository: Support MySQL/MariaDB
        :type: feature
        :pr: 1345

        Add support for MySQL/MariaDB to the SQLAlchemy repository, using the
        `asyncmy <https://github.com/long2ice/asyncmy>`_ driver.

    .. change:: SQLAlchemy repository: Support MySQL/MariaDB
        :type: feature
        :pr: 1345

        Add support for MySQL/MariaDB to the SQLAlchemy repository, using the
        `asyncmy <https://github.com/long2ice/asyncmy>`_ driver.

    .. change:: SQLAlchemy repository: Add matching logic to ``get_or_create``
        :type: feature
        :pr: 1345

        Add a ``match_fields`` argument to
        ``litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository.get_or_create``.
        This lets you lookup a model using a subset of the kwargs you've provided. If the remaining kwargs are different
        from the retrieved model's stored values, an update is performed.

    .. change:: Repository: Extend filter types
        :type: feature
        :pr: 1345

        Add new filters ``litestar.contrib.repository.filters.OrderBy`` and
        ``litestar.contrib.repository.filters.SearchFilter``, providing ``ORDER BY ...`` and
        ``LIKE ...`` / ``ILIKE ...`` clauses respectively

    .. change:: SQLAlchemy repository: Rename ``SQLAlchemyRepository`` > ``SQLAlchemyAsyncRepository``
        :breaking:
        :type: misc
        :pr: 1345

        ``SQLAlchemyRepository`` has been renamed to
        ``litestar.contrib.sqlalchemy.repository.SQLAlchemyAsyncRepository``.


    .. change:: DTO: Add ``AbstractDTOFactory`` and backends
        :type: feature
        :pr: 1461

        An all-new DTO implementation was added, using ``AbstractDTOFactory`` as a base class, providing Pydantic and
        msgspec backends to facilitate (de)serialization and validation.

    .. change:: DTO: Remove ``from_connection`` / extend ``from_data``
        :breaking:
        :type: misc
        :pr: 1500

        The method ``DTOInterface.from_connection`` has been removed and replaced by ``DTOInterface.from_bytes``, which
        receives both the raw bytes from the connection, and the connection instance. Since ``from_bytes`` now does not
        handle connections anymore, it can also be a synchronous method, improving symmetry with
        ``DTOInterface.from_bytes``.

        The signature of ``from_data`` has been changed to also accept the connection, matching ``from_bytes``'
        signature.

        As a result of these changes,
        :meth:`DTOInterface.from_bytes <litestar.dto.interface.DTOInterface.data_to_encodable_type>` no longer needs to
        receive the connection instance, so the ``request`` parameter has been dropped.

    .. change:: WebSockets: Support DTOs in listeners
        :type: feature
        :pr: 1518

        Support for DTOs has been added to :class:`WebSocketListener <litestar.handlers.WebsocketListener>` and
        :class:`WebSocketListener <litestar.handlers.websocket_listener>`. A ``dto`` and ``return_dto`` parameter has
        been added, providing the same functionality as their route handler counterparts.

    .. change:: DTO based serialization plugin
        :breaking:
        :type: feature
        :pr: 1501

        :class:`SerializationPluginProtocol <litestar.plugins.SerializationPluginProtocol>` has been re-implemented,
        leveraging the new :class:`DTOInterface <litestar.dto.interface.DTOInterface>`.

        If a handler defines a plugin supported type as either the ``data`` kwarg type annotation, or as the return
        annotation for a handler function, and no DTO has otherwise been resolved to handle the type, the protocol
        creates a DTO implementation to represent that type which is then used to de-serialize into, and serialize from
        instances of that supported type.

        .. important::
            The `Piccolo ORM <https://piccolo-orm.com/>`_ and `Tortoise ORM <https://tortoise.github.io/>`_ plugins have
            been removed by this change, but will be re-implemented using the new patterns in a future release leading
            up to the 2.0 release.

    .. change:: SQLAlchemy 1 contrib module removed
        :breaking:
        :type: misc
        :pr: 1501

        As a result of the changes introduced in `#1501 <https://github.com/litestar-org/litestar/pull/1501>`_,
        SQLAlchemy 1 support has been dropped.

        .. note::
            If you rely on SQLAlchemy 1, you can stick to Starlite *1.51* for now. In the future, a SQLAlchemy 1 plugin
            may be released as a standalone package.

    .. change:: Fix inconsistent parsing of unix timestamp between Pydantic and cattrs
        :type: bugfix
        :pr: 1492
        :issue: 1491

        Timestamps parsed as :class:`date <datetime.date>` with Pydantic return a UTC date, while cattrs implementation
        return a date with the local timezone.

        This was corrected by forcing dates to UTC when being parsed by attrs.

    .. change:: Fix: Retrieve type hints from class with no ``__init__`` method causes error
        :type: bugfix
        :pr: 1505
        :issue: 1504

        An error would occur when using a callable without an :meth:`object.__init__` method was used in a placed that
        would cause it to be inspected (such as a route handler's signature).

        This was caused by trying to access the ``__module__`` attribute of :meth:`object.__init__`, which would fail
        with

        .. code-block::

            'wrapper_descriptor' object has no attribute '__module__'

    .. change:: Fix error raised for partially installed attrs dependencies
        :type: bugfix
        :pr: 1543

        An error was fixed that would cause a :exc:`MissingDependencyException` to be raised when dependencies for
        `attrs <https://www.attrs.org>`_ were partially installed. This was fixed by being more specific about the
        missing dependencies in the error messages.

    .. change:: Change ``MissingDependencyException`` to be a subclass of ``ImportError``
        :type: misc
        :pr: 1557

        :exc:`MissingDependencyException` is now a subclass of :exc:`ImportError`, to make handling cases where both
        of them might be raised easier.

    .. change:: Remove bool coercion in URL parsing
        :breaking:
        :type: bugfix
        :pr: 1550
        :issue: 1547

        When defining a query parameter as ``param: str``, and passing it a string value of ``"true"``, the value
        received by the route handler was the string ``"True"``, having been title cased. The same was true for the value
        of ``"false"``.

        This has been fixed by removing the coercing of boolean-like values during URL parsing and leaving it up to
        the parsing utilities of the receiving side (i.e. the handler's signature model) to handle these values
        according to the associated type annotations.

    .. change:: Update ``standard`` and ``full`` package extras
        :type: misc
        :pr: 1494

        - Add SQLAlchemy, uvicorn, attrs and structlog to the ``full`` extra
        - Add uvicorn to the ``standard`` extra
        - Add ``uvicorn[standard]`` as an optional dependency to be used in the extras

    .. change:: Remove support for declaring DTOs as handler types
        :breaking:
        :type: misc
        :pr: 1534

        Prior to this, a DTO type could be declared implicitly using type annotations. With the addition of the ``dto``
        and ``return_dto`` parameters, this feature has become superfluous and, in the spirit of offering only one clear
        way of doing things, has been removed.

    .. change:: Fix missing ``content-encoding`` headers on gzip/brotli compressed files
        :type: bugfix
        :pr: 1577
        :issue: 1576

        Fixed a bug that would cause static files served via ``StaticFilesConfig`` that have been compressed with gripz
        or brotli to miss the appropriate ``content-encoding`` header.

    .. change:: DTO: Simplify ``DTOConfig``
        :type: misc
        :breaking:
        :pr: 1580

        - The ``include`` parameter has been removed, to provide a more accessible interface and avoid overly complex
          interplay with ``exclude`` and its support for dotted attributes
        - ``field_mapping`` has been renamed to ``rename_fields`` and support to remap field types has been dropped
        - experimental ``field_definitions`` has been removed. It may be replaced with a "ComputedField" in a future
          release that will allow multiple field definitions to be added to the model, and a callable that transforms
          them into a value for a model field. See


.. changelog:: 2.0.0alpha4

    .. change:: ``attrs`` and ``msgspec`` support in :class:`Partial <litestar.partial.Partial>`
        :type: feature
        :pr: 1462

        :class:`Partial <litestar.partial.Partial>` now supports constructing partial models for attrs and msgspec

    .. change:: :class:`Annotated <typing.Annotated>` support for route handler and dependency annotations
        :type: feature
        :pr: 1462

        :class:`Annotated <typing.Annotated>` can now be used in route handler and dependencies to specify additional
        information about the fields.

        .. code-block:: python

            @get("/")
            def index(param: int = Parameter(gt=5)) -> dict[str, int]: ...

        .. code-block:: python

            @get("/")
            def index(param: Annotated[int, Parameter(gt=5)]) -> dict[str, int]: ...

    .. change:: Support ``text/html`` Media-Type in ``Redirect`` response container
        :type: bugfix
        :issue: 1451
        :pr: 1474

        The media type in :class:`Redirect <litestar.response.RedirectResponse>` won't be forced to ``text/plain`` anymore and
        now supports setting arbitrary media types.


    .. change:: Fix global namespace for type resolution
        :type: bugfix
        :pr: 1477
        :issue: 1472

        Fix a bug where certain annotations would cause a :exc:`NameError`


    .. change:: Add uvicorn to ``cli`` extra
        :type: bugfix
        :issue: 1478
        :pr: 1480

        Add the ``uvicorn`` package to the ``cli`` extra, as it is required unconditionally


    .. change:: Update logging levels when setting ``Litestar.debug`` dynamically
        :type: bugfix
        :issue: 1476
        :pr: 1482

        When passing ``debug=True`` to :class:`Litestar <litestar.app.Litestar>`, the ``litestar`` logger would be set
        up in debug mode, but changing the ``debug`` attribute after the class had been instantiated did not update the
        logger accordingly.

        This lead to a regression where the ``--debug`` flag to the CLI's ``run`` command would no longer have the
        desired affect, as loggers would still be on the ``INFO`` level.


.. changelog:: 2.0.0alpha3

    .. change:: SQLAlchemy 2.0 Plugin
        :type: feature
        :pr: 1395

        A :class:`SQLAlchemyInitPlugin <litestar.contrib.sqlalchemy.plugins.SQLAlchemyInitPlugin>` was added,
        providing support for managed synchronous and asynchronous sessions.

        .. seealso::
            :doc:`/usage/databases/sqlalchemy/index`

    .. change:: Attrs signature modelling
        :type: feature
        :pr: 1382

        Added support to model route handler signatures with attrs instead of Pydantic

    .. change:: Support setting status codes in ``Redirect`` container
        :type: feature
        :pr: 1412
        :issue: 1371

        Add support for manually setting status codes in the
        :class:`RedirectResponse <litestar.response_containers.Redirect>` response container.
        This was previously only possible by setting the ``status_code`` parameter on
        the corresponding route handler, making dynamic redirect status codes and
        conditional redirects using this container hard to implement.

    .. change:: Sentinel value to support caching responses indefinitely
        :type: feature
        :pr: 1414
        :issue: 1365

        Add the :class:`CACHE_FOREVER <litestar.config.response_cache.CACHE_FOREVER>` sentinel value, that, when passed
        to a route handlers ``cache argument``, will cause it to be cached forever, skipping the default expiration.

        Additionally, add support for setting
        :attr:`ResponseCacheConfig.default_expiration <litestar.config.response_cache.ResponseCacheConfig>` to ``None``,
        allowing to cache values indefinitely by default when setting ``cache=True`` on a route handler.

    .. change:: `Accept`-header parsing and content negotiation
        :type: feature
        :pr: 1317

        Add an :attr:`accept <litestar.connection.Request.accept>` property to
        :class:`Request <litestar.connection.Request>`, returning the newly added
        :class:`Accept <litestar.datastructures.headers.Accept>` header wrapper, representing the requests ``Accept``
        HTTP header, offering basic content negotiation.

        .. seealso::
            :ref:`usage/responses:Content Negotiation`

    .. change:: Enhanced WebSockets support
        :type: feature
        :pr: 1402

        Add a new set of features for handling WebSockets, including automatic connection handling, (de)serialization
        of incoming and outgoing data analogous to route handlers and OOP based event dispatching.

        .. seealso::
            :doc:`/usage/websockets`

    .. change:: SQLAlchemy 1 plugin mutates app state destructively
        :type: bugfix
        :pr: 1391
        :issue: 1368

        When using the SQLAlchemy 1 plugin, repeatedly running through the application lifecycle (as done when testing
        an application not provided by a factory function), would result in a :exc:`KeyError` on the second pass.

        This was caused be the plugin's ``on_shutdown`` handler deleting the ``engine_app_state_key`` from the
        application's state on application shutdown, but only adding it on application init.

        This was fixed by adding performing the necessary setup actions on application startup rather than init.

    .. change:: Fix SQLAlchemy 1 Plugin - ``'Request' object has no attribute 'dict'``
        :type: bugfix
        :pr: 1389
        :issue: 1388

        An annotation such as

        .. code-block:: python

            async def provide_user(request: Request[User, Token, Any]) -> User: ...

        would result in the error ``'Request' object has no attribute 'dict'``.

        This was fixed by changing how ``get_plugin_for_value`` interacts with :func:`typing.get_args`

    .. change:: Support OpenAPI schema generation with stringized return annotation
        :type: bugfix
        :pr: 1410
        :issue: 1409

        The following code would result in non-specific and incorrect information being generated for the OpenAPI schema:

        .. code-block:: python

            from __future__ import annotations

            from starlite import Starlite, get


            @get("/")
            def hello_world() -> dict[str, str]:
                return {"hello": "world"}

        This could be alleviated by removing ``from __future__ import annotations``. Stringized annotations in any form
        are now fully supported.

    .. change:: Fix OpenAPI schema generation crashes for models with ``Annotated`` type attribute
        :type: bugfix
        :issue: 1372
        :pr: 1400

        When using a model that includes a type annotation with :class:`typing.Annotated` in a route handler, the
        interactive documentation would raise an error when accessed. This has been fixed and :class:`typing.Annotated`
        is now fully supported.

    .. change:: Support empty ``data`` in ``RequestFactory``
        :type: bugfix
        :issue: 1419
        :pr: 1420

        Add support for passing an empty ``data`` parameter to a
        :class:`RequestFactory <litestar.testing.RequestFactory>`, which would previously lead to an error.

    .. change:: ``create_test_client`` and ``crate_async_test_client`` signatures and docstrings to to match ``Litestar``
        :type: misc
        :pr: 1417

        Add missing parameters to :func:`create_test_client <litestar.testing.create_test_client>` and
        :func:`create_test_client <litestar.testing.create_async_test_client>`. The following parameters were added:

        - ``cache_control``
        - ``debug``
        - ``etag``
        - ``opt``
        - ``response_cache_config``
        - ``response_cookies``
        - ``response_headers``
        - ``security``
        - ``stores``
        - ``tags``
        - ``type_encoders``



.. changelog:: 2.0.0alpha2

    .. change:: Repository contrib & SQLAlchemy repository
        :type: feature
        :pr: 1254

        Add a a ``repository`` module to ``contrib``, providing abstract base classes
        to implement the repository pattern. Also added was the ``contrib.repository.sqlalchemy``
        module, implementing a SQLAlchemy repository, offering hand-tuned abstractions
        over commonly used tasks, such as handling of object sessions, inserting,
        updating and upserting individual models or collections.

    .. change:: Data stores & registry
        :type: feature
        :pr: 1330
        :breaking:

        The ``starlite.storage`` module added in the previous version has been
        renamed ``starlite.stores`` to reduce ambiguity, and a new feature, the
        ``starlite.stores.registry.StoreRegistry`` has been introduced;
        It serves as a central place to manage stores and reduces the amount of
        configuration needed for various integrations.

        - Add ``stores`` kwarg to ``Starlite`` and ``AppConfig`` to allow seeding of the ``StoreRegistry``
        - Add ``Starlite.stores`` attribute, containing a ``StoreRegistry``
        - Change ``RateLimitMiddleware`` to use ``app.stores``
        - Change request caching to use ``app.stores``
        - Change server side sessions to use ``app.stores``
        - Move ``starlite.config.cache.CacheConfig`` to  ``starlite.config.response_cache.ResponseCacheConfig``
        - Rename ``Starlite.cache_config`` > ``Starlite.response_cache_config``
        - Rename ``AppConfig.cache_config`` > ``response_cache_config``
        - Remove ``starlite/cache`` module
        - Remove ``ASGIConnection.cache`` property
        - Remove ``Starlite.cache`` attribute

        .. attention::
            ``starlite.middleware.rate_limit.RateLimitMiddleware``,
            ``starlite.config.response_cache.ResponseCacheConfig``,
            and ``starlite.middleware.session.server_side.ServerSideSessionConfig``
            instead of accepting a ``storage`` argument that could be passed a ``Storage`` instance now have to be
            configured via the ``store`` attribute, accepting a string key for the store to be used from the registry.
            The ``store`` attribute has a unique default set, guaranteeing a unique
            ``starlite.stores.memory.MemoryStore`` instance is acquired for every one of them from the
            registry by default

        .. seealso::

            :doc:`/usage/stores`


    .. change:: Add ``starlite.__version__``
        :type: feature
        :pr: 1277

        Add a ``__version__`` constant to the ``starlite`` namespace, containing a
        :class:`NamedTuple <typing.NamedTuple>`, holding information about the currently
        installed version of Starlite


    .. change:: Add ``starlite version`` command to CLI
        :type: feature
        :pr: 1322

        Add a new ``version`` command to the CLI which displays the currently installed
        version of Starlite


    .. change:: Enhance CLI autodiscovery logic
        :type: feature
        :breaking:
        :pr: 1322

        Update the CLI :ref:`usage/cli:autodiscovery` to only consider canonical modules app and application, but every
        ``starlite.app.Starlite`` instance or application factory able to return a ``Starlite`` instance within
        those or one of their submodules, giving priority to the canonical names app and application for application
        objects and submodules containing them.

        .. seealso::
            :ref:`CLI autodiscovery <usage/cli:autodiscovery>`

    .. change:: Configurable exception logging and traceback truncation
        :type: feature
        :pr: 1296

        Add three new configuration options to ``starlite.logging.config.BaseLoggingConfig``:

        ``starlite.logging.config.LoggingConfig.log_exceptions``
            Configure when exceptions are logged.

            ``always``
                Always log exceptions

            ``debug``
                Log exceptions in debug mode only

            ``never``
                Never log exception

        ``starlite.logging.config.LoggingConfig.traceback_line_limit``
            Configure how many lines of tracback are logged

        ``starlite.logging.config.LoggingConfig.exception_logging_handler``
            A callable that receives three parameters - the ``app.logger``, the connection scope and the traceback
            list, and should handle logging

        .. seealso::
            ``starlite.logging.config.LoggingConfig``


    .. change:: Allow overwriting default OpenAPI response descriptions
        :type: bugfix
        :issue: 1292
        :pr: 1293

        Fix https://github.com/litestar-org/litestar/issues/1292 by allowing to overwrite
        the default OpenAPI response description instead of raising :exc:`ImproperlyConfiguredException`.


    .. change:: Fix regression in path resolution that prevented 404's being raised for false paths
        :type: bugfix
        :pr: 1316
        :breaking:

        Invalid paths within controllers would under specific circumstances not raise a 404. This was a regression
        compared to ``v1.51``

        .. note::
            This has been marked as breaking since one user has reported to rely on this "feature"


    .. change:: Fix ``after_request`` hook not being called on responses returned from handlers
        :type: bugfix
        :pr: 1344
        :issue: 1315

        ``after_request`` hooks were not being called automatically when a ``starlite.response.Response``
        instances was returned from a route handler directly.

        .. seealso::
            :ref:`after_request`


    .. change:: Fix ``SQLAlchemyPlugin`` raises error when using SQLAlchemy UUID
        :type: bugfix
        :pr: 1355

        An error would be raised when using the SQLAlchemy plugin with a
        `sqlalchemy UUID <https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.UUID>`_. This
        was fixed by adding it to the provider map.


    .. change:: Fix ``JSON.parse`` error in ReDoc and Swagger OpenAPI handlers
        :type: bugfix
        :pr: 1363

        The HTML generated by the ReDoc and Swagger OpenAPI handlers would cause
        `JSON.parse <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse>`_
        to throw an error. This was fixed by removing the call to ``JSON.parse``.


    .. change:: Fix CLI prints application info twice
        :type: bugfix
        :pr: 1322

        Fix an error where the CLI would print application info twice on startup


    .. change:: Update ``SimpleEventEmitter`` to use worker pattern
        :type: misc
        :pr: 1346

        ``starlite.events.emitter.SimpleEventEmitter`` was updated to using an async worker, pulling
        emitted events from a queue and subsequently calling listeners. Previously listeners were called immediately,
        making the operation effectively "blocking".


    .. change:: Make ``BaseEventEmitterBackend.emit`` synchronous
        :type: misc
        :breaking:
        :pr: 1376

        ``starlite.events.emitter.BaseEventEmitterBackend``, and subsequently
        ``starlite.events.emitter.SimpleEventEmitter`` and
        ``starlite.app.Starlite.emit`` have been changed to synchronous function, allowing them to easily be
        used within synchronous route handlers.


    .. change:: Move 3rd party integration plugins to ``contrib``
        :type: misc
        :breaking:
        :pr: 1279 1252

        - Move ``plugins.piccolo_orm`` > ``contrib.piccolo_orm``
        - Move ``plugins.tortoise_orm`` > ``contrib.tortoise_orm``


    .. change:: Remove ``picologging`` dependency from the ``standard`` package extra
        :type: misc
        :breaking:
        :pr: 1313

        `picologging <https://github.com/microsoft/picologging>`_ has been removed form the ``standard`` package extra.
        If you have been previously relying on this, you need to change ``pip install starlite[standard]`` to
        ``pip install starlite[standard,picologging]``


    .. change:: Replace ``Starlite()`` ``initial_state`` keyword argument with ``state``
        :type: misc
        :pr: 1350
        :breaking:

        The ``initial_state`` argument to ``starlite.app.Starlite`` has been replaced with a ``state`` keyword
        argument, accepting an optional ``starlite.datastructures.state.State`` instance.

        Existing code using this keyword argument will need to be changed from

        .. code-block:: python

            from starlite import Starlite

            app = Starlite(..., initial_state={"some": "key"})

        to

        .. code-block:: python

                from starlite import Starlite
                from starlite.datastructures.state import State

                app = Starlite(..., state=State({"some": "key"}))


    .. change:: Remove support for 2 argument form of ``before_send``
        :type: misc
        :pr: 1354
        :breaking:

        ``before_send`` hook handlers initially accepted 2 arguments, but support for a 3 argument form was added
        later on, accepting an additional ``scope`` parameter. Support for the 2 argument form has been dropped with
        this release.

        .. seealso::
            :ref:`before_send`


    .. change:: Standardize module exports
        :type: misc
        :pr: 1273
        :breaking:

        A large refactoring standardising the way submodules make their names available.

        The following public modules have changed their location:

        - ``config.openapi`` > ``openapi.config``
        - ``config.logging`` > ``logging.config``
        - ``config.template`` > ``template.config``
        - ``config.static_files`` > ``static_files.config``

        The following modules have been removed from the public namespace:

        - ``asgi``
        - ``kwargs``
        - ``middleware.utils``
        - ``cli.utils``
        - ``contrib.htmx.utils``
        - ``handlers.utils``
        - ``openapi.constants``
        - ``openapi.enums``
        - ``openapi.datastructures``
        - ``openapi.parameters``
        - ``openapi.path_item``
        - ``openapi.request_body``
        - ``openapi.responses``
        - ``openapi.schema``
        - ``openapi.typescript_converter``
        - ``openapi.utils``
        - ``multipart``
        - ``parsers``
        - ``signature``


.. changelog:: 2.0.0alpha1

    .. change:: Validation of controller route handler methods
        :type: feature
        :pr: 1144

        Starlite will now validate that no duplicate handlers (that is, they have the same
        path and same method) exist.

    .. change:: HTMX support
        :type: feature
        :pr: 1086

        Basic support for HTMX requests and responses.

    .. change:: Alternate constructor ``Starlite.from_config``
        :type: feature
        :pr: 1190

        ``starlite.app.Starlite.from_config`` was added to the
        ``starlite.app.Starlite`` class which allows to construct an instance
        from an ``starlite.config.app.AppConfig`` instance.

    .. change:: Web concurrency option for CLI ``run`` command
        :pr: 1218
        :type: feature

        A ``--wc`` / --web-concurrency` option was added to the ``starlite run`` command,
        enabling users to specify the amount of worker processes to use. A corresponding
        environment variable ``WEB_CONCURRENCY`` was added as well

    .. change:: Validation of ``state`` parameter in handler functions
        :type: feature
        :pr: 1264

        Type annotations of the reserved ``state`` parameter in handler functions will
        now be validated such that annotations using an unsupported type will raise a
        ``starlite.exceptions.ImproperlyConfiguredException``.

    .. change:: Generic application state
        :type: feature
        :pr: 1030

        ``starlite.connection.base.ASGIConnection`` and its subclasses are now generic on ``State``
        which allow to to fully type hint a request as ``Request[UserType, AuthType, StateType]``.

    .. change:: Dependency injection of classes
        :type: feature
        :pr: 1143

        Support using classes (not class instances, which were already supported) as dependency providers.
        With this, now every callable is supported as a dependency provider.

    .. change:: Event bus
        :pr: 1105
        :type: feature

        A simple event bus system for Starlite, supporting synchronous and asynchronous listeners and emitters, providing a
        similar interface to handlers. It currently features a simple in-memory, process-local backend

    .. change:: Unified storage interfaces
        :type: feature
        :pr: 1184
        :breaking:

        Storage backends for server-side sessions ``starlite.cache.Cache``` have been unified and replaced
        by the ``starlite.storages``, which implements generic asynchronous key/values stores backed
        by memory, the file system or redis.

        .. important::
            This is a breaking change and you need to change your session / cache configuration accordingly


    .. change:: Relaxed type annotations
        :pr: 1140
        :type: misc

        Type annotations across the library have been relaxed to more generic forms, for example
        ``Iterable[str]`` instead of ``List[str]`` or ``Mapping[str, str]`` instead of ``Dict[str, str]``.

    .. change:: ``type_encoders`` support in ``AbstractSecurityConfig``
        :type: misc
        :pr: 1167

        ``type_encoders`` support has been added to
        ``starlite.security.base.AbstractSecurityConfig``, enabling support for customized
        ``type_encoders`` for example in ``starlite.contrib.jwt.jwt_auth.JWTAuth``.


    .. change::  Renamed handler module names
        :type: misc
        :breaking:
        :pr: 1170

        The modules containing route handlers have been renamed to prevent ambiguity between module and handler names.

        - ``starlite.handlers.asgi`` > ``starlite.handlers.asgi_handlers``
        - ``starlite.handlers.http`` > ``starlite.handlers.http_handlers``
        - ``starlite.handlers.websocket`` > ``starlite.handlers.websocket_handlers``


    .. change:: New plugin protocols
        :type: misc
        :pr: 1176
        :breaking:

        The plugin protocol has been split into three distinct protocols, covering different use cases:

        ``starlite.plugins.InitPluginProtocol``
            Hook into an application's initialization process

        ``starlite.plugins.SerializationPluginProtocol``
            Extend the serialization and deserialization capabilities of an application

        ``starlite.plugins.OpenAPISchemaPluginProtocol``
            Extend OpenAPI schema generation


    .. change::  Unify response headers and cookies
        :type: misc
        :breaking:
        :pr: 1209

        :ref:`response headers <usage/responses:Setting Response Headers>` and
        :ref:`response cookies <usage/responses:Setting Response Cookies>` now have the
        same interface, along with the ``headers`` and ``cookies`` keyword arguments to
        ``starlite.response.Response``. They each allow to pass either a
        `:class:`Mapping[str, str] <typing.Mapping>`, e.g. a dictionary, or a :class:`Sequence <typing.Sequence>` of
        ``starlite.datastructures.response_header.ResponseHeader`` or
        ``starlite.datastructures.cookie.Cookie`` respectively.


    .. change:: Replace Pydantic models with dataclasses
        :type: misc
        :breaking:
        :pr: 1242

        Several Pydantic models used for configuration have been replaced with dataclasses or plain classes. This change
        should be mostly non-breaking, unless you relied on those configuration objects being Pydantic models. The changed
        models are:

        - ``starlite.config.allowed_hosts.AllowedHostsConfig``
        - ``starlite.config.app.AppConfig``
        - ``starlite.config.response_cache.ResponseCacheConfig``
        - ``starlite.config.compression.CompressionConfig``
        - ``starlite.config.cors.CORSConfig``
        - ``starlite.config.csrf.CSRFConfig``
        - ``starlite.logging.config.LoggingConfig``
        - ``starlite.openapi.OpenAPIConfig``
        - ``starlite.static_files.StaticFilesConfig``
        - ``starlite.template.TemplateConfig``
        - ``starlite.contrib.jwt.jwt_token.Token``
        - ``starlite.contrib.jwt.jwt_auth.JWTAuth``
        - ``starlite.contrib.jwt.jwt_auth.JWTCookieAuth``
        - ``starlite.contrib.jwt.jwt_auth.OAuth2Login``
        - ``starlite.contrib.jwt.jwt_auth.OAuth2PasswordBearerAuth``
        - ``starlite.contrib.opentelemetry.OpenTelemetryConfig``
        - ``starlite.middleware.logging.LoggingMiddlewareConfig``
        - ``starlite.middleware.rate_limit.RateLimitConfig``
        - ``starlite.middleware.session.base.BaseBackendConfig``
        - ``starlite.middleware.session.client_side.CookieBackendConfig``
        - ``starlite.middleware.session.server_side.ServerSideSessionConfig``
        - ``starlite.response_containers.ResponseContainer``
        - ``starlite.response_containers.File``
        - ``starlite.response_containers.Redirect``
        - ``starlite.response_containers.Stream``
        - ``starlite.security.base.AbstractSecurityConfig``
        - ``starlite.security.session_auth.SessionAuth``


    .. change:: SQLAlchemy plugin moved to ``contrib``
        :type: misc
        :breaking:
        :pr: 1252

        The ``SQLAlchemyPlugin` has moved to ``starlite.contrib.sqlalchemy_1.plugin`` and will only be compatible
        with the SQLAlchemy 1.4 release line. The newer SQLAlchemy 2.x releases will be supported by the
        ``contrib.sqlalchemy`` module.


    .. change:: Cleanup of the ``starlite`` namespace
        :type: misc
        :breaking:
        :pr: 1135

        The ``starlite`` namespace has been cleared up, removing many names from it, which now have to be imported from
        their respective submodules individually. This was both done to improve developer experience as well as reduce
        the time it takes to ``import starlite``.

    .. change:: Fix resolving of relative paths in ``StaticFilesConfig``
        :type: bugfix
        :pr: 1256

        Using a relative :class:`pathlib.Path` did not resolve correctly and result in a ``NotFoundException``

    .. change:: Fix ``--reload`` flag to ``starlite run`` not working correctly
        :type: bugfix
        :pr: 1191

        Passing the ``--reload`` flag to the ``starlite run`` command did not work correctly in all circumstances due to an
        issue with uvicorn. This was resolved by invoking uvicorn in a subprocess.


    .. change:: Fix optional types generate incorrect OpenAPI schemas
        :type: bugfix
        :pr: 1210

        An optional query parameter was incorrectly represented as

        .. code-block::

            { "oneOf": [
              { "type": null" },
              { "oneOf": [] }
             ]}


    .. change:: Fix ``LoggingMiddleware`` is sending obfuscated session id to client
        :type: bugfix
        :pr: 1228

        ``LoggingMiddleware`` would in some cases send obfuscated data to the client, due to a bug in the obfuscation
        function which obfuscated values in the input dictionary in-place.


    .. change:: Fix missing ``domain`` configuration value for JWT cookie auth
        :type: bugfix
        :pr: 1223

        ``starlite.contrib.jwt.jwt_auth.JWTCookieAuth`` didn't set the ``domain`` configuration value on the response
        cookie.


    .. change:: Fix https://github.com/litestar-org/litestar/issues/1201: Can not serve static file in ``/`` path
        :type: bugfix
        :issue: 1201

        A validation error made it impossible to serve static files from the root path ``/`` .

    .. change:: Fix https://github.com/litestar-org/litestar/issues/1149: Middleware not excluding static path
        :type: bugfix
        :issue: 1149

        A middleware's ``exclude`` parameter would sometimes not be honoured if the path was used to serve static files
        using ``StaticFilesConfig``
