from __future__ import annotations

import dataclasses
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional, TypedDict

import jwt
import msgspec

from litestar.exceptions import ImproperlyConfiguredException, NotAuthorizedException

if TYPE_CHECKING:
    from collections.abc import Sequence

    from typing_extensions import Self

__all__ = (
    "JWTDecodeOptions",
    "Token",
)


def _normalize_datetime(value: datetime) -> datetime:
    """Convert the given value into UTC and strip microseconds.

    Args:
        value: A datetime instance

    Returns:
        A datetime instance
    """
    if value.tzinfo is not None:
        value.astimezone(timezone.utc)

    return value.replace(microsecond=0)


class JWTDecodeOptions(TypedDict, total=False):
    """``options`` for PyJWTs :func:`jwt.decode`"""

    verify_aud: bool
    verify_iss: bool
    verify_exp: bool
    verify_nbf: bool
    strict_aud: bool
    require: list[str]


@dataclass
class Token:
    """JWT Token DTO."""

    exp: datetime
    """Expiration - datetime for token expiration."""
    sub: str
    """Subject - usually a unique identifier of the user or equivalent entity."""
    iat: datetime = field(default_factory=lambda: _normalize_datetime(datetime.now(timezone.utc)))
    """Issued at - should always be current now."""
    iss: Optional[str] = field(default=None)  # noqa: UP007
    """Issuer - optional unique identifier for the issuer."""
    aud: Optional[str] = field(default=None)  # noqa: UP007
    """Audience - intended audience."""
    jti: Optional[str] = field(default=None)  # noqa: UP007
    """JWT ID - a unique identifier of the JWT between different issuers."""
    extras: dict[str, Any] = field(default_factory=dict)
    """Extra fields that were found on the JWT token."""

    def __post_init__(self) -> None:
        if len(self.sub) < 1:
            raise ImproperlyConfiguredException("sub must be a string with a length greater than 0")

        if isinstance(self.exp, datetime) and (
            (exp := _normalize_datetime(self.exp)).timestamp()
            >= _normalize_datetime(datetime.now(timezone.utc)).timestamp()
        ):
            self.exp = exp
        else:
            raise ImproperlyConfiguredException("exp value must be a datetime in the future")

        if isinstance(self.iat, datetime) and (
            (iat := _normalize_datetime(self.iat)).timestamp()
            <= _normalize_datetime(datetime.now(timezone.utc)).timestamp()
        ):
            self.iat = iat
        else:
            raise ImproperlyConfiguredException("iat must be a current or past time")

    @classmethod
    def decode_payload(
        cls,
        encoded_token: str,
        secret: str,
        algorithms: list[str],
        issuer: list[str] | None = None,
        audience: str | Sequence[str] | None = None,
        options: JWTDecodeOptions | None = None,
    ) -> Any:
        """Decode and verify the JWT and return its payload"""
        return jwt.decode(
            jwt=encoded_token,
            key=secret,
            algorithms=algorithms,
            issuer=issuer,
            audience=audience,
            options=options,  # type: ignore[arg-type]
        )

    @classmethod
    def decode(
        cls,
        encoded_token: str,
        secret: str,
        algorithm: str,
        audience: str | Sequence[str] | None = None,
        issuer: str | Sequence[str] | None = None,
        require_claims: Sequence[str] | None = None,
        verify_exp: bool = True,
        verify_nbf: bool = True,
        strict_audience: bool = False,
    ) -> Self:
        """Decode a passed in token string and return a Token instance.

        Args:
            encoded_token: A base64 string containing an encoded JWT.
            secret: The secret with which the JWT is encoded.
            algorithm: The algorithm used to encode the JWT.
            audience: Verify the audience when decoding the token. If the audience in
                the token does not match any audience given, raise a
                :exc:`NotAuthorizedException`
            issuer: Verify the issuer when decoding the token. If the issuer in the
                token does not match any issuer given, raise a
                :exc:`NotAuthorizedException`
            require_claims: Verify that the given claims are present in the token
            verify_exp: Verify that the value of the ``exp`` (*expiration*) claim is in
                the future
            verify_nbf: Verify that the value of the ``nbf`` (*not before*) claim is in
                the past
            strict_audience: Verify that the value of the ``aud`` (*audience*) claim is
                a single value, and not a list of values, and matches ``audience``
                exactly. Requires the value passed to the ``audience`` to be a sequence
                of length 1

        Returns:
            A decoded Token instance.

        Raises:
            NotAuthorizedException: If the token is invalid.
        """

        options: JWTDecodeOptions = {
            "verify_aud": bool(audience),
            "verify_iss": bool(issuer),
        }
        if require_claims:
            options["require"] = list(require_claims)
        if verify_exp is False:
            options["verify_exp"] = False
        if verify_nbf is False:
            options["verify_nbf"] = False
        if strict_audience:
            if audience is None or (not isinstance(audience, str) and len(audience) != 1):
                raise ValueError("When using 'strict_audience=True', 'audience' must be a sequence of length 1")
            options["strict_aud"] = True
            # although not documented, pyjwt requires audience to be a string if
            # using the strict_aud option
            if not isinstance(audience, str):
                audience = audience[0]

        try:
            payload = cls.decode_payload(
                encoded_token=encoded_token,
                secret=secret,
                algorithms=[algorithm],
                audience=audience,
                issuer=list(issuer) if issuer else None,
                options=options,
            )
            # msgspec can do these conversions as well, but to keep backwards
            # compatibility, we do it ourselves, since the datetime parsing works a
            # little bit different there
            payload["exp"] = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            payload["iat"] = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            extra_fields = payload.keys() - {f.name for f in dataclasses.fields(cls)}
            extras = payload.setdefault("extras", {})
            for key in extra_fields:
                extras[key] = payload.pop(key)
            return msgspec.convert(payload, cls, strict=False)
        except (
            KeyError,
            jwt.exceptions.InvalidTokenError,
            ImproperlyConfiguredException,
            msgspec.ValidationError,
        ) as e:
            raise NotAuthorizedException("Invalid token") from e

    def encode(self, secret: str, algorithm: str) -> str:
        """Encode the token instance into a string.

        Args:
            secret: The secret with which the JWT is encoded.
            algorithm: The algorithm used to encode the JWT.

        Returns:
            An encoded token string.

        Raises:
            ImproperlyConfiguredException: If encoding fails.
        """
        try:
            return jwt.encode(
                payload={k: v for k, v in asdict(self).items() if v is not None},
                key=secret,
                algorithm=algorithm,
            )
        except (jwt.DecodeError, NotImplementedError) as e:
            raise ImproperlyConfiguredException("Failed to encode token") from e
