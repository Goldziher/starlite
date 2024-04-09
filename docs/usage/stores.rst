:tocdepth: 4

Stores
======

.. py:currentmodule:: litestar.stores


When developing applications, oftentimes a simply storage mechanism is needed, for example when
:doc:`caching response data</usage/caching>` or storing data for
:ref:`server-side sessions <usage/middleware/builtin-middleware:Server-side sessions>`. In cases like these a
traditional database is often not needed, and a simple key/value store suffices.

Litestar provides several low level key value stores, offering an asynchronous interface to store data in a
thread- and process-safe manner. These stores are centrally managed via a
:class:`registry <litestar.stores.registry.StoreRegistry>`, allowing easy access throughout the whole application and
third party integration (for example plugins).


Built-in stores
---------------

:class:`MemoryStore <litestar.stores.memory.MemoryStore>`
    A simple in-memory store, using a dictionary to hold data. This store offers no persistence and is not thread or multiprocess safe,
    but it is suitable for basic applications such as caching and has generally the lowest overhead. This is the default store used by
    Litestar internally. If you plan to enable :ref:`multiple web workers<cli-run-options>` and you need inter-process communication
    across multiple worker processes, you should use one of the other non-memory stores instead.

:class:`FileStore <litestar.stores.file.FileStore>`
    A store that saves data as files on disk. Persistence is built in, and data is easy to extract and back up.
    It is slower compared to in-memory solutions, and primarily suitable for situations when larger amounts of data
    need to be stored, is particularly long-lived, or persistence has a very high importance. Offers `namespacing`_.

:class:`RedisStore <litestar.stores.redis.RedisStore>`
    A store backend by `redis <https://redis.io/>`_. It offers all the guarantees and features of Redis, making it
    suitable for almost all applications. Offers `namespacing`_.

.. admonition:: Why not memcached?
    :class: info

    Memcached is not a supported backend, and will likely also not be added in the future. The reason for this is simply
    that it's hard to support memcached properly, since it's missing a lot of basic functionality like checking a key's
    expiry time, or something like Redis' `SCAN <https://redis.io/commands/scan/>`_ command, which allows to implement
    pattern-based deletion of keys.


Interacting with a store
------------------------

The most fundamental operations of a store are:

- :meth:`get <.base.Store.get>`: To retrieve a stored value
- :meth:`set <.base.Store.set>`: To set a value in the store
- :meth:`delete <.base.Store.delete>`: To delete a stored value


Getting and setting values
++++++++++++++++++++++++++


.. literalinclude:: /examples/stores/get_set.py
    :language: python


Setting an expiry time
++++++++++++++++++++++

The :meth:`set <.base.Store.set>` method has an optional parameter ``expires_in``, allowing to specify a time after
which a stored value should expire.


.. literalinclude:: /examples/stores/expiry.py
    :language: python


.. note::
    It is up to the individual store to decide how to handle expired values, and implementations may differ. The
    :class:`redis based store <.redis.RedisStore>` for example uses Redis' native expiry mechanism to handle this,
    while the :class:`FileStore <.file.FileStore>` only deletes expired values when they're trying to be accessed,
    or explicitly deleted via the :meth:`delete_expired <.file.FileStore.delete_expired>` method.


It is also possible to extend the expiry time on each access, which is useful for applications such as server side
sessions or LRU caches:

.. literalinclude:: /examples/stores/expiry_renew_on_get.py
    :language: python


Deleting expired values
#######################

When using a :class:`MemoryStore <.memory.MemoryStore>` or :class:`FileStore <.file.FileStore>`, expired data won't be
deleted automatically. Instead, it will only happen when the data is being accessed, or if this process is invoked
explicitly via :meth:`MemoryStore.delete_expired <.memory.MemoryStore.delete_expired>` or
:meth:`FileStore.delete_expired <.file.FileStore.delete_expired>` respectively.

It's a good practice to call ``delete_expired`` periodically, to ensure the size of the stored values does not grow
indefinitely.

In this example, an :ref:`after_response <after_response>` handler is used to delete expired items at most every 30
second:

.. literalinclude:: /examples/stores/delete_expired_after_response.py
    :language: python

When using the :class:`FileStore <.file.FileStore>`, expired items may also be deleted on startup:


.. literalinclude:: /examples/stores/delete_expired_on_startup.py
    :language: python


.. note::
    For the :class:`MemoryStore <.memory.MemoryStore>`, this is not needed as the data is simply stored in a dictionary.
    This means that every time a new instance of this store is created, it will start out empty.


What can be stored
++++++++++++++++++

Stores generally operate on :class:`bytes`; They accept bytes to store, and will return bytes. For convenience, the
:meth:`set <.base.Store.set>` method also allows to pass in strings, which will be UTF-8 encoded before being stored.
This means that :meth:`get <.base.Store.get>` will return bytes even when a string has been passed to
:meth:`set <.base.Store.set>`.

The reason for this limitation is simple: Different backends used to store the data offer vastly different encoding,
storage, and (de)serialization capacities. Since stores are designed to be interchangeable, this means settling for a
common denominator, a type that all backends will support. :class:`bytes` meet these requirements and make it possible
to store a very wide variety of data.

