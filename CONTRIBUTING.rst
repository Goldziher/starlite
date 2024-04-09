Contribution Guide
==================

.. _pipx: https://pypa.github.io/pipx/
.. |pipx| replace:: `pipx <https://pypa.github.io/pipx/>`__

.. _homebrew: https://brew.sh/
.. |homebrew| replace:: `Homebrew <https://brew.sh/>`__


Getting Started
---------------

Supported Python Versions
+++++++++++++++++++++++++

The lowest currently supported version is Python 3.8.
At a minimum you will need Python 3.8 for code changes and 3.12 if you plan on doing documentation building / changes.

You can use various tools to manage multiple Python versions on your system including:

* `pyenv <https://github.com/pyenv/pyenv>`_ and `pyenv-win for Windows <https://github.com/pyenv-win/pyenv-win>`_
* `rtx / mise <https://mise.jdx.dev/>`_
* `asdf <https://asdf-vm.com/>`_
* `Building each version manually from source <https://www.build-python-from-source.com/>`_
* Utilizing `GitHub Codespaces <https://codespaces.new/litestar-org/litestar?quickstart=1>`_

We use the lowest supported version in our type-checking CI,
this ensures that the changes you made are backward compatible.

Setting up the environment
++++++++++++++++++++++++++

.. tip:: We maintain a Makefile with several commands to help with common tasks.
   You can run ``make help`` to see a list of available commands.

If you are utilizing `GitHub Codespaces <https://codespaces.new/litestar-org/litestar?quickstart=1>`_,
the environment will bootstrap itself automatically. The steps below are for local development.

#. Install `PDM <https://pdm.fming.dev/latest/>`_:

   .. tab-set::

        .. tab-item:: Makefile
            :sync: makefile

            .. code-block:: bash
                :caption: Using our Make target to install PDM

                make install-pdm

        .. tab-item:: pipx
            :sync: pipx

            .. code-block:: bash
                :caption: Using |pipx|

                pipx install pdm

        .. tab-item:: Homebrew
            :sync: homebrew

            .. code-block:: bash
                :caption: Using |homebrew|

                brew install pdm

#. Run ``make install`` to create a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_
   and install the required development dependencies or run the PDM installation command manually:

   .. code-block:: shell
        :caption: Installing the documentation dependencies

        pdm install

#. If you're working on the documentation and need to build it locally, install the extra dependencies with
   ``make docs-install`` or:

   .. code-block:: shell
        :caption: Installing the documentation dependencies

        pdm install -G:docs

#. Install `pre-commit <https://pre-commit.com/>`_:

   .. tab-set::

        .. tab-item:: pip
            :sync: pip

            .. code-block:: bash
                :caption: Using pip

                python3 -m pip install pre-commit

        .. tab-item:: pipx
            :sync: pipx

            .. code-block:: bash
                :caption: Using |pipx|

                pipx install pre-commit

        .. tab-item:: Homebrew
            :sync: homebrew

            .. code-block:: bash
                :caption: Using |homebrew|

                brew install pre-commit

#. Install our pre-commit hooks. by running ``make install`` or:

   .. code-block:: shell
        :caption: Installing pre-commit hooks

        pre-commit install --install-hooks

.. tip:: Many modern IDEs like PyCharm or VS Code will enable the PDM-managed virtualenv that is created in step 2
   for you automatically.
   If your IDE / editor does not offer this functionality, then you will need to manually activate the virtualenv
   yourself. Otherwise you may encounter errors or unexpected behaviour when trying to run the commands referenced
   within this document.

   To activate the virtualenv manually, please consult PDM's documentation on
   `working with virtual environments <https://pdm-project.org/latest/usage/venv/#working-with-virtual-environments>`_.
   A simpler alternative is using the PDM plugin `pdm-shell <https://github.com/abersheeran/pdm-shell>`_.

   The rest of this document will assume this environment is active wherever commands are referenced.

Code contributions
------------------

Workflow
++++++++

#. `Fork <https://github.com/litestar-org/litestar/fork>`_ the `Litestar repository <https://github.com/litestar-org/litestar>`_
#. Clone your fork locally with git
#. `Set up the environment <#setting-up-the-environment>`_
#. Make your changes
#. (Optional) Run ``pre-commit run --all-files`` to run linters and formatters. This step is optional and will be executed
   automatically by git before you make a commit, but you may want to run it manually in order to apply fixes
#. Commit your changes to git. We follow `conventional commits <https://www.conventionalcommits.org/>`_
   which are enforced using a ``pre-commit`` hook.
#. Push the changes to your fork
#. Open a `pull request <https://docs.github.com/en/pull-requests>`_. Give the pull request a descriptive title
   indicating what it changes. The style of the PR title should also follow
   `conventional commits <https://www.conventionalcommits.org/>`_, and this is enforced using a GitHub action.
