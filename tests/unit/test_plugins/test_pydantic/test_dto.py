from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional, cast

import pydantic as pydantic_v2
import pytest
from pydantic import v1 as pydantic_v1
from typing_extensions import Literal

from litestar import Request, post
from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO, _model_dump_json
from litestar.testing import create_test_client
from litestar.types import Empty
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from pydantic import BaseModel

    from litestar import Litestar


def test_schema_required_fields_with_pydantic_dto(
    use_experimental_dto_backend: bool, base_model: type[BaseModel]
) -> None:
    class PydanticUser(base_model):  # type: ignore[misc, valid-type]
        age: int
        name: str

    class UserDTO(PydanticDTO[PydanticUser]):
        config = DTOConfig(experimental_codegen_backend=use_experimental_dto_backend)

    @post(dto=UserDTO, return_dto=None, signature_types=[PydanticUser])
    def handler(data: PydanticUser, request: Request) -> dict:
        schema = request.app.openapi_schema
        return schema.to_schema()

    with create_test_client(handler) as client:
        data = PydanticUser(name="A", age=10)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        received = client.post(
            "/",
            content=_model_dump_json(data),
            headers=headers,
        )
        required = next(iter(received.json()["components"]["schemas"].values()))["required"]
        assert len(required) == 2


def test_field_definition_implicit_optional_default(base_model: type[BaseModel]) -> None:
    class Model(base_model):  # type: ignore[misc, valid-type]
        a: Optional[str]  # noqa: UP007

    dto_type = PydanticDTO[Model]
    field_defs = list(dto_type.generate_field_definitions(Model))
    assert len(field_defs) == 1
    assert field_defs[0].default is None


def test_detect_nested_field_pydantic_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("litestar.plugins.pydantic.dto.pydantic_v2", Empty)

    class Model(pydantic_v1.BaseModel):
        a: str

    dto_type = PydanticDTO[Model]
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(Model)) is True
    assert dto_type.detect_nested_field(FieldDefinition.from_annotation(int)) is False


def test_pydantic_field_descriptions(create_module: Callable[[str], ModuleType]) -> None:
    module = create_module(
        """
from litestar import Litestar, get
from litestar.plugins.pydantic import PydanticDTO
from litestar.dto import DTOConfig
from pydantic import BaseModel, Field
from typing_extensions import Annotated

class User(BaseModel):
    id: Annotated[
        int,
        Field(description="This is a test (id description).", gt=1),
    ]

class DataCollectionDTO(PydanticDTO[User]):
    config = DTOConfig(rename_strategy="camel")

@get("/user", return_dto=DataCollectionDTO, sync_to_thread=False)
def get_user() -> User:
    return User(id=user_id)

app = Litestar(route_handlers=[get_user])
        """
    )
    app = cast("Litestar", module.app)
    schema = app.openapi_schema
    assert schema.components.schemas is not None
    component_schema = schema.components.schemas["GetUserUserResponseBody"]
    assert component_schema.properties is not None
    assert component_schema.properties["id"].description == "This is a test (id description)."
    assert component_schema.properties["id"].exclusive_minimum == 1  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "model_config_option, forbid_unknown_fields_default, expected_dto_config_option",
    [
        ("forbid", False, True),
        ("forbid", True, True),
        ("allow", False, False),
        ("allow", True, True),
        ("ignore", True, True),
        ("ignore", False, False),
    ],
)
def test_forbid_unknown_fields_if_forbid_extra_is_set_v1(
    use_experimental_dto_backend: bool,
    forbid_unknown_fields_default: bool,
    model_config_option: Literal["forbid", "allow", "ignore"],
    expected_dto_config_option: bool,
) -> None:
    class Model(pydantic_v1.BaseModel):
        class Config:
            extra = model_config_option

        a: str

    dto_config = DTOConfig(
        experimental_codegen_backend=use_experimental_dto_backend,
        # config set on the pydantic model should take precedence
        forbid_unknown_fields=forbid_unknown_fields_default,
    )
    dto = PydanticDTO[Annotated[Model, dto_config]]

    assert dto.config.forbid_unknown_fields is expected_dto_config_option
    # ensure the config is merged
    assert dto.config.experimental_codegen_backend is use_experimental_dto_backend


@pytest.mark.parametrize(
    "model_config_option, forbid_unknown_fields_default, expected_dto_config_option",
    [
        ("forbid", False, True),
        ("forbid", True, True),
        ("allow", False, False),
        ("allow", True, True),
        ("ignore", True, True),
        ("ignore", False, False),
    ],
)
def test_forbid_unknown_fields_if_forbid_extra_is_set_v2(
    use_experimental_dto_backend: bool,
    forbid_unknown_fields_default: bool,
    model_config_option: Literal["forbid", "allow", "ignore"],
    expected_dto_config_option: bool,
) -> None:
    class Model(pydantic_v2.BaseModel):
        a: str
        model_config = pydantic_v2.ConfigDict(extra=model_config_option)

    dto_config = DTOConfig(
        experimental_codegen_backend=use_experimental_dto_backend,
        # config set on the pydantic model should take precedence
        forbid_unknown_fields=forbid_unknown_fields_default,
    )
    dto = PydanticDTO[Annotated[Model, dto_config]]

    assert dto.config.forbid_unknown_fields is expected_dto_config_option
    # ensure the config is merged
    assert dto.config.experimental_codegen_backend is use_experimental_dto_backend
