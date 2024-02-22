Litestar library documentation
==============================

Litestar is a powerful, flexible, highly performant, and opinionated ASGI framework.

The Litestar framework supports :doc:`/usage/plugins`, ships
with :doc:`dependency injection </usage/dependency-injection>`, :doc:`security primitives </usage/security/index>`,
:doc:`OpenAPI schema generation </usage/openapi>`, `MessagePack <https://msgpack.org/>`_,
:doc:`middlewares </usage/middleware/index>`, a great :doc:`CLI </usage/cli>` experience, and much more.

Installation
------------

.. code-block:: shell

   pip install litestar

.. tip:: ``litestar[standard]`` includes commonly used extras like ``uvicorn`` and ``jinja2`` (for templating).

.. dropdown:: Extras
    :icon: star

    `Pydantic <https://docs.pydantic.dev/latest/>`_
        :code:`pip install litestar[pydantic]`

    `Attrs <https://www.attrs.org>`_
        :code:`pip install litestar[attrs]`

    :ref:`Brotli Compression Middleware <usage/middleware/builtin-middleware:brotli>`:
        :code:`pip install litestar[brotli]`

    :ref:`Cookie Based Sessions <usage/middleware/builtin-middleware:client-side sessions>`
        :code:`pip install litestar[cryptography]`

    :doc:`JWT </usage/security/jwt>`
        :code:`pip install litestar[jwt]`

    :doc:`RedisStore </usage/stores>`
        :code:`pip install litestar[redis]`

    :ref:`Picologging <usage/logging:using picologging>`
        :code:`pip install litestar[picologging]`

    :ref:`StructLog <usage/logging:using structlog>`
        :code:`pip install litestar[structlog]`

    :doc:`Prometheus Instrumentation </usage/metrics/prometheus>`
        :code:`pip install litestar[prometheus]`

    :doc:`Open Telemetry Instrumentation </usage/metrics/open-telemetry>`
        :code:`pip install litestar[opentelemetry]`

    :doc:`SQLAlchemy </usage/databases/sqlalchemy/index>`
        :code:`pip install litestar[sqlalchemy]`

    :doc:`CLI </usage/cli>`
        .. deprecated:: 2.1.1
           The ``litestar`` base installation now includes the CLI dependencies and this group is no longer required
           to use the CLI.
           If you need the optional CLI dependencies, install the ``standard`` group instead.
           **Will be removed in 3.0**

        :code:`pip install litestar[cli]`

    :doc:`Jinja Templating </usage/templating>`
        :code:`pip install litestar[jinja]`

    :doc:`Mako Templating </usage/templating>`
        :code:`pip install litestar[mako]`

    Standard Installation (includes Uvicorn and Jinja2 templating):
        :code:`pip install litestar[standard]`

    All Extras:
        :code:`pip install litestar[full]`

    .. note:: The full extras is not recommended because it will add a lot of unnecessary extras.

.. _minimal_example:

Minimal Example
---------------

At a minimum, make sure you have installed ``litestar[standard]``, which includes uvicorn.

First, create a file named ``app.py`` with the following contents:

.. code-block:: python

   from litestar import Litestar, get


   @get("/")
   async def index() -> str:
       return "Hello, world!"


   @get("/books/{book_id:int}")
   async def get_book(book_id: int) -> dict[str, int]:
       return {"book_id": book_id}


   app = Litestar([index, get_book])

Then, run the following command:

.. code-block:: shell

    litestar run
    # Or you can run Uvicorn directly:
    uvicorn app:app --reload

You can now visit ``http://localhost:8000/`` and ``http://localhost:8000/books/1`` in your browser and
you should see the responses of your two endpoints:

.. code-block:: text

   "Hello, world!"

and

.. code-block:: json

   {"book_id": 1}

.. tip:: You can also check out the automatically generated OpenAPI-based documentation at:

    * ``http://localhost:8000/schema`` (for `ReDoc <https://redocly.com/redoc>`_),
    * ``http://localhost:8000/schema/swagger`` (for `Swagger UI <https://swagger.io/>`_),
    * ``http://localhost:8000/schema/elements`` (for `Stoplight Elements <https://stoplight.io/open-source/elements/>`_)
    * ``http://localhost:8000/schema/rapidoc`` (for `RapiDoc <https://rapidocweb.com/>`_)