.. admonition:: Technical details

    :class:`MemoryStore <.memory.MemoryStore>` differs from this, because it does not do any encoding before storing
    the value. This means that it's technically possible to store arbitrary objects in this store, and get the same
    object back. However, this is not reflected in the store's typing, as the underlying :class:`Store <.base.Store>`
    interface does not guarantee this behaviour, and it is not guaranteed that
    :class:`MemoryStore <.memory.MemoryStore>` will always behave in this case.


Namespacing
+++++++++++

When stores are being used for more than one purpose, some extra bookkeeping is required to safely perform bulk
operations such as :class:`delete_all <.base.Store.delete_all>`. If for example a
:class:`RedisStore <.redis.RedisStore>` was used, simply issuing a `FLUSHALL <https://redis.io/commands/flushall/>`_
command might have unforeseen consequences.

To help with this, some stores offer namespacing capabilities, allowing to build a simple hierarchy of stores.
These come with the additional :meth:`with_namespace <.base.NamespacedStore.with_namespace>` method, which returns a
new :class:`NamespacedStore <.base.NamespacedStore>` instance. Once a namespaced store is created, operations on it
will only affect itself and its child namespaces.

When using the :class:`RedisStore <.redis.RedisStore>`, this allows to reuse the same underlying
:class:`Redis <redis.asyncio.Redis>` instance and connection, while ensuring isolation.

.. note::
    :class:`RedisStore <.redis.RedisStore>` uses the ``LITESTAR`` namespace by default; all keys created by this store,
    will use the ``LITESTAR`` prefix when storing data in redis.
    :meth:`RedisStore.delete_all <.redis.RedisStore.delete_all>` is implemented in such a way that it will only delete
    keys matching the current namespace, making it safe and side-effect free.

    This can be turned off by explicitly passing ``namespace=None`` to the store when creating a new instance.


.. literalinclude:: /examples/stores/namespacing.py
    :language: python

Even though all three stores defined here use the same Redis instance, calling ``delete_all`` on the ``cache_store``
will not affect data within the ``session_store``.

Defining stores hierarchically like this still allows to easily clear everything, by simply calling
:meth:`delete_all <.base.Store.delete_all>` on the root store.


Managing stores with the registry
---------------------------------

The :class:`StoreRegistry <litestar.stores.registry.StoreRegistry>` is a central place through which stores can be
configured and managed, and can help to easily access stores set up and used by other parts of the application, Litestar
internals or third party integrations. It is available throughout the whole application context via the
:class:`Litestar.stores <litestar.app.Litestar>` attribute.

It operates on a few basic principles:

- An initial mapping of stores can be provided to the registry
- Registered stores can be requested with :meth:`get <.registry.StoreRegistry.get>`
- If a store has been requested that has not been registered yet, a store of that name will be created and registered
  using the `the default factory`_


.. literalinclude:: /examples/stores/registry.py
    :language: python


This pattern offers isolation of stores, and an easy way to configure stores used by middlewares and other Litestar
features or third party integrations.

In the following example, the store set up by the
:class:`RateLimitMiddleware <litestar.middleware.rate_limit.RateLimitMiddleware>` is accessed via the registry:

.. literalinclude:: /examples/stores/registry_access_integration.py
    :language: python


This works because :class:`RateLimitMiddleware <litestar.middleware.rate_limit.RateLimitMiddleware>` will request
its store internally via ``app.stores.get`` as well.


The default factory
+++++++++++++++++++

The pattern above is made possible by using the registry's default factory; A callable that gets invoked
every time a store is requested that hasn't been registered yet. It's similar to the ``default`` argument to
:meth:`dict.get`.

By default, the default factory is a function that returns a new
:class:`MemoryStore <litestar.stores.memory.MemoryStore>` instance. This behaviour can be changed by supplying a
custom ``default_factory`` method to the registry.

To make use of this, a registry instance can be passed directly to the application:

.. literalinclude:: /examples/stores/registry_default_factory.py
    :language: python

The registry will now return the same :class:`MemoryStore <litestar.stores.memory.MemoryStore>` every time an undefined
store is being requested.


Using the registry to configure integrations
++++++++++++++++++++++++++++++++++++++++++++

This mechanism also allows to control the stores used by various integrations, such as middlewares:

.. literalinclude:: /examples/stores/registry_configure_integrations.py
    :language: python


In this example, the registry is being set up with stores using the ``sessions`` and ``response_cache`` keys. These are
not magic constants, but instead configuration values that can be changed. Those names just happen to be their default
values. Adjusting those default values allows to easily reuse stores, without the need for a more complex setup:

.. literalinclude:: /examples/stores/configure_integrations_set_names.py
    :language: python

Now the rate limit middleware and response caching will use the ``redis`` store, while sessions will be store in the
``file`` store.


Setting up the default factory with namespacing
+++++++++++++++++++++++++++++++++++++++++++++++

The default factory can be used in conjunction with `namespacing`_ to create isolated, hierarchically organized stores,
with minimal boilerplate:

.. literalinclude:: /examples/stores/registry_default_factory_namespacing.py
    :language: python


Without any extra configuration, every call to ``app.stores.get`` with a unique name will return a namespace for this
name only, while re-using the underlying Redis instance.


Store lifetime
++++++++++++++

Stores may not be automatically closed when the application is shut down.
This is the case in particular for the RedisStore if you are not using the class method :meth:`RedisStore.with_client <.redis.RedisStore.with_client>` and passing in your own Redis instance.
In this case you're responsible to close the Redis instance yourself.
