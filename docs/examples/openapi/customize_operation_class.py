from dataclasses import dataclass, field
from typing import Optional

from litestar import Litestar, MediaType, Request, post
from litestar.exceptions import HTTPException
from litestar.openapi.spec import OpenAPIMediaType, OpenAPIType, Operation, RequestBody, Schema
from litestar.status_codes import HTTP_400_BAD_REQUEST


@dataclass
class CustomOperation(Operation):
    """Custom Operation class which includes a non-standard field which is part of an OpenAPI extension."""

    x_code_samples: Optional[list[dict[str, str]]] = field(default=None, metadata={"alias": "x-codeSamples"})

    def __post_init__(self) -> None:
        self.tags = ["ok"]
        self.description = "Requires OK, Returns OK"
        self.request_body = RequestBody(
            content={
                "text": OpenAPIMediaType(
                    schema=Schema(
                        title="Body",
                        type=OpenAPIType.STRING,
                        example="OK",
                    )
                ),
            },
            description="OK is the only accepted value",
        )
        self.x_codeSamples = [
            {"lang": "Python", "source": "import requests; requests.get('localhost/example')", "label": "Python"},
            {"lang": "cURL", "source": "curl -XGET localhost/example", "label": "curl"},
        ]


@post("/", operation_class=CustomOperation, media_type=MediaType.TEXT)
async def route(request: Request) -> str:
    """

    Returns: OK

    """

    if (await request.body()) == b"OK":
        return "OK"
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="request payload must be OK")


app = Litestar(route_handlers=[route])
