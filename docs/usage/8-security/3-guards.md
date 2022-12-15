# Guards

Guards are callables that receive two arguments - `connection`, which is the [`ASGIConnection`][starlite.connection.ASGIConnection]
instance, and `route_handler`, which is a copy of the [`BaseRouteHandler`][starlite.handlers.base.BaseRouteHandler].
Their role is to *authorize* the request by verifying that the connection is allowed to reach the endpoint handler in question.
If verification fails, the guard should raise an HTTPException, usually a
[`NotAuthorizedException`][starlite.exceptions.NotAuthorizedException] with a `status_code` of 401.

To illustrate this we will implement a rudimentary role based authorization system in our Starlite app. As we have done
for `authentication`, we will assume that we added some sort of persistence layer without actually
specifying it in the example.

We begin by creating an `Enum` with two roles - `consumer` and `admin`:

```python
from enum import Enum


class UserRole(str, Enum):
    CONSUMER = "consumer"
    ADMIN = "admin"
```

Our `User` model will now look like this:

```python
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
```

Given that the User model has a "role" property we can use it to authorize a request. Let's create a guard that only
allows admin users to access certain route handlers and then add it to a route handler function:

```python
from starlite import ASGIConnection, BaseRouteHandler, NotAuthorizedException
from pydantic import BaseModel, UUID4
from starlite import post
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


def admin_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_admin:
        raise NotAuthorizedException()


@post(path="/user", guards=[admin_user_guard])
def create_user(data: User) -> User:
    ...
```

Thus, only an admin user would be able to send a post request to the `create_user` handler.

## Guard Scopes

Guards can be declared on all levels of the app - the Starlite instance, routers, controllers and individual route
handlers:

```python
from starlite import ASGIConnection, Controller, Router, Starlite, BaseRouteHandler


def my_guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None:
    ...


# controller
class UserController(Controller):
    path = "/user"
    guards = [my_guard]

    ...


# router
admin_router = Router(path="admin", route_handlers=[UserController], guards=[my_guard])

# app
app = Starlite(route_handlers=[admin_router], guards=[my_guard])
```

The deciding factor on where to place a guard is on the kind of access restriction that are required: do only specific
route handlers need to be restricted? An entire controller? All the paths under a specific router? Or the entire app?

As you can see in the above examples - `guards` is a list. This means you can add **multiple** guards at every layer.
Unlike `dependencies`, guards do not override each other but are rather _cumulative_. This means that you can define
guards on different levels of your app, and they will combine.

## The Route Handler "opt" Key

Occasionally there might be a need to set some values on the route handler itself - these can be permissions, or some
other flag. This can be achieved with [`opts` kwarg](../2-route-handlers/5-handler-opts.md) of route handler

To illustrate this lets say we want to have an endpoint that is guarded by a "secret" token, to which end we create
the following guard:

```python
from starlite import ASGIConnection, BaseRouteHandler, NotAuthorizedException, get
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
def secret_endpoint() -> None:
    ...
```
