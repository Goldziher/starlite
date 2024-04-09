==============
Flash Messages
==============

.. versionadded:: 2.7.0

Flash messages are a powerful tool for conveying information to the user,
such as success notifications, warnings, or errors through one-time messages alongside a response due
to some kind of user action.

They are typically used to display a message on the next page load and are a great way
to enhance user experience by providing immediate feedback on their actions from things like form submissions.

Registering the plugin
----------------------

The FlashPlugin can be easily integrated with different templating engines.
Below are examples of how to register the ``FlashPlugin`` with ``Jinja2``, ``Mako``, and ``MiniJinja`` templating engines.

.. tab-set::

    .. tab-item:: Jinja2
        :sync: jinja

        .. literalinclude:: /examples/plugins/flash_messages/jinja.py
            :language: python
            :caption: Registering the flash message plugin using the Jinja2 templating engine

    .. tab-item:: Mako
        :sync: mako

        .. literalinclude:: /examples/plugins/flash_messages/mako.py
            :language: python
            :caption: Registering the flash message plugin using the Mako templating engine

    .. tab-item:: MiniJinja
        :sync: minijinja

        .. literalinclude:: /examples/plugins/flash_messages/minijinja.py
            :language: python
            :caption: Registering the flash message plugin using the MiniJinja templating engine

Using the plugin
----------------

After registering the FlashPlugin with your application, you can start using it to add and display
flash messages within your application routes.

Here is an example showing how to use the FlashPlugin with the Jinja2 templating engine to display flash messages.
The same approach applies to Mako and MiniJinja engines as well.

.. literalinclude:: /examples/plugins/flash_messages/usage.py
    :language: python
    :caption: Using the flash message plugin with Jinja2 templating engine to display flash messages

Breakdown
+++++++++

#. Here we import the requires classes and functions from the Litestar package and related plugins.
#. We then create our ``TemplateConfig`` and ``FlashConfig`` instances, each setting up the configuration for
   the template engine and flash messages, respectively.
#. A single route handler named ``index`` is defined using the ``@get()`` decorator.

   * Within this handler, the ``flash`` function is called to add a new flash message.
     This message is stored in the request's context, making it accessible to the template engine for rendering in the response.
   * The function returns a ``Template`` instance, where ``template_str``
     (read more about :ref:`template strings <usage/templating:template files vs. strings>`)
     contains inline HTML and Jinja2 template code.
     This template dynamically displays any flash messages by iterating over them with a Jinja2 for loop.
     Each message is wrapped in a paragraph (``<p>``) tag, showing the message content and its category.

#. Finally, a ``Litestar`` application instance is created, specifying the ``flash_plugin`` and ``index`` route handler in its configuration.
   The application is also configured with the ``template_config``, which includes the ``Jinja2`` templating engine and the path to the templates directory.