You can check out a more in-depth tutorial in the :doc:`/tutorials/todo-app/index` section!

Sponsors
--------

Litestar is a community-driven open-source initiative that thrives on the generous contributions of our sponsors,
enabling us to pursue innovative developments.

A huge thank you to our current sponsors:

.. raw:: html

    <div style="display: flex; justify-content: center; align-items: center; gap: 8px;">
      <div>
        <a href="https://scalar.com">
          <img src="https://raw.githubusercontent.com/litestar-org/branding/main/assets/sponsors/scalar.svg" alt="Scalar.com" style="border-radius: 10px; width: auto; max-height: 150px;"/>
        </a>
        <p style="text-align: center;">Scalar.com</p>
      </div>
      <div>
        <a href="https://telemetrysports.com/">
          <img src="https://raw.githubusercontent.com/litestar-org/branding/main/assets/sponsors/telemetry-sports/unofficial-telemetry-whitebg.svg" alt="Telemetry Sports" style="border-radius: 10px; width: auto; max-height: 150px;"/>
        </a>
        <p style="text-align: center;">Telemetry Sports</p>
      </div>
      <div>
        <a href="https://www.stok.kr/" title="Stok - Stack Up Your Assets!">
            <img src="https://avatars.githubusercontent.com/u/144093421?s=400&v=4" alt="Stok" style="border-radius: 10px; width: auto; max-height: 150px;" />
        </a>
        <p style="text-align: center;">Stok</p>
      </div>
    </div>

We invite organizations and individuals to join our sponsorship program.
By becoming a sponsor on platforms like `GitHub <sponsor-github_>`_
and `Open Collective <sponsor-oc_>`_, you can play a pivotal role in our project's growth.

Additionally, we engage in pledge-based sponsorship opportunities through `Polar <sponsor-polar_>`_.


.. _sponsor-github: https://github.com/sponsors/litestar-org
.. _sponsor-oc: https://opencollective.com/litestar
.. _sponsor-polar: https://polar.sh/litestar-org

Expanded Example
----------------

**Define your data model** using pydantic or any library based on it (for example ormar, beanie, SQLModel):

.. code-block:: python

    from pydantic import BaseModel, UUID4


    class User(BaseModel):
        first_name: str
        last_name: str
        id: UUID4




You can also use dataclasses (standard library and Pydantic),
:class:`typing.TypedDict`, or :class:`msgspec.Struct`.

.. code-block:: python

   from uuid import UUID

   from dataclasses import dataclass
   from litestar.dto import DTOConfig, DataclassDTO


   @dataclass
   class User:
       first_name: str
       last_name: str
       id: UUID


   class PartialUserDTO(DataclassDTO[User]):
       config = DTOConfig(exclude={"id"}, partial=True)

**Define a Controller for your data model:**

.. code-block:: python

    from typing import List

    from litestar import Controller, get, post, put, patch, delete
    from litestar.dto import DTOData
    from pydantic import UUID4

    from my_app.models import User, PartialUserDTO


    class UserController(Controller):
        path = "/users"

        @post()
        async def create_user(self, data: User) -> User: ...

        @get()
        async def list_users(self) -> List[User]: ...

        @patch(path="/{user_id:uuid}", dto=PartialUserDTO)
        async def partial_update_user(
            self, user_id: UUID4, data: DTOData[User]
        ) -> User: ...

        @put(path="/{user_id:uuid}")
        async def update_user(self, user_id: UUID4, data: User) -> User: ...

        @get(path="/{user_id:uuid}")
        async def get_user(self, user_id: UUID4) -> User: ...

        @delete(path="/{user_id:uuid}")
        async def delete_user(self, user_id: UUID4) -> None: ...


When instantiating your app, import your *controller* into your application's
entry-point and pass it to Litestar:

.. code-block:: python

   from litestar import Litestar

   from my_app.controllers.user import UserController

   app = Litestar(route_handlers=[UserController])

To **run your application**, use an ASGI server such as `uvicorn <https://www.uvicorn.org/>`_ :

.. code-block:: shell

   uvicorn my_app.main:app --reload


Philosophy
----------

- Litestar is a community-driven project. This means not a single author,
  but rather a core team of maintainers is leading the project, supported by a community
  of contributors. Litestar currently has 5 maintainers and is being very actively developed.
