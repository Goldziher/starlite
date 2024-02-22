Static files
============

To serve static files (i.e. serve arbitrary files from a given directory), the
:func:`~litestar.static_files.create_static_files_router` can be used to create a
:class:`Router <litestar.router.Router>` to handle this task.

.. literalinclude:: /examples/static_files/full_example.py
    :language: python

In this example, files from the directory ``assets`` will be served on the path
``/static``. A file ``assets/hello.txt`` would now be available on ``/static/hello.txt``

.. attention::
    Directories are interpreted as relative to the working directory from which the
    application is started


Sending files as attachments
----------------------------

By default, files are sent "inline", meaning they will have a
``Content-Disposition: inline`` header. Setting ``send_as_attachment=True`` flag will
send them with a ``Content-Disposition: attachment`` instead:

.. literalinclude:: /examples/static_files/send_as_attachment.py
    :language: python


HTML mode
---------

"HTML mode" can be enabled by setting ``html_mode=True``. This will:

- Serve and ``/index.html`` when the path ``/`` is requested
- Attempt to serve ``/404.html`` when a requested file is not found


.. literalinclude:: /examples/static_files/html_mode.py
    :language: python


Passing options to the generated router
---------------------------------------

Options available on :class:`~litestar.router.Router` can be passed to directly
:func:`~litestar.static_files.create_static_files_router`:

.. literalinclude:: /examples/static_files/passing_options.py
    :language: python


Using a custom router class
---------------------------

The router class used can be customized with the ``router_class`` parameter:

.. literalinclude:: /examples/static_files/custom_router.py
    :language: python



Retrieving paths to static files
--------------------------------

:meth:`~litestar.app.Litestar.route_reverse` and
:meth:`~litestar.connection.ASGIConnection.url_for` can be used to retrieve the path
under which a specific file will be available:

.. literalinclude:: /examples/static_files/route_reverse.py
    :language: python

.. tip::

    The ``name`` parameter has to match the ``name`` parameter passed to
    :func:`create_static_files_router`, which defaults to ``static``.


(Remote) file systems
---------------------

To customize how Litestar interacts with the file system, a class implementing the
:class:`~litestar.types.FileSystemProtocol` can be passed to ``file_system``. An example
of this are the file systems provided by
`fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_, which includes support
for FTP, SFTP, Hadoop, SMB, GitHub and
`many more <https://filesystem-spec.readthedocs.io/en/latest/api.html#implementations>`_,
with support for popular cloud providers available via 3rd party implementations such as

- S3 via `S3FS <https://s3fs.readthedocs.io/en/latest/>`_
- Google Cloud Storage via `GCFS <https://gcsfs.readthedocs.io/en/latest/>`_
- Azure Blob Storage via `adlfs <https://github.com/fsspec/adlfs>`_


.. literalinclude:: /examples/static_files/file_system.py
    :language: python


Upgrading from legacy StaticFilesConfig
---------------------------------------

.. important:: Info
    :class:`StaticFilesConfig` is deprecated and will be removed in Litestar 3.0


Existing code can be upgraded to :func:`create_static_files_router` by replacing
:class:`StaticFilesConfig` instances with this function call and passing the result to
``route_handlers`` instead of ``static_files_config``:


.. literalinclude:: /examples/static_files/upgrade_from_static_1.py
    :language: python


.. literalinclude:: /examples/static_files/upgrade_from_static_2.py
    :language: python
