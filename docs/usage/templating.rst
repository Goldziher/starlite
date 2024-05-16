Templating
==========

Litestar has built-in support for `Jinja2 <https://jinja.palletsprojects.com/en/3.0.x/>`_
, `Mako <https://www.makotemplates.org/>`_ and `Minijinja <https://github.com/mitsuhiko/minijinja/tree/main/minijinja-py>`_
template engines, as well as abstractions to make use of any template engine you wish.

Template engines
----------------

To stay lightweight, a Litestar installation does not include the *Jinja*, *Mako* or *Minijinja*
libraries themselves. Before you can start using them, you have to install it via the
respective extra:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. code-block:: shell

            pip install litestar[jinja]

    .. tab-item:: Mako
        :sync: mako

        .. code-block:: shell

            pip install litestar[mako]

    .. tab-item:: MiniJinja
        :sync: minijinja

        .. code-block:: shell

            pip install litestar[minijinja]

.. tip::

    *Jinja* is included in the ``standard`` extra. If you installed Litestar using
    ``litestar[standard]``, you do not need to explicitly add the ``jinja`` extra.


Registering a template engine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To register one of the built-in template engines you simply need to pass it to the Litestar constructor:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/template_engine_jinja.py
            :language: python

    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/template_engine_mako.py
            :language: python

    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/template_engine_minijinja.py
            :language: python

.. note::

    The ``directory`` parameter passed to :class:`TemplateConfig <litestar.template.TemplateConfig>`
    can be either a directory or list of directories to use for loading templates.

Registering a Custom Template Engine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The above example will create a jinja Environment instance, but you can also pass in your own instance.

.. literalinclude:: /examples/templating/registering_new_template.py
    :language: python


.. note::

    The ``instance`` parameter passed to :class:`TemplateConfig <litestar.template.TemplateConfig>`
    can not be used in conjunction with the ``directory`` parameter, if you choose to use instance you're fully responsible on the engine creation.

Defining a custom template engine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to use another templating engine, you can easily do so by implementing
:class:`TemplateEngineProtocol <litestar.template.TemplateEngineProtocol>`. This class accepts a generic
argument which should be the template class, and it specifies two methods:

.. literalinclude:: /examples/templating/engine_custom.py
    :language: python


Once you have your custom engine you can register it as you would the built-in engines.

Accessing the template engine instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to access the template engine instance, you can do so via the
:class:`TemplateConfig.engine <litestar.template.TemplateConfig>` attribute:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/engine_instance_jinja.py
            :language: python

    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/engine_instance_mako.py
            :language: python

    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/engine_instance_minijinja.py
            :language: python

Template responses
------------------

Once you have a template engine registered you can return :class:`templates responses <.response.Template>` from
your route handlers:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/returning_templates_jinja.py
            :language: python

    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/returning_templates_mako.py
            :language: python

    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/returning_templates_minijinja.py
            :language: python

* ``name`` is the name of the template file within on of the specified directories. If
  no file with that name is found, a :class:`TemplateNotFoundException <.exceptions.TemplateNotFoundException>`
  exception will be raised.
* ``context`` is a dictionary containing arbitrary data that will be passed to the template
  engine's ``render`` method. For Jinja and Mako, this data will be available in the `template context <#template-context>`_

Template Files vs. Strings
--------------------------

When you define a template response, you can either pass a template file name or a string
containing the template. The latter is useful if you want to define the template inline
for small templates or :doc:`HTMX </usage/htmx>` responses for example.

.. tab-set::

    .. tab-item:: File name

            .. literalinclude:: /examples/templating/template_file.py
                :caption: Template via file
                :language: python


    .. tab-item:: String

            .. literalinclude:: /examples/templating/template_string.py
                :caption: Template via string
                :language: python


Template context
----------------

Both `Jinja2 <https://jinja.palletsprojects.com/en/3.0.x/>`_ and `Mako <https://www.makotemplates.org/>`_ support passing a context
object to the template as well as defining callables that will be available inside the template.

Accessing the request instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current :class:`Request <litestar.connection.request.Request>` is available within the
template context under ``request``, which also provides access to the :doc:`app instance </usage/applications>`.

