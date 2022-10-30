import re
import secrets
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Pattern,
    Type,
    TypeVar,
    Union,
    cast,
)

from orjson import OPT_SERIALIZE_NUMPY, dumps, loads
from pydantic import BaseConfig, BaseModel, PrivateAttr, conint, conlist, constr
from starlette.datastructures import MutableHeaders
from typing_extensions import Literal

from starlite import ASGIConnection, Cookie, DefineMiddleware
from starlite.middleware.base import MiddlewareProtocol
from starlite.middleware.utils import should_bypass_middleware
from starlite.types import Empty
from starlite.utils import default_serializer, get_serializer_from_scope

if TYPE_CHECKING:
    from starlite.types import ASGIApp, Message, Receive, Scope, ScopeSession, Send


ONE_DAY_IN_SECONDS = 60 * 60 * 24

ConfigT = TypeVar("ConfigT", bound="BaseBackendConfig")
ServerConfigT = TypeVar("ServerConfigT", bound="ServerSideSessionConfig")
BaseSessionBackendT = TypeVar("BaseSessionBackendT", bound="BaseSessionBackend")


class BaseBackendConfig(BaseModel):
    _backend_class: Type["BaseSessionBackend"] = PrivateAttr()

    """Configuration for Session middleware cookies."""

    class Config(BaseConfig):
        arbitrary_types_allowed = True

    key: constr(min_length=1, max_length=256) = "session"  # type: ignore[valid-type]
    """
    Key to use for the cookie inside the header,
    e.g. `session=<data>` where 'session' is the cookie key and <data> is the session data.

    Notes:
        - If a session cookie exceeds 4KB in size it is split. In this case the key will be of the format
            'session-{segment number}'.
    """
    max_age: conint(ge=1) = ONE_DAY_IN_SECONDS * 14  # type: ignore[valid-type]
    """Maximal age of the cookie before its invalidated."""
    scopes: conlist(Literal["http", "websocket"], min_items=1, max_items=2) = ["http", "websocket"]  # type: ignore[valid-type]
    """Scopes for the middleware - options are 'http' and 'websocket' with the default being both"""
    path: str = "/"
    """Path fragment that must exist in the request url for the cookie to be valid. Defaults to '/'."""
    domain: Optional[str] = None
    """Domain for which the cookie is valid."""
    secure: bool = False
    """Https is required for the cookie."""
    httponly: bool = True
    """Forbids javascript to access the cookie via 'Document.cookie'."""
    samesite: Literal["lax", "strict", "none"] = "lax"
    """Controls whether or not a cookie is sent with cross-site requests. Defaults to 'lax'."""
    exclude: Optional[Union[str, List[str]]] = None
    """A pattern or list of patterns to skip in the session middleware."""
    exclude_opt_key: str = "skip_session"
    """An identifier to use on routes to disable the session middleware for a particular route"""

    @property
    def middleware(self) -> DefineMiddleware:
        """Use this property to insert the config into a middleware list on one
        of the application layers.

        Examples:

            ```python
            from os import urandom

            from starlite import Starlite, Request, get
            from starlite.middleware.session import SessionCookieConfig

            session_config = SessionCookieConfig(secret=urandom(16))


            @get("/")
            def my_handler(request: Request) -> None:
                ...


            app = Starlite(route_handlers=[my_handler], middleware=[session_config.middleware])
            ```

        Returns:
            An instance of DefineMiddleware including 'self' as the config kwarg value.
        """
        return DefineMiddleware(SessionMiddleware, backend=self._backend_class(config=self))


class ServerSideSessionConfig(BaseBackendConfig):
    session_id_bytes: int = 32
    """
    Number of bytes used to generate a random session-ID
    """


