from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from starlite.openapi.spec.base import BaseSchemaObject

if TYPE_CHECKING:
    from starlite.openapi.spec.oauth_flows import OAuthFlows

__all__ = ("SecurityScheme",)


@dataclass
class SecurityScheme(BaseSchemaObject):
    """Defines a security scheme that can be used by the operations.

    Supported schemes are HTTP authentication,
    an API key (either as a header, a cookie parameter or as a query parameter),
    mutual TLS (use of a client certificate),
    OAuth2's common flows (implicit, password, client credentials and authorization code)
    as defined in `RFC6749 <https://tools.ietf.org/html/rfc6749>`_,
    and `OpenID Connect Discovery <https://tools.ietf.org/html/draft-ietf-oauth-discovery-06>`_.

    Please note that as of 2020, the implicit flow is about to be deprecated by
    `OAuth 2.0 Security Best Current Practice <https://tools.ietf.org/html/draft-ietf-oauth-security-topics>`_.
    Recommended for most use case is Authorization Code Grant flow with PKCE.
    """

    type: Literal["apiKey", "http", "mutualTLS", "oauth2", "openIdConnect"]
    """
    **REQUIRED**. The type of the security scheme.
    """

    description: str | None = None
    """A description for security scheme.

    `CommonMark syntax <https://spec.commonmark.org/>`_ MAY be used for
    rich text representation.
    """

    name: str | None = None
    """
    **REQUIRED** for `apiKey`. The name of the header, query or cookie parameter to be used.
    """

    security_scheme_in: Literal["query", "header", "cookie"] | None = None
    """
    **REQUIRED** for `apiKey`. The location of the API key.
    """

    scheme: str | None = None
    """
    **REQUIRED** for `http`. The name of the HTTP Authorization scheme to be used in the
    `Authorization header as defined in RFC7235 <https://tools.ietf.org/html/rfc7235#section-5.1>`_.

    The values used SHOULD be registered in the
    `IANA Authentication Scheme registry <https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml>`_.
    """

    bearer_format: str | None = None
    """A hint to the client to identify how the bearer token is formatted.

    Bearer tokens are usually generated by an authorization server, so
    this information is primarily for documentation purposes.
    """

    flows: OAuthFlows | None = None
    """
    **REQUIRED** for `oauth2`. An object containing configuration information for the flow types supported.
    """

    open_id_connect_url: str | None = None
    """
    **REQUIRED** for `openIdConnect`. OpenId Connect URL to discover OAuth2 configuration values.
    This MUST be in the form of a URL. The OpenID Connect standard requires the use of TLS.
    """
