# Route Handlers

Route handlers are the core of Starlite. They are constructed by decorating a function or method with one of the handler
decorators exported from Starlite.

## HTTP Route Handlers

The base decorator is called `route`:

```python
from starlite import HttpMethod, route


@route(path="/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...
```

What `route` does is wrap the given function or class method and replace it with an instance of the
class `HTTPRouteHandler`. In fact, route is merely an alias for `HTTPRouteHandler`, thus you could have done this
instead:

```python
from starlite import HttpMethod, HTTPRouteHandler


@HTTPRouteHandler(path="/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...
```

!!! important
    A function decorated by `route` or any of the other route handler decorator **must** have an annotated
    return value, even if the return value is `None` as in the above example. This limitation is enforced to ensure
    consistent schema generation, as well as stronger typing.

### Declaring Path(s)

All route handlers accept an optional path argument. This argument can be declared as a kwarg using the `path` key word:

```python
from starlite import HttpMethod, route


@route(path="/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...
```

It can also be passed as an argument without the key-word:

```python
from starlite import HttpMethod, route


@route("/some-path", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...
```

And the value for this argument can be either a string path, as in the above examples, or a list of string paths:

```python
from starlite import HttpMethod, route


@route(
    ["/some-path", "/some-other-path"], http_method=[HttpMethod.GET, HttpMethod.POST]
)
def my_endpoint() -> None:
    ...
```