class BaseSessionBackend(ABC, Generic[ConfigT]):
    __slots__ = ("config",)

    def __init__(self, config: ConfigT) -> None:
        """Abstract session backend defining the interface between a storage
        mechanism and the [SessionMiddleware][
        starlite.middleware.session.SessionMiddleware].

        This serves as the base class for all client- and server-side
        backends
        """
        self.config = config

    @staticmethod
    def serlialize_data(data: "ScopeSession", scope: Optional["Scope"] = None) -> bytes:
        """Serialize data into bytes for storage in the backend.

        Args:
            data: Session data of the current scope
            scope: A scope, if applicable, from which to extract a serializer

        Returns:
            `data` serialized as bytes

        The serializer will be
        extracted from `scope` or fall back to [default_serializer][starlite.utils.default_serializer]
        """
        serializer = (get_serializer_from_scope(scope) if scope else None) or default_serializer
        return dumps(data, default=serializer, option=OPT_SERIALIZE_NUMPY)

    @staticmethod
    def deserialize_data(data: Any) -> Dict[str, Any]:
        """Deserialize data into a dictionary for use in the application scope.

        Args:
            data: Data to be deserialized

        Returns:
            Deserialized data as a dictionary
        """
        return cast("Dict[str, Any]", loads(data))

    @abstractmethod
    async def store_in_message(
        self, scope_session: "ScopeSession", message: "Message", connection: ASGIConnection
    ) -> None:
        """Stores the necessary information in the outgoing `Message`

        Args:
            scope_session: Current session to store
            message: Outgoing send-message
            connection: Originating ASGIConnection containing the scope

        Returns:
            None
        """

    @abstractmethod
    async def load_from_connection(self, connection: ASGIConnection) -> Dict[str, Any]:
        """Load session data from a connection and return it as a dictionary to
        be used in the current application scope.

        Args:
            connection: An ASGIConnection instance

        Returns:
            The session data

        Notes:
            - This should not modify the connection's scope. The data returned by this
            method will be stored in the application scope by the middleware
        """