- Litestar draws inspiration from `NestJS <https://nestjs.com/>`_ - a contemporary TypeScript framework - which places
  opinions and patterns at its core.
- While still allowing for **function-based endpoints**, Litestar seeks to build on Python's powerful and versatile
  OOP, by placing **class-based controllers** at its core.
- Litestar is **not** a microframework. Unlike frameworks such as FastAPI, Starlette, or Flask, Litestar includes a lot
  of functionalities out of the box needed for a typical modern web application, such as ORM integration,
  client- and server-side sessions, caching, OpenTelemetry integration, and many more. It's not aiming to be "the next
  Django" (for example, it will never feature its own ORM), but its scope is not micro either.


Feature comparison with similar frameworks
------------------------------------------

+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
|                             | Litestar                           | FastAPI             | Starlette        | Sanic               | Quart               |
+=============================+====================================+=====================+==================+=====================+=====================+
| OpenAPI                     | :octicon:`check`                   | :octicon:`check`    | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Automatic API documentation | Swagger, ReDoc, Stoplight Elements | Swagger, ReDoc      | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Data validation             | :octicon:`check`                   | :octicon:`check`    | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Dependency Injection        | :octicon:`check`                   | :octicon:`check`    | :octicon:`dash`  | :octicon:`check`    | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Class based routing         | :octicon:`check`                   | (Through extension) | :octicon:`check` | :octicon:`check`    | :octicon:`check`    |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| ORM integration             | SQLAlchemy, Tortoise, Piccolo      | :octicon:`dash`     | :octicon:`dash`  | :octicon:`dash`     | (Through extension) |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Templating                  | Jinja, Mako                        | Jinja               | Jinja            | Jinja               | Jinja               |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| MessagePack                 | :octicon:`check`                   | :octicon:`dash`     | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| CORS                        | :octicon:`check`                   | :octicon:`check`    | :octicon:`check` | :octicon:`check`    | (Through extension) |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| CSRF                        | :octicon:`check`                   | :octicon:`dash`     | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Rate-limiting               | :octicon:`check`                   | :octicon:`dash`     | :octicon:`dash`  | (Through extension) | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| JWT                         | :octicon:`check`                   | :octicon:`dash`     | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Sessions                    | :octicon:`check`                   | Client-side         | Client-side      | :octicon:`dash`     | Client-side         |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Authentication              | JWT / Session based                | :octicon:`dash`     | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+
| Caching                     | :octicon:`check`                   |  :octicon:`dash`    | :octicon:`dash`  | :octicon:`dash`     | :octicon:`dash`     |
+-----------------------------+------------------------------------+---------------------+------------------+---------------------+---------------------+


Example Applications
--------------------


* `litestar-pg-redis-docker <https://github.com/litestar-org/litestar-pg-redis-docker>`_ : In addition to Litestar, this
  demonstrates a pattern of application modularity, SQLAlchemy 2.0 ORM, Redis cache connectivity, and more. Like all
  Litestar projects, this application is open to contributions, big and small.
* `litestar-fullstack <https://github.com/litestar-org/litestar-fullstack>`_ : A fully-capable, production-ready fullstack
  Litestar web application configured with best practices. It includes SQLAlchemy 2.0, VueJS, `Vite <https://vitejs.dev/>`_,
  `SAQ job queue <https://saq-py.readthedocs.io/en/latest/>`_, ``Jinja`` templates and more.
  `Read more <https://litestar-org.github.io/litestar-fullstack/latest/>`_.
* `litestar-hello-world <https://github.com/litestar-org/litestar-hello-world>`_: A bare-minimum application setup.
  Great for testing and POC work.


.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    usage/index
    reference/index
    benchmarks

.. toctree::
    :titlesonly:
    :caption: Guides
    :hidden:

    migration/index
    topics/index
    tutorials/index

.. toctree::
    :titlesonly:
    :caption: Contributing
    :hidden:

    contribution-guide
    Available Issues <https://github.com/search?q=user%3Alitestar-org+state%3Aopen+label%3A%22good+first+issue%22+++no%3Aassignee+&type=issues=>
    Code of Conduct <https://github.com/litestar-org/.github?tab=coc-ov-file#readme>
