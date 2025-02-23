===============
Getting Started
===============

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
   :caption: app.py

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

.. csv-table:: Litestar vs. other frameworks
   :file: _static/tables/framework-comparison.csv
   :widths: 5, 35, 15, 15, 15, 15
   :header-rows: 1

Example Applications
--------------------

* `litestar-pg-redis-docker <https://github.com/litestar-org/litestar-pg-redis-docker>`_ : In addition to Litestar, this
  demonstrates a pattern of application modularity, SQLAlchemy 2.0 ORM, Redis cache connectivity, and more. Like all
  Litestar projects, this application is open to contributions, big and small.
* `litestar-fullstack <https://github.com/litestar-org/litestar-fullstack>`_ : A fully-capable, production-ready fullstack
  Litestar web application configured with best practices. It includes SQLAlchemy 2.0, ReactJS, `Vite <https://vitejs.dev/>`_,
  `SAQ job queue <https://saq-py.readthedocs.io/en/latest/>`_, ``Jinja`` templates and more.
  `Read more <https://litestar-org.github.io/litestar-fullstack/latest/>`_.
* `litestar-hello-world <https://github.com/litestar-org/litestar-hello-world>`_: A bare-minimum application setup.
  Great for testing and POC work.