#. Add yourself as a contributor using the `all-contributors bot <https://allcontributors.org/docs/en/bot/usage>`_

Guidelines for writing code
----------------------------

- Code should be `Pythonic and zen <https://peps.python.org/pep-0020/>`_
- All code should be fully `typed <https://peps.python.org/pep-0484/>`_. This is enforced via
  `mypy <https://mypy.readthedocs.io/en/stable/>`_ and `Pyright <https://github.com/microsoft/pyright/>`_

  * When requiring complex types, use a `type alias <https://docs.python.org/3/library/typing.html#type-aliases>`_.
    Check :doc:`reference/types` if a type alias for your use case already exists
  * If something cannot be typed correctly due to a limitation of the type checkers, you may use :func:`typing.cast`
    to rectify the situation. However, you should only use this as a last resort if you've exhausted all other options
    of `type narrowing <https://mypy.readthedocs.io/en/stable/type_narrowing.html>`_, such as :func:`isinstance` checks
    and `type guards <https://docs.python.org/3/library/typing.html#typing.TypeGuard>`_.
  * You may use a properly scoped ``type: ignore`` if you ensured that a line is correct, but mypy / pyright has
    issues with it.

    Properly scoped meaning do not use blank ``type: ignore``, instead supply the specific error code, e.g.,
    ``type: ignore[attr-defined]``

- If you are adding or modifying existing code, ensure that it's fully tested. 100% test coverage is mandatory, and will
  be checked on the PR using `SonarCloud <https://www.sonarsource.com/products/sonarcloud/>`_ and
  `Codecov <https://codecov.io/>`_
- All functions, methods, classes, and attributes should be documented with a docstring. We use the
  `Google docstring style <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_. If you come
  across a function or method that doesn't conform to this standard, please update it as you go
- When adding a new public interface, it has to be  included in the reference documentation located in
  ``docs/reference``. If applicable, add or modify examples in the docs related to the new functionality implemented,
  following the guidelines established in `Adding examples`_.

Writing and running tests
+++++++++++++++++++++++++

Tests are contained within the ``tests`` directory, and follow the same directory structure as the ``litestar`` module.
If you are adding a test case, it should be located within the correct submodule of ``tests``. E.g., tests for
``litestar/utils/sync.py`` reside in ``tests/utils/test_sync.py``.

The ``Makefile`` includes several commands for running tests:

- ``make test`` to run tests located in ``tests``
- ``make test-examples`` to run tests located in ``docs/examples/tests``
- ``make test-all`` to run all tests
- ``make coverage`` to run tests with coverage and generate an html report

The tests make use of `pytest-xdist <https://pytest-xdist.readthedocs.io>`_ to speed up
test runs. These are enabled by default when running ``make test``, ``make test-all``
or ``make coverage``. Due to the nature of pytest-xdist, attaching a debugger isn't as
straightforward. For debugging, it's recommended to run the tests individually with
``pytest <test name>`` or via an IDE, which will skip ``pytest-xdist``.

Running type checkers
+++++++++++++++++++++

We use `mypy <https://mypy.readthedocs.io/en/stable/>`_ and `pyright <https://github.com/microsoft/pyright/>`_ to
enforce type safety. You can run them with:

- ``make mypy``
- ``make pyright``
- ``make type-check`` to run both
- ``make lint`` to run pre-commit hooks and type checkers.

Our type checkers are run on Python 3.8 in CI, so you should make sure to run them on the same version locally as well.

Project documentation
---------------------

The documentation is located in the ``/docs`` directory and is written  in
`reStructuredText <https://docutils.sourceforge.io/rst.html>`_ with the `Sphinx <https://www.sphinx-doc.org/en/master/>`_.
library. If you're unfamiliar with any of those,
`reStructuredText primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ and
`Sphinx quickstart <https://www.sphinx-doc.org/en/master/usage/quickstart.html>`_ are recommended reads.

Docs theme and appearance
+++++++++++++++++++++++++

We welcome contributions that enhance / improve the appearance and usability of the docs. We use the excellent
`PyData Sphinx Theme <https://pydata-sphinx-theme.readthedocs.io/>`_ theme, which comes with a lot of options out of the box.
If you wish to contribute to the docs style / setup, or static site generation, you should consult the theme docs
as a first step.

Running the docs locally
++++++++++++++++++++++++

To run or build the docs locally, you need to first install the required dependencies:

.. code-block:: shell
    :caption: Installing the documentation dependencies

    pdm install -G:docs

Then you can serve the documentation with our helpful Makefile targets:

.. code-block:: shell
    :caption: Serving the documentation locally

    make docs-serve

Writing and editing docs
++++++++++++++++++++++++

We welcome contributions that enhance / improve the content of the docs. Feel free to add examples, clarify text,
restructure the docs, etc., but make sure to follow these guidelines:

