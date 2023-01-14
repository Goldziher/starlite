import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Generator, Generic, Optional, TypeVar, cast

from anyio.from_thread import BlockingPortal, start_blocking_portal

from starlite import ASGIConnection, ImproperlyConfiguredException
from starlite.datastructures import MutableScopeHeaders  # noqa: TC001
from starlite.exceptions import MissingDependencyException
from starlite.types import AnyIOBackend, ASGIApp, HTTPResponseStartEvent

if TYPE_CHECKING:
    from starlite.middleware.session.base import BaseBackendConfig, BaseSessionBackend
    from starlite.middleware.session.cookie_backend import CookieBackend
try:
    pass
except ImportError as e:
    raise MissingDependencyException(
        "To use starlite.testing, install starlite with 'testing' extra, e.g. `pip install starlite[testing]`"
    ) from e

T = TypeVar("T", bound=ASGIApp)


def fake_http_send_message(headers: MutableScopeHeaders) -> HTTPResponseStartEvent:
    headers.setdefault("content-type", "application/text")
    return HTTPResponseStartEvent(type="http.response.start", status=200, headers=headers.headers)


def fake_asgi_connection(app: ASGIApp, cookies: Dict[str, str]) -> ASGIConnection[Any, Any, Any]:
    scope = {
        "type": "http",
        "path": "/",
        "raw_path": b"/",
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "method": "GET",
        "http_version": "1.1",
        "extensions": {"http.response.template": {}},
        "app": app,
        "state": {},
        "path_params": {},
        "route_handler": None,
        "_cookies": cookies,
    }
    return ASGIConnection[Any, Any, Any](
        scope=scope,  # type: ignore[arg-type]
    )


class BaseTestClient(Generic[T]):
    __test__ = False
    blocking_portal: "BlockingPortal"

    __slots__ = "app", "base_url", "backend", "backend_options", "session_config", "_session_backend"

    def __init__(
        self,
        app: T,
        base_url: str = "http://testserver.local",
        backend: AnyIOBackend = "asyncio",
        backend_options: Optional[Dict[str, Any]] = None,
        session_config: Optional["BaseBackendConfig"] = None,
    ):
        if "." not in base_url:
            warnings.warn(
                f"The base_url {base_url!r} might cause issues. Try adding a domain name such as .local: "
                f"'{base_url}.local'",
                UserWarning,
            )
        self._session_backend: Optional["BaseSessionBackend"] = None
        if session_config:
            self._session_backend = session_config._backend_class(config=session_config)
        self.app = app
        self.backend = backend
        self.backend_options = backend_options

    @property
    def session_backend(self) -> "BaseSessionBackend":
        if not self._session_backend:
            raise ImproperlyConfiguredException(
                "Session has not been initialized for this TestClient instance. You can"
                "do so by passing a configuration object to TestClient: TestClient(app=app, session_config=...)"
            )
        return self._session_backend

    @contextmanager
    def portal(self) -> Generator["BlockingPortal", None, None]:
        """Get a BlockingPortal.

        Returns:
            A contextmanager for a BlockingPortal.
        """
        if hasattr(self, "blocking_portal"):
            yield self.blocking_portal
        else:
            with start_blocking_portal(backend=self.backend, backend_options=self.backend_options) as portal:
                yield portal

    @staticmethod
    def _create_session_cookies(backend: "CookieBackend", data: Dict[str, Any]) -> Dict[str, str]:
        encoded_data = backend.dump_data(data=data)
        return {cookie.key: cast("str", cookie.value) for cookie in backend._create_session_cookies(encoded_data)}
