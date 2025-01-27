Debugging
=========

Using the Python debugger
--------------------------

You can configure Litestar to drop into the :doc:`Python Debugger <python:library/pdb>`
when an exception occurs. This can be configured in different ways:

Configuring ``Litestar`` with the ``pdb_on_exception`` option
    .. code-block:: python

        app = Litestar(pdb_on_exception=True)


Running your app with the CLI and using the ``--pdb`` flag
    .. code-block:: shell

        litestar run --pdb

Using the ``LITESTAR_PDB`` environment variable
    ``LITESTAR_PDB=1``


Debugging with an IDE
---------------------

You can easily attach your IDEs debugger to your application, whether you're running it
via the CLI or a webserver like `uvicorn <https://www.uvicorn.org/>`_.

Intellij / PyCharm
++++++++++++++++++

Using the CLI
*************

1. Create a new debug configuration via ``Run`` > ``Edit Configurations``
2. Select ``Module name`` option and set it to ``litestar``
3. Add the ``run`` parameter and optionally additional parameters you want to pass
   to the CLI

   .. image:: /images/debugging/pycharm-config-cli.png

4. Run your application in the debugger via ``Run`` > ``Debug Litestar``

   .. image:: /images/debugging/pycharm-debug.png
        :align: center


.. important::
    Breakpoints inside route handlers might not work correctly when used in conjunction
    with the ``--reload`` and ``--web-concurrency`` parameters. If you want to use the
    CLI while making use of these options, you can attach the debugger manually to the
    running uvicorn process via ``Run`` > ``Attach to process``.


Using uvicorn
*************

1. Create a new debug configuration via ``Run`` > ``Edit Configurations``
2. Select ``Module name`` option and set it to ``uvicorn``
3. Add the ``app:app`` parameter (or the equivalent path to your application object)

   .. image:: /images/debugging/pycharm-config-uvicorn.png

4. Run your application in the debugger via ``Run`` > ``Debug Litestar``

   .. image:: /images/debugging/pycharm-debug.png
        :align: center


VS Code
+++++++


Using the CLI
*************


1. Add a new debugging configuration via ``Run`` > ``Add configuration``
    .. image:: /images/debugging/vs-code-add-config.png
        :align: center
2. From the ``Select a debug configuration`` dialog, select ``Module``
    .. image:: /images/debugging/vs-code-select-config.png
3. Enter ``litestar`` as the module name
    .. image:: /images/debugging/vs-code-config-litestar.png
4. In the opened JSON file, alter the configuration as follows:
    .. code-block:: json

        {
            "name": "Python: Litestar app",
            "type": "python",
            "request": "launch",
            "module": "litestar",
            "justMyCode": true,
            "args": ["run"]
        }

5. Run your application via the debugger via ``Run`` > ``Start debugging``
    .. image:: /images/debugging/vs-code-debug.png
        :align: center


Using uvicorn
**************

1. Add a new debugging configuration via ``Run`` > ``Add configuration``
    .. image:: /images/debugging/vs-code-add-config.png
        :align: center
2. From the ``Select a debug configuration`` dialog, select ``Module``
    .. image:: /images/debugging/vs-code-select-config.png
3. Enter ``uvicorn`` as the module name
    .. image:: /images/debugging/vs-code-config-litestar.png
4. In the opened JSON file, alter the configuration as follows:
    .. code-block:: json

        {
            "name": "Python: Litestar app",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "justMyCode": true,
            "args": ["app:app"]
        }

5. Run your application via the debugger via ``Run`` > ``Start debugging``
    .. image:: /images/debugging/vs-code-debug.png
        :align: center


Customizing the debugger
-------------------------

You can configure Litestar with the debug_module option to enable interactive debugging. Currently, it supports the following debugging tools:
`ipdb <https://github.com/gotcha/ipdb>`_, `PuDB <https://documen.tician.de/pudb/>`_ and `pdbr <https://github.com/cansarigol/pdbr>`_. Also supports `pdb++ <https://github.com/pdbpp/pdbpp>`_.
The default value is `pdb <https://docs.python.org/3/library/pdb.html>`_.

    .. code-block:: python

        import ipdb


        app = Litestar(pdb_on_exception=True, debugger_module=ipdb)
