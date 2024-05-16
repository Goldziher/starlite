OpenTelemetry
=============

Litestar includes optional OpenTelemetry instrumentation that is exported from ``litestar.contrib.opentelemetry``. To use
this package, you should first install the required dependencies:

.. code-block:: bash
    :caption: as separate package

    pip install opentelemetry-instrumentation-asgi


.. code-block:: bash
    :caption: as a Litestar extra

    pip install litestar[opentelemetry]

Once these requirements are satisfied, you can instrument your Litestar application by creating an instance
of :class:`OpenTelemetryConfig <litestar.contrib.opentelemetry.OpenTelemetryConfig>` and passing the middleware it creates to
the Litestar constructor:

.. literalinclude:: /examples/metrics/opentelemetry.py
    :language: python


The above example will work out of the box if you configure a global ``tracer_provider`` and/or ``metric_provider`` and an
exporter to use these (see the
`OpenTelemetry Exporter docs <https://opentelemetry.io/docs/instrumentation/python/exporters/>`_ for further details).

You can also pass con figuration to the ``OpenTelemetryConfig`` telling it which providers to use. Consult
:class:`reference docs <litestar.contrib.opentelemetry.OpenTelemetryConfig>` regarding the configuration options you can use.