- Write text in idiomatic English, using simple language
- Do not use contractions for ease of reading for non-native English speakers
- Opt for `Oxford commas <https://en.wikipedia.org/wiki/Serial_comma>`_ when listing a series of terms
- Keep examples simple and self contained (see `Adding examples`_). This is to ensure they are tested
  alongside the rest of the test suite and properly type checked and linted.
- Provide links where applicable.
- Use `intersphinx <https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html>`_ wherever possible when
  referencing external libraries
- Provide diagrams using `Mermaid <https://mermaid.js.org/>`_ where applicable and possible

Adding examples
~~~~~~~~~~~~~~~

The examples from the docs are located in their own modules inside the ``/docs/examples`` folder. This makes it easier
to test them alongside the rest of the test suite, ensuring they do not become stale as Litestar evolves.

Please follow the next guidelines when adding a new example:

- Add the example in the corresponding module directory in ``/docs/examples`` or create a new one if necessary
- Create a suite for the module in ``/docs/examples/tests`` that tests the aspects of the example that it demonstrates
- Reference the example in the rst file with an external reference code block, e.g.

.. code-block:: rst
   :caption: An example of how to use literal includes of external files

   .. literalinclude:: /examples/test_thing.py
      :caption: All includes should have a descriptive caption

Automatically execute examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our docs include a Sphinx extension that can automatically run requests against example apps
and include their result in the documentation page when its being built. This only requires 2 steps:

1. Create an example file with an ``app`` object in it, which is an instance of ``Litestar``
2. Add a comment in the form of ``# run: /hello`` to the example file

When building the docs (or serving them locally), a process serving the ``app`` instance
will be launched, and the requests specified in the comments will be run against it. The
comments will be stripped from the result, and the output of the ``curl`` invocation inserted
after the example code-block.

The ``# run:`` syntax is nothing special; everything after the colon will be passed to
the ``curl`` command that's being invoked. The URL is built automatically, so the
specified path can just be a path relative to the app.

In practice, this looks like the following:

.. code-block:: python
   :caption: An example of how to use the automatic example runner
   :no-upgrade:

   from typing import Dict

   from litestar import Litestar, get


   @get("/")
   def hello_world() -> Dict[str, str]:
       """Handler function that returns a greeting dictionary."""
       return {"hello": "world"}


   app = Litestar(route_handlers=[hello_world])

   # run: /

This is equivalent to:

.. code-block:: python
   :caption: An example of how to use the automatic example runner

      from typing import Dict

      from litestar import Litestar, get


      @get("/")
      def hello_world() -> Dict[str, str]:
          """Handler function that returns a greeting dictionary."""
          return {"hello": "world"}


      app = Litestar(route_handlers=[hello_world])


.. admonition:: Run it

      .. code-block:: bash

         > curl http://127.0.0.1:8000/
         {"hello": "world"}


Creating a New Release
----------------------

#. Checkout the ``main`` branch:

   .. code-block:: shell
        :caption: Checking out the main branch of the ``litestar`` repository

        git checkout main

#. Run the release preparation script:

   .. code-block:: shell
        :caption: Preparing  a new release

        python tools/prepare_release.py <new version number> --update-version --create-draft-release

   Replace ``<new version number>`` with the desired version number following the
   `versioning scheme <https://litestar.dev/about/litestar-releases#version-numbering>`_.

   This script will:

   - Update the version in ``pyproject.toml``
   - Generate a changelog entry in :doc:`/release-notes/changelog`
   - Create a draft release on GitHub

#. Review the generated changelog entry in :doc:`/release-notes/changelog` to ensure it looks correct.

#. Commit the changes to ``main``:

   .. code-block:: shell
        :caption: Committing the changes to the main branch

        git commit -am "chore(release): prepare release vX.Y.Z"

   Replace ``vX.Y.Z`` with the actual version number.

#. Create a new branch for the release:

   .. code-block:: shell
        :caption: Creating a new branch for the release

        git checkout -b vX.Y.Z

#. Push the changes to a ``vX.Y.Z`` branch:

   .. code-block:: shell
        :caption: Pushing the changes to the ``vX.Y.Z`` branch

        git push origin vX.Y.Z

#. Open a pull request from the ``vX.Y.Z`` branch to ``main``.
#. Once the pull request is approved, go to the draft release on GitHub
   (the release preparation script will provide a link).
#. Review the release notes in the draft release to ensure they look correct.
#. If everything looks good, click "Publish release" to make the release official.
#. Go to the `Release Action <https://github.com/litestar-org/litestar/actions/workflows/publish.yml>`_ and approve
   the release workflow if necessary.
#. Check that the release workflow runs successfully.

.. note:: The version number should follow `semantic versioning <https://semver.org/>`_ and
   `PEP 440 <https://peps.python.org/pep-0440/>`_.
