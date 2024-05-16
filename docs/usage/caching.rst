Caching
=======

Caching responses
------------------

Sometimes it's desirable to cache some responses, especially if these involve expensive calculations, or when polling is
expected. Litestar comes with a simple mechanism for caching:

.. literalinclude:: /examples/caching/caching_response.py
    :caption: Caching response
    :language: python


By setting :paramref:`~litestar.handlers.HTTPRouteHandler.cache` to ``True``, the response from the handler
will be cached. If no ``cache_key_builder`` is set in the route handler, caching for the route handler will be
enabled for the :attr:`~.config.response_cache.ResponseCacheConfig.default_expiration`.

.. note:: If the default :paramref:`~litestar.config.response_cache.ResponseCacheConfig.default_expiration` is set to
    ``None``, setting up the route handler with :paramref:`~litestar.handlers.HTTPRouteHandler.cache` set to ``True``
    will keep the response in cache indefinitely.

Alternatively you can specify the number of seconds to cache the responses from the given handler like so:

.. literalinclude:: /examples/caching/caching_duration.py
    :caption: Caching the response for 120 seconds by setting the :paramref:`~litestar.handlers.HTTPRouteHandler.cache`
      parameter to the number of seconds to cache the response.
    :emphasize-lines: 4
    :language: python


If you want the response to be cached indefinitely, you can pass the :class:`~.config.response_cache.CACHE_FOREVER`
sentinel instead:

.. literalinclude:: /examples/caching/caching_forever.py
    :caption: Caching the response indefinitely by setting the :paramref:`~litestar.handlers.HTTPRouteHandler.cache`
      parameter to :class:`~litestar.config.response_cache.CACHE_FOREVER`.
    :language: python

Configuration
-------------

You can configure caching behaviour on the application level by passing an instance of
:class:`~.config.response_cache.ResponseCacheConfig` to the :class:`Litestar instance <.app.Litestar>`.

Changing where data is stored
+++++++++++++++++++++++++++++

By default, caching will use the :class:`~.stores.memory.MemoryStore`, but it can be configured with
any :class:`~.stores.base.Store`, for example :class:`~.stores.redis.RedisStore`:

.. literalinclude:: /examples/caching/caching_storage_redis.py
    :caption: Using Redis as the cache store.
    :language: python


Specifying a cache key builder
++++++++++++++++++++++++++++++

Litestar uses the request's path + sorted query parameters as the cache key. This can be adjusted by providing a
"key builder" function, either at application or route handler level.

.. literalinclude:: /examples/caching/caching_key_builder.py
    :caption: Using a custom cache key builder.
    :language: python


.. literalinclude:: /examples/caching/caching_key_builder_specific_route.py
    :caption: Using a custom cache key builder for a specific route handler.
    :language: python
