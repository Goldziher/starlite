from typing import Annotated

from pydantic import BaseModel, Json, conint

from litestar import Litestar, get
from litestar.openapi.spec.example import Example
from litestar.openapi.spec.external_documentation import ExternalDocumentation
from litestar.params import Parameter


class Version(BaseModel):
    id: conint(ge=1, le=10)  # type: ignore[valid-type]
    specs: Json


VERSIONS = {1: Version(id=1, specs='{"some": "value"}')}


@get(path="/versions/{version:int}", sync_to_thread=False)
def get_product_version(
    version: Annotated[
        int,
        Parameter(
            ge=1,
            le=10,
            title="Available Product Versions",
            description="Get a specific version spec from the available specs",
            examples=[Example(value=1)],
            external_docs=ExternalDocumentation(
                url="https://mywebsite.com/documentation/product#versions",  # type: ignore[arg-type]
            ),
        ),
    ],
) -> Version:
    return VERSIONS[version]


app = Litestar(route_handlers=[get_product_version])
