Handling Secrets
================

Overview
--------

Two data structures are available to assist in handling secrets in web services:
:class:`SecretString <datastructures.SecretString>` and :class:`SecretBytes <datastructures.SecretBytes>`. These are
containers for holding sensitive data within your application.

Secret Parameters
-----------------

The following example demonstrates how to use :class:`~datastructures.SecretString` to accept a secret value as a parameter in a GET request:

.. literalinclude:: /examples/datastructures/secrets/secret_header.py
    :caption: Example of using SecretString for a Header Parameter

.. note::

    When storing and comparing secrets, use secure practices to prevent unauthorized access. For example, use
    environment variables, secret management services, or encrypted databases to store secrets securely. When comparing
    secrets, use :func:`secrets.compare_digest` or similar to mitigate the risk of timing attacks.

.. note::

    The :func:`headers <connection.ASGIConnection.headers>` attribute of the :class:`~connection.ASGIConnection`
    object stores the headers exactly as they are parsed from the ASGI message. Care should be taken to ensure that
    these headers are not logged or otherwise exposed in a way that could compromise the security of the application.

Secret Body
-----------

This example demonstrates use of a data structure with a :class:`~datastructures.SecretString` field to accept a secret
within the HTTP body of a request:

.. literalinclude:: /examples/datastructures/secrets/secret_body.py
    :caption: Example of using SecretString for a Request Body

Security Considerations
-----------------------

While :class:`SecretString` and :class:`SecretBytes` can help in securely transferring secret data through the framework,
it's vital to adopt secure practices for storing and comparing secrets within your application. Here are a few
guidelines:

- Store secrets securely, using environment variables, secret management services, or encrypted databases.
- Always use constant time comparison functions such as :func:`secrets.compare_digest` for comparing secret values to
  mitigate the risk of timing attacks.
- Implement access controls and logging to monitor and restrict who can access sensitive information.
