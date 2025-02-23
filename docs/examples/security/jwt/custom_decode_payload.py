import dataclasses
from collections.abc import Sequence
from typing import Any, Optional, Union

from litestar.security.jwt.token import JWTDecodeOptions, Token


@dataclasses.dataclass
class CustomToken(Token):
    @classmethod
    def decode_payload(
        cls,
        encoded_token: str,
        secret: str,
        algorithms: list[str],
        issuer: Optional[list[str]] = None,
        audience: Union[str, Sequence[str], None] = None,
        options: Optional[JWTDecodeOptions] = None,
    ) -> Any:
        payload = super().decode_payload(
            encoded_token=encoded_token,
            secret=secret,
            algorithms=algorithms,
            issuer=issuer,
            audience=audience,
            options=options,
        )
        payload["sub"] = payload["sub"].split("@", maxsplit=1)[1]
        return payload