class ServerSideBackend(Generic[ServerConfigT], BaseSessionBackend[ServerConfigT]):
    __slots__ = ()

    def __init__(self, config: ServerConfigT) -> None:
        """Base class for server-side backends. Implements.

        [BaseSessionBackend][starlite.middleware.session.base.BaseSessionBackend] and defines and
        interface which subclasses can implement to facilitate the storage of session data
        """
        super().__init__(config=config)

    @abstractmethod
    async def get(self, session_id: str) -> Union[bytes, str, Dict[str, Any], None]:
        """Retrieve data associated with `session_id`.

        Args:
            session_id: The session-ID

        Returns:
            The session data, if existing, otherwise `None`.
        """

    @abstractmethod
    async def set(self, session_id: str, data: bytes) -> None:
        """Store `data` under the `session_id` for later retrieval.

        If there is already data associated with `session_id`, replace
        it with `data` and reset its expiry time

        Args:
            session_id: The session-ID
            data: Serialized session data

        Returns:
            None
        """

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete the data associated with `session_id`. Fails silently if no
        such session-ID exists.

        Args:
            session_id: The session-ID

        Returns:
            None
        """

    @abstractmethod
    async def delete_all(self) -> None:
        """Delete all session data stored within this backend.

        Returns:
            None
        """

    def generate_session_id(self) -> str:
        """Generate a new session-ID, with n=[session_id_bytes][starlite.middle
        ware.session.base.ServerSideSessionConfig.session_id_bytes] random
        bytes.

        Returns:
            A session-ID
        """
        return secrets.token_hex(self.config.session_id_bytes)

    async def store_in_message(
        self, scope_session: "ScopeSession", message: "Message", connection: ASGIConnection
    ) -> None:
        """Stores the necessary information in the outgoing `Message` by
        setting a cookie containing the session-ID. If the session is empty, a
        null-cookie will be set. Otherwise, the serialised data will be stored
        using [set][starlite.middleware.session.base.ServerSideBackend.set],
        under the current session-id. If no session-ID exists, a new ID will be
        generated using [generate_session_id][starlite.middleware.session.base.
        ServerSideBackend.generate_session_id].

        Args:
            scope_session: Current session to store
            message: Outgoing send-message
            connection: Originating ASGIConnection containing the scope

        Returns:
            None
        """
        scope = connection.scope
        headers = MutableHeaders(scope=message)
        session_id = connection.cookies.get(self.config.key)
        if session_id == "null":
            session_id = None
        if not session_id:
            session_id = self.generate_session_id()

        cookie_params = self.config.dict(
            exclude_none=True,
            exclude={"secret", "key"} | set(self.config.__fields__) - set(BaseBackendConfig.__fields__),
        )

        if scope_session is Empty:
            await self.delete(session_id)
            headers.append(
                "Set-Cookie",
                Cookie(value="null", key=self.config.key, expires=0, **cookie_params).to_header(header=""),
            )
        else:
            serialised_data = self.serlialize_data(scope_session, scope)
            await self.set(session_id=session_id, data=serialised_data)

            headers["Set-Cookie"] = Cookie(value=session_id, key=self.config.key, **cookie_params).to_header(header="")

    async def load_from_connection(self, connection: ASGIConnection) -> Dict[str, Any]:
        """Load session data from a connection and return it as a dictionary to
        be used in the current application scope.

        The session-ID will be gathered from a cookie with the key set in the
        [configuration][starlite.middleware.session.base.BaseBackendConfig.key]. If
        a cookie is found, its value will be used as the session-ID and data associated
        with this ID will be loaded using [get][starlite.middleware.session.base.ServerSideBackend.get].
        If no cookie was found or no data was loaded from the store, this will return an
        empty dictionary.

        Args:
            connection: An ASGIConnection instance

        Returns:
            The current session data
        """
        session_id = connection.cookies.get(self.config.key)
        if session_id:
            data = await self.get(session_id)
            if isinstance(data, dict):
                return data
            if data is not None:
                return self.deserialize_data(data)
        return {}


class SessionMiddleware(MiddlewareProtocol, Generic[BaseSessionBackendT]):
    __slots__ = ("backend", "_exclude_pattern", "_exclude_opt_key")

    def __init__(self, app: "ASGIApp", backend: BaseSessionBackendT) -> None:
        """Starlite session middleware for storing session data.

        Args:
            app: An ASGI application
            backend: A [BaseSessionBackend][starlite.middleware.session.base.BaseSessionBackend]
                instance used to store and retrieve session data
        """

        self.app = app
        self.backend = backend
        self._exclude_pattern: Optional[Pattern[str]] = None
        self._exclude_opt_key = backend.config.exclude_opt_key

        if backend.config.exclude:
            exclude = backend.config.exclude
            self._exclude_pattern = re.compile("|".join(exclude)) if isinstance(exclude, list) else re.compile(exclude)

    def create_send_wrapper(self, connection: ASGIConnection) -> Callable[["Message"], Awaitable[None]]:
        """
        Creates a wrapper for the ASGI send function, which handles setting the cookies on the outgoing response.
        Args:
            connection: ASGIConnection

        Returns:
            None
        """

        async def wrapped_send(message: "Message") -> None:
            """A wrapper around the send function, declared in local scope to
            use closure values.

            Args:
                message: An ASGI message.

            Returns:
                None
            """
            if message["type"] != "http.response.start":
                await connection.send(message)
                return

            scope_session = connection.scope.get("session")

            await self.backend.store_in_message(scope_session, message, connection)
            await connection.send(message)

        return wrapped_send

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        """
        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        if not should_bypass_middleware(
            scope=scope,
            scopes=self.backend.config.scopes,
            exclude_opt_key=self._exclude_opt_key,
            exclude_path_pattern=self._exclude_pattern,
        ):
            connection = ASGIConnection[Any, Any, Any](scope, receive=receive, send=send)
            scope["session"] = await self.backend.load_from_connection(connection)

            await self.app(scope, receive, self.create_send_wrapper(connection))
        else:
            await self.app(scope, receive, send)