Accessing ``app.state.key`` for example would look like this:
<strong>check_context_key: </strong>{{ check_context_key() }}

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/templates/request_instance.html.jinja2
            :language: html


    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/templates/request_instance.html.mako
            :language: html


    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/templates/request_instance.html.minijinja
            :language: html


Adding CSRF inputs
^^^^^^^^^^^^^^^^^^

If you want to add a hidden ``<input>`` tag containing a
`CSRF token <https://developer.mozilla.org/en-US/docs/Web/Security/Types_of_attacks#cross-site_request_forgery_csrf>`_,
you first need to configure :ref:`CSRF protection <usage/middleware/builtin-middleware:csrf>`.
With that in place, you can now insert the CSRF input field inside an HTML form:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/templates/csrf_inputs.html.jinja2
            :language: html


    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/templates/csrf_inputs.html.mako
            :language: html


    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/templates/csrf_inputs.html.minijinja
            :language: html


The input holds a CSRF token as its value and is hidden so users cannot see or interact with it. The token is sent
back to the server when the form is submitted, and is checked by the CSRF middleware.

.. note::

    The `csrf_input` must be marked as safe in order to ensure that it does not get escaped.

Passing template context
^^^^^^^^^^^^^^^^^^^^^^^^

Passing context to the template is very simple - its one of the kwargs expected by the :class:`Template <litestar.response.Template>`
container, so simply pass a string keyed dictionary of values:

.. literalinclude:: /examples/templating/passing_template_context.py
    :language: python


Template callables
------------------

Both `Jinja2 <https://jinja.palletsprojects.com/en/3.0.x/>`_ and `Mako <https://www.makotemplates.org/>`_ allow users to define custom
callables that are ran inside the template. Litestar builds on this and offers some functions out of the box.

Built-in callables
^^^^^^^^^^^^^^^^^^

``url_for``
    To access urls for route handlers you can use the ``url_for`` function. Its signature and behaviour
    matches :meth:`route_reverse <litestar.app.Litestar.route_reverse>` behaviour. More details about route handler indexing
    can be found :ref:`here <usage/routing/handlers:route handler indexing>`.

``csrf_token``
    This function returns the request's unique :ref:`CSRF token <usage/middleware/builtin-middleware:csrf>` You can use this
    if you wish to insert the ``csrf_token`` into non-HTML based templates, or insert it into HTML templates not using a hidden input field but
    by some other means, for example inside a special ``<meta>`` tag.

``url_for_static_asset``
    URLs for static files can be created using the ``url_for_static_asset`` function. It's signature and behaviour are identical to
    :meth:`app.url_for_static_asset <litestar.app.Litestar.url_for_static_asset>`.


Registering template callables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The  :class:`TemplateEngineProtocol <litestar.template.base.TemplateEngineProtocol>` specifies the method
``register_template_callable`` that allows defining a custom callable on a template engine. This method is implemented
for the two built in engines, and it can be used to register callables that will be injected into the template. The callable
should expect one argument - the context dictionary. It can be any callable - a function, method, or class that defines
the call method. For example:

.. tab-set::

    .. tab-item:: Jinja
        :sync: jinja

        .. literalinclude:: /examples/templating/template_functions_jinja.py
            :caption: template_functions.py
            :language: python

        .. literalinclude:: /examples/templating/templates/index.html.jinja2
            :language: html
            :caption: templates/index.html.jinja2

    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/templating/template_functions_mako.py
            :caption: template_functions.py
            :language: python

        .. literalinclude:: /examples/templating/templates/index.html.mako
            :language: html
            :caption: templates/index.html.mako

    .. tab-item:: Minijinja
        :sync: minijinja

        .. literalinclude:: /examples/templating/template_functions_minijinja.py
            :caption: template_functions.py
            :language: python

        .. literalinclude:: /examples/templating/templates/index.html.minijinja
            :language: html
            :caption: templates/index.html.minijinja

Run the example with ``uvicorn template_functions:app`` , visit  http://127.0.0.1:8000, and
you'll see

.. image:: /images/examples/template_engine_callable.png
    :alt: Template engine callable example
