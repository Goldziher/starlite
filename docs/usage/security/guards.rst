Guards
======

Guards are callables that receive two arguments - ``connection``, which is the
:class:`ASGIConnection <.connection.ASGIConnection>` instance, and ``route_handler``, which is a copy of the
:class:`BaseRouteHandler <.handlers.BaseRouteHandler>`. Their role is to *authorize* the request by verifying that
the connection is allowed to reach the endpoint handler in question. If verification fails, the guard should raise an
HTTPException, usually a :class:`NotAuthorizedException <.exceptions.NotAuthorizedException>` with a ``status_code``
of 401.

To illustrate this we will implement a rudimentary role based authorization system in our Litestar app. As we have done
for ``authentication``, we will assume that we added some sort of persistence layer without actually
specifying it in the example.

We begin by creating an :class:`Enum <enum.Enum>` with two roles - ``consumer`` and ``admin``\ :

.. code-block:: python

   from enum import Enum


   class UserRole(str, Enum):
       CONSUMER = "consumer"
       ADMIN = "admin"

Our ``User`` model will now look like this:

.. code-block:: python

   from pydantic import BaseModel, UUID4
   from enum import Enum


   class UserRole(str, Enum):
       CONSUMER = "consumer"
       ADMIN = "admin"


   class User(BaseModel):
       id: UUID4
       role: UserRole

       @property
       def is_admin(self) -> bool:
           """Determines whether the user is an admin user"""
           return self.role == UserRole.ADMIN

Given that the User model has a "role" property we can use it to authorize a request. Let's create a guard that only
allows admin users to access certain route handlers and then add it to a route handler function:

.. code-block:: python

   from enum import Enum

   from pydantic import BaseModel, UUID4
   from litestar import post
   from litestar.connection import ASGIConnection
   from litestar.exceptions import NotAuthorizedException
   from litestar.handlers.base import BaseRouteHandler


   class UserRole(str, Enum):
       CONSUMER = "consumer"
       ADMIN = "admin"


   class User(BaseModel):
       id: UUID4
       role: UserRole

       @property
       def is_admin(self) -> bool:
           """Determines whether the user is an admin user"""
           return self.role == UserRole.ADMIN


   def admin_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
       if not connection.user.is_admin:
           raise NotAuthorizedException()


   @post(path="/user", guards=[admin_user_guard])
   def create_user(data: User) -> User: ...

Thus, only an admin user would be able to send a post request to the ``create_user`` handler.

Guard scopes
------------

Guards can be declared on all levels of the app - the Litestar instance, routers, controllers, and individual route
handlers:

.. code-block:: python

   from litestar import Controller, Router, Litestar
   from litestar.connection import ASGIConnection
   from litestar.handlers.base import BaseRouteHandler


   def my_guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None: ...


   # controller
   class UserController(Controller):
       path = "/user"
       guards = [my_guard]

       ...


   # router
   admin_router = Router(path="admin", route_handlers=[UserController], guards=[my_guard])

   # app
   app = Litestar(route_handlers=[admin_router], guards=[my_guard])

The deciding factor on where to place a guard is on the kind of access restriction that are required: do only specific
route handlers need to be restricted? An entire controller? All the paths under a specific router? Or the entire app?

As you can see in the above examples - ``guards`` is a list. This means you can add **multiple** guards at every layer.
Unlike ``dependencies`` , guards do not override each other but are rather *cumulative*. This means that you can define
guards on different levels of your app, and they will combine.

.. caution::

    If guards are placed at the controller or the app level, they **will** be executed on all ``OPTIONS`` requests as well.
    For more details, including a workaround, refer https://github.com/litestar-org/litestar/issues/2314.


The route handler "opt" key
---------------------------

Occasionally there might be a need to set some values on the route handler itself - these can be permissions, or some
other flag. This can be achieved with :ref:`the opts kwarg <handler_opts>` of route handler

To illustrate this lets say we want to have an endpoint that is guarded by a "secret" token, to which end we create
the following guard:

.. code-block:: python

   from litestar import get
   from litestar.exceptions import NotAuthorizedException
   from litestar.connection import ASGIConnection
   from litestar.handlers.base import BaseRouteHandler
   from os import environ


   def secret_token_guard(
       connection: ASGIConnection, route_handler: BaseRouteHandler
   ) -> None:
       if (
           route_handler.opt.get("secret")
           and not connection.headers.get("Secret-Header", "")
           == route_handler.opt["secret"]
       ):
           raise NotAuthorizedException()


   @get(path="/secret", guards=[secret_token_guard], opt={"secret": environ.get("SECRET")})
   def secret_endpoint() -> None: ...
