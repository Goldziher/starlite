from litestar import Litestar, get
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme, Tag


@get(
    "/public",
    tags=["public"],
    security=[{}],  # this endpoint is marked as having optional security
)
def public_path_handler() -> dict[str, str]:
    return {"hello": "world"}


@get("/other", tags=["internal"], security=[{"apiKey": []}])
def internal_path_handler() -> None: ...


app = Litestar(
    route_handlers=[public_path_handler, internal_path_handler],
    openapi_config=OpenAPIConfig(
        title="my api",
        version="1.0.0",
        tags=[
            Tag(name="public", description="This endpoint is for external users"),
            Tag(name="internal", description="This endpoint is for internal users"),
        ],
        security=[{"BearerToken": []}],
        components=Components(
            security_schemes={
                "BearerToken": SecurityScheme(
                    type="http",
                    scheme="bearer",
                )
            },
        ),
    ),
)
