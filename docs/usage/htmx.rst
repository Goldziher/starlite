HTMX
====

Litestar HTMX integration.

HTMXRequest
------------

A special :class:`~litestar.connection.Request` class, providing interaction with the
HTMX client.

.. literalinclude:: /examples/htmx/htmx_request.py
    :language: python


See :class:`HTMXDetails <litestar.contrib.htmx.request.HTMXDetails>` for a full list of
available properties.


HTMX Response Classes
---------------------


HTMXTemplate Response Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common  use-case for `htmx` to render an html page or html snippet. Litestar makes this easy by providing
an :class:`HTMXTemplate <litestar.contrib.htmx.response.HTMXTemplate>` response:

.. literalinclude:: /examples/htmx/htmx_response.py
    :language: python


.. note::
    - Return type is litestar's ``Template`` and not ``HTMXTemplate``.
    - ``trigger_event``, ``params``, and ``after parameters`` are linked to one another.
    - If you are triggering an event then ``after`` is required and it must be one of ``receive``, ``settle``, or ``swap``.

HTMX provides two types of responses - one that doesn't allow changes to the DOM and one that does.
Litestar supports both of these:

1 - Responses that don't make any changes to DOM.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :class:`HXStopPolling <litestar.contrib.htmx.response.HXStopPolling>` to stop polling for a response.

.. literalinclude:: /examples/htmx/htmx_response_no_dom_change.py
    :language: python


Use :class:`ClientRedirect  <litestar.contrib.htmx.response.ClientRedirect>` to redirect with a page reload.

.. literalinclude:: /examples/htmx/htmx_client_redirect.py
    :language: python

Use :class:`ClientRefresh  <litestar.contrib.htmx.response.ClientRefresh>` to force a full page refresh.

.. literalinclude:: /examples/htmx/htmx_client_refresh.py
    :language: python


2 - Responses that may change DOM.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :class:`HXLocation <litestar.contrib.htmx.response.HXLocation>` to redirect to a new location without page reload.

- Note: this class provides the ability to change ``target``, ``swapping`` method, the sent ``values``, and the ``headers``.)

.. literalinclude:: /examples/htmx/htmx_response_change_dom.py
    :language: python


Use :class:`PushUrl <litestar.contrib.htmx.response.PushUrl>` to carry a response and push a url to the browser, optionally updating the `history` stack.

- Note: If the value for ``push_url`` is set to ``False`` it will prevent updating browser history.

.. literalinclude:: /examples/htmx/htmx_push_url.py
    :language: python


Use :class:`ReplaceUrl <litestar.contrib.htmx.response.ReplaceUrl>` to carry a response and replace the url in the browser's ``location`` bar.
- Note: If the value to ``replace_url`` is set to ``False`` it will prevent it updating the browser location bar.

.. literalinclude:: /examples/htmx/htmx_replace_url.py
    :language: python


Use :class:`Reswap <litestar.contrib.htmx.response.Reswap>` to carry a response perhaps a swap

.. literalinclude:: /examples/htmx/htmx_reswap.py
    :language: python


Use :class:`Retarget <litestar.contrib.htmx.response.Retarget>` to carry a response and change the target element.

.. literalinclude:: /examples/htmx/htmx_retarget.py
    :language: python


Use :class:`TriggerEvent <litestar.contrib.htmx.response.TriggerEvent>` to carry a response and trigger an event.

.. literalinclude:: /examples/htmx/htmx_trigger_event.py
    :language: python
