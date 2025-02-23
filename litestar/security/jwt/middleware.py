from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from litestar.exceptions import NotAuthorizedException
from litestar.middleware.authentication import (
    AbstractAuthenticationMiddleware,
    AuthenticationResult,
)
from litestar.security.jwt.token import Token

__all__ = ("JWTAuthenticationMiddleware", "JWTCookieAuthenticationMiddleware")


if TYPE_CHECKING:
    from collections.abc import Awaitable, Sequence
    from typing import Any

    from litestar.connection import ASGIConnection
    from litestar.types import ASGIApp, Method, Scopes


class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    """JWT Authentication middleware.

    This class provides JWT authentication functionalities.
    """

    __slots__ = (
        "algorithm",
        "auth_header",
        "require_claims",
        "retrieve_user_handler",
        "revoked_token_handler",
        "strict_audience",
        "token_audience",
        "token_cls",
        "token_issuer",
        "token_secret",
        "verify_expiry",
        "verify_not_before",
    )

    def __init__(
        self,
        algorithm: str,
        app: ASGIApp,
        auth_header: str,
        exclude: str | list[str] | None,
        exclude_http_methods: Sequence[Method] | None,
        exclude_opt_key: str,
        retrieve_user_handler: Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[Any]],
        scopes: Scopes,
        token_secret: str,
        token_cls: type[Token] = Token,
        token_audience: Sequence[str] | None = None,
        token_issuer: Sequence[str] | None = None,
        require_claims: Sequence[str] | None = None,
        verify_expiry: bool = True,
        verify_not_before: bool = True,
        strict_audience: bool = False,
        revoked_token_handler: Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[Any]] | None = None,
    ) -> None:
        """Check incoming requests for an encoded token in the auth header specified, and if present retrieve the user
        from persistence using the provided function.

        Args:
            algorithm: JWT hashing algorithm to use.
            app: An ASGIApp, this value is the next ASGI handler to call in the middleware stack.
            auth_header: Request header key from which to retrieve the token. E.g. ``Authorization`` or ``X-Api-Key``.
            exclude: A pattern or list of patterns to skip.
            exclude_opt_key: An identifier to use on routes to disable authentication for a particular route.
            exclude_http_methods: A sequence of http methods that do not require authentication.
            retrieve_user_handler: A function that receives a :class:`Token <.security.jwt.Token>` and returns a user,
                which can be any arbitrary value.
            scopes: ASGI scopes processed by the authentication middleware.
            token_secret: Secret for decoding the JWT. This value should be equivalent to the secret used to
                encode it.
            token_cls: Token class used when encoding / decoding JWTs
            token_audience: Verify the audience when decoding the token. If the audience
                in the token does not match any audience given, raise a
                :exc:`NotAuthorizedException`
            token_issuer: Verify the issuer when decoding the token. If the issuer in
                the token does not match any issuer given, raise a
                :exc:`NotAuthorizedException`
            require_claims: Require these claims to be present in the JWT payload
            verify_expiry: Verify that the value of the ``exp`` (*expiration*) claim is in the future
            verify_not_before: Verify that the value of the ``nbf`` (*not before*) claim is in the past
            strict_audience: Verify that the value of the ``aud`` (*audience*) claim is a single value, and
                not a list of values, and matches ``audience`` exactly. Requires that
                ``accepted_audiences`` is a sequence of length 1
            revoked_token_handler: A function that receives a :class:`Token <.security.jwt.Token>` and returns a boolean
                indicating whether the token has been revoked.
        """
        super().__init__(
            app=app,
            exclude=exclude,
            exclude_from_auth_key=exclude_opt_key,
            exclude_http_methods=exclude_http_methods,
            scopes=scopes,
        )
        self.algorithm = algorithm
        self.auth_header = auth_header
        self.retrieve_user_handler = retrieve_user_handler
        self.revoked_token_handler = revoked_token_handler
        self.token_secret = token_secret
        self.token_cls = token_cls
        self.token_audience = token_audience
        self.token_issuer = token_issuer
        self.require_claims = require_claims
        self.verify_expiry = verify_expiry
        self.verify_not_before = verify_not_before
        self.strict_audience = strict_audience

    async def authenticate_request(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthenticationResult:
        """Given an HTTP Connection, parse the JWT api key stored in the header and retrieve the user correlating to the
        token from the DB.

        Args:
            connection: An Litestar HTTPConnection instance.

        Returns:
            AuthenticationResult

        Raises:
            NotAuthorizedException: If token is invalid or user is not found.
        """
        auth_header = connection.headers.get(self.auth_header)
        if not auth_header:
            raise NotAuthorizedException("No JWT token found in request header")
        encoded_token = auth_header.partition(" ")[-1]
        return await self.authenticate_token(encoded_token=encoded_token, connection=connection)

    async def authenticate_token(
        self, encoded_token: str, connection: ASGIConnection[Any, Any, Any, Any]
    ) -> AuthenticationResult:
        """Given an encoded JWT token, parse, validate and look up sub within token.

        Args:
            encoded_token: Encoded JWT token.
            connection: An ASGI connection instance.

        Raises:
            NotAuthorizedException: If token is invalid or user is not found.

        Returns:
            AuthenticationResult
        """
        token = self.token_cls.decode(
            encoded_token=encoded_token,
            secret=self.token_secret,
            algorithm=self.algorithm,
            audience=self.token_audience,
            issuer=self.token_issuer,
            require_claims=self.require_claims,
            verify_exp=self.verify_expiry,
            verify_nbf=self.verify_not_before,
            strict_audience=self.strict_audience,
        )

        user = await self.retrieve_user_handler(token, connection)
        token_revoked = False

        if self.revoked_token_handler:
            token_revoked = await self.revoked_token_handler(token, connection)

        if not user or token_revoked:
            raise NotAuthorizedException()

        return AuthenticationResult(user=user, auth=token)


class JWTCookieAuthenticationMiddleware(JWTAuthenticationMiddleware):
    """Cookie based JWT authentication middleware."""

    __slots__ = ("auth_cookie_key",)

    def __init__(
        self,
        algorithm: str,
        app: ASGIApp,
        auth_cookie_key: str,
        auth_header: str,
        exclude: str | list[str] | None,
        exclude_opt_key: str,
        exclude_http_methods: Sequence[Method] | None,
        retrieve_user_handler: Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[Any]],
        scopes: Scopes,
        token_secret: str,
        token_cls: type[Token] = Token,
        token_audience: Sequence[str] | None = None,
        token_issuer: Sequence[str] | None = None,
        require_claims: Sequence[str] | None = None,
        verify_expiry: bool = True,
        verify_not_before: bool = True,
        strict_audience: bool = False,
        revoked_token_handler: Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[Any]] | None = None,
    ) -> None:
        """Check incoming requests for an encoded token in the auth header or cookie name specified, and if present
        retrieves the user from persistence using the provided function.

        Args:
            algorithm: JWT hashing algorithm to use.
            app: An ASGIApp, this value is the next ASGI handler to call in the middleware stack.
            auth_cookie_key: Cookie name from which to retrieve the token. E.g. ``token`` or ``accessToken``.
            auth_header: Request header key from which to retrieve the token. E.g. ``Authorization`` or ``X-Api-Key``.
            exclude: A pattern or list of patterns to skip.
            exclude_opt_key: An identifier to use on routes to disable authentication for a particular route.
            exclude_http_methods: A sequence of http methods that do not require authentication.
            retrieve_user_handler: A function that receives a :class:`Token <.security.jwt.Token>` and returns a user,
                which can be any arbitrary value.
            scopes: ASGI scopes processed by the authentication middleware.
            token_secret: Secret for decoding the JWT. This value should be equivalent to the secret used to
                encode it.
            token_cls: Token class used when encoding / decoding JWTs
            token_audience: Verify the audience when decoding the token. If the audience
                in the token does not match any audience given, raise a
                :exc:`NotAuthorizedException`
            token_issuer: Verify the issuer when decoding the token. If the issuer in
                the token does not match any issuer given, raise a
                :exc:`NotAuthorizedException`
            require_claims: Require these claims to be present in the JWT payload
            verify_expiry: Verify that the value of the ``exp`` (*expiration*) claim is in the future
            verify_not_before: Verify that the value of the ``nbf`` (*not before*) claim is in the past
            strict_audience: Verify that the value of the ``aud`` (*audience*) claim is a single value, and
                not a list of values, and matches ``audience`` exactly. Requires that
                ``accepted_audiences`` is a sequence of length 1
            revoked_token_handler: A function that receives a :class:`Token <.security.jwt.Token>` and returns a boolean
                indicating whether the token has been revoked.
        """
        super().__init__(
            algorithm=algorithm,
            app=app,
            auth_header=auth_header,
            exclude=exclude,
            exclude_http_methods=exclude_http_methods,
            exclude_opt_key=exclude_opt_key,
            retrieve_user_handler=retrieve_user_handler,
            revoked_token_handler=revoked_token_handler,
            scopes=scopes,
            token_secret=token_secret,
            token_cls=token_cls,
            token_audience=token_audience,
            token_issuer=token_issuer,
            require_claims=require_claims,
            verify_expiry=verify_expiry,
            verify_not_before=verify_not_before,
            strict_audience=strict_audience,
        )
        self.auth_cookie_key = auth_cookie_key

    async def authenticate_request(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthenticationResult:
        """Given an HTTP Connection, parse the JWT api key stored in the header and retrieve the user correlating to the
        token from the DB.

        Args:
            connection: An Litestar HTTPConnection instance.

        Raises:
            NotAuthorizedException: If token is invalid or user is not found.

        Returns:
            AuthenticationResult
        """
        auth_header = connection.headers.get(self.auth_header) or connection.cookies.get(self.auth_cookie_key)
        if not auth_header:
            raise NotAuthorizedException("No JWT token found in request header or cookies")
        encoded_token = auth_header.partition(" ")[-1]
        return await self.authenticate_token(encoded_token=encoded_token, connection=connection)