This is particularly useful when you want to have optional [path parameters](3-parameters.md#path-parameters):

```python
from starlite import HttpMethod, route


@route(
    ["/some-path", "/some-path/{some_id:int}"],
    http_method=[HttpMethod.GET, HttpMethod.POST],
)
def my_endpoint(some_id: int = 1) -> None:
    ...
```

### Route Handler Kwargs

The `route` decorator **requires** an `http_method` kwarg, which is a member of the enum `starlite.enums.HttpMethod` or
a list of members, e.g. `HttpMethod.GET` or `[HttpMethod.PATCH, HttpMethod.PUT]`.

Additionally, you can pass the following optional kwargs:

- `status_code`: the status code for a success response. If not
  specified, [a default value will be used](5-responses.md#status-codes).
- `media_type`: A string or a member of the enum `starlite.enums.MediaType`, which specifies the MIME Media Type for the
  response. Defaults to `MediaType.JSON`. See [media-type](5-responses.md#media-type).
- `response_class`: A custom response class to be used as the app default.
  See [using-custom-responses](5-responses.md#using-custom-responses).
- `response_headers`: A dictionary of `ResponseHeader` instances.
  See [response-headers](5-responses.md#response-headers).
- `dependencies`: A dictionary mapping dependency providers. See [dependency-injection](6-dependency-injection.md).
- `opt`: String keyed dictionary of arbitrary value that can be used by [guards](9-guards.md).
- `before_request`: A sync or async function to execute before a `Request` is passed to the route handler. If this
  function returns a value, the request will not reach the route handler, and instead this value will be used.
- `after_request`: A sync or async function to execute before the `Response` is returned. This function receives the
  `Respose` object and it must return a `Response` object.
- `background_tasks`: A callable wrapped in an instance of `starlette.background.BackgroundTask` or a sequence
  of `BackgroundTask` instances wrapped in `starlette.background.BackgroundTasks`. The callable(s) will be called after
  the response is executed. Note - if you return a value from a `before_request` hook, background tasks passed to the
  handler will not be executed.

And the following kwargs, which affect [OpenAPI schema generation](12-openapi.md#route-handler-configuration)

- `include_in_schema`: A boolean flag dictating whether the given route handler will appear in the generated OpenAPI
  schema. Defaults to `True`.
- `tags`: a list of openapi-pydantic `Tag` models, which correlate to
  the [tag specification](https://spec.openapis.org/oas/latest.html#tag-object).
- `summary`: Text used for the route's schema _summary_ section.
- `description`: Text used for the route's schema _description_ section.
- `response_description`: Text used for the route's response schema _description_ section.
- `operation_id`: An identifier used for the route's schema _operationId_. Defaults to the `__name__` of the wrapped
  function.
- `deprecated`: A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema. Defaults
  to `False`.
- `raises`: A list of exception classes extending from `starlite.HttpException`. This list should describe all
  exceptions raised within the route handler's function/method. The Starlite `ValidationException` will be added
  automatically for the schema if any validation is involved.

### Semantic Handler Decorators

Starlite also includes "semantic" decorators, that is, decorators the pre-set the `http_method` kwarg to a specific HTTP
verb, which correlates with their name:

- `delete`
- `get`
- `patch`
- `post`
- `put`

These are used exactly like `route` with the sole exception that you cannot configure the `http_method` kwarg:

```python
from typing import List

from starlite import Partial, delete, get, patch, post, put

from my_app.models import Resource


@get(path="/resources")
def list_resources() -> List[Resource]:
    ...


@post(path="/resources")
def create_resource(data: Resource) -> Resource:
    ...


@get(path="/resources/{pk:int}")
def retrieve_resource(pk: int) -> Resource:
    ...


@put(path="/resources/{pk:int}")
def update_resource(data: Resource, pk: int) -> Resource:
    ...


@patch(path="/resources/{pk:int}")
def partially_update_resource(data: Partial[Resource], pk: int) -> Resource:
    ...


@delete(path="/resources/{pk:int}")
def delete_resource(pk: int) -> None:
    ...
```

Although these decorators are merely subclasses of `PathHandler` that pre-set the `http_method`, using _get_, _patch_
, _put_, _delete_ or _post_ instead of _route_ makes the code clearer and simpler.

Furthermore, in the OpenAPI specification each unique combination of http verb (e.g. "GET", "POST" etc.) and path is
regarded as a distinct [operation](https://spec.openapis.org/oas/latest.html#operation-object), and each operation
should be distinguished by a unique `operationId` and optimally also have a `summary` and `description` sections.

As such, using the `route` decorator is discouraged. Instead, the preferred pattern is to share code using secondary
class methods or by abstracting code to reusable functions.

## Websocket Route Handlers

!!! info
    This feature is available from v0.2.0 onwards

Alongside the HTTP Route handlers discussed above, Starlite also support Websockets via the `websocket` decorator:

```python
from starlite import WebSocket, websocket


@websocket(path="/socket")
async def my_websocket_handler(socket: WebSocket) -> None:
    await socket.accept()
    await socket.send_json({...})
    await socket.close()
```

The `websocket` decorator is also an aliased class, in this case - of the `WebsocketRouteHandler`. Thus. you can write
the above like so:

```python
from starlite import WebSocket, WebsocketRouteHandler


@WebsocketRouteHandler(path="/socket")
async def my_websocket_handler(socket: WebSocket) -> None:
    await socket.accept()
    await socket.send_json({...})
    await socket.close()
```

In difference to HTTP routes handlers, websocket handlers have the following requirements:

1. they **must** declare a `socket` kwarg. If this is missing an exception will be raised.
2. they **must** have a return annotation of `None`. Any other annotation, or lack thereof, will raise an exception.

Additionally, they should be async because the socket interface is async - but this is not enforced. You will not be
able to do anything meaningful without this and python will raise errors as required.

In all other regards websocket handlers function exactly like other route handlers.

!!! note
    OpenAPI currently does not support websockets. As a result not schema will be generated for websocket route
    handlers, and you cannot configure any schema related parameters for these.

## ASGI Route Handlers

!!! info
    This feature is available from v0.7.0 onwards

You can write your own ASGI apps using the `asgi` route handler decorator:

```python
from starlette.types import Scope, Receive, Send
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlite import Response, asgi


@asgi(path="/my-asgi-app")
async def my_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "http":
        if scope["method"] == "GET":
            response = Response({"hello": "world"}, status_code=HTTP_200_OK)
            await response(scope=scope, receive=receive, send=send)
        return
    response = Response(
        {"detail": "unsupported request"}, status_code=HTTP_400_BAD_REQUEST
    )
    await response(scope=scope, receive=receive, send=send)
```

!!! note
    ASGI apps are currently not handled in OpenAPI generation - although this might change in the future.

## Handler Function Kwargs

Route handler functions or methods access various data by declaring these as annotated function kwargs. The annotated
kwargs are inspected by Starlite and then injected into the request handler.

The following sources can be accessed using annotated function kwargs:

1. [path, query, header and cookie parameters](3-parameters.md)
2. [the request body](4-request-body.md)
3. [dependencies](6-dependency-injection.md)

Additionally, you can specify the following special kwargs:

- `state`: injects a copy of the application `state`.
- `request`: injects the request instance.
- `headers`: injects the request `headers` as a parsed dictionary.
- `query`: injects the request `query_params` as a parsed dictionary.
- `cookies`: injects the request `cookies` as a parsed dictionary.

For example:

```python
from typing import Any, Dict
from starlite import State, Request, get


@get(path="/")
def my_request_handler(
    state: State,
    request: Request,
    headers: Dict[str, Any],
    query: Dict[str, Any],
    cookies: Dict[str, Any],
) -> None:
    ...
```

!!! tip
    You can define a custom typing for your application state and then use it as a type instead of just using the
    State class from Starlite
