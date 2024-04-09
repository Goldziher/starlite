# ruff: noqa: UP006
from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, TypedDict
from unittest.mock import MagicMock

import pytest
from typing_extensions import TypeAlias

from litestar import Controller, Litestar, MediaType, Response, delete, get, post
from litestar._openapi.datastructures import OpenAPIContext
from litestar._openapi.responses import (
    ResponseFactory,
    create_error_responses,
)
from litestar._openapi.schema_generation.plugins import openapi_schema_plugins
from litestar.datastructures import Cookie, ResponseHeader
from litestar.dto import AbstractDTO
from litestar.exceptions import (
    HTTPException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.handlers import HTTPRouteHandler
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.datastructures import ResponseSpec
from litestar.openapi.spec import Example, OpenAPIHeader, OpenAPIMediaType, Reference, Schema
from litestar.openapi.spec.enums import OpenAPIType
from litestar.response import File, Redirect, Stream, Template
from litestar.response.base import T
from litestar.routes import HTTPRoute
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_307_TEMPORARY_REDIRECT,
    HTTP_400_BAD_REQUEST,
    HTTP_406_NOT_ACCEPTABLE,
)
from litestar.typing import FieldDefinition
from tests.models import DataclassPerson, DataclassPersonFactory
from tests.unit.test_openapi.utils import PetException

CreateFactoryFixture: TypeAlias = "Callable[..., ResponseFactory]"


@pytest.fixture()
def create_factory() -> CreateFactoryFixture:
    def _create_factory(route_handler: HTTPRouteHandler, generate_examples: bool = False) -> ResponseFactory:
        return ResponseFactory(
            context=OpenAPIContext(
                openapi_config=OpenAPIConfig(title="test", version="1.0.0", create_examples=generate_examples),
                plugins=openapi_schema_plugins,
            ),
            route_handler=route_handler,
        )

    return _create_factory


def get_registered_route_handler(handler: HTTPRouteHandler | type[Controller], name: str) -> HTTPRouteHandler:
    app = Litestar(route_handlers=[handler])
    return app.asgi_router.route_handler_index[name]  # type: ignore[return-value]


def test_create_responses(
    person_controller: type[Controller], pet_controller: type[Controller], create_factory: CreateFactoryFixture
) -> None:
    for route in Litestar(route_handlers=[person_controller]).routes:
        assert isinstance(route, HTTPRoute)
        for route_handler, _ in route.route_handler_map.values():
            if route_handler.resolve_include_in_schema():
                responses = create_factory(route_handler).create_responses(True)
                assert responses
                assert str(route_handler.status_code) in responses
                assert str(HTTP_400_BAD_REQUEST) in responses

    handler = get_registered_route_handler(
        pet_controller,
        "tests.unit.test_openapi.conftest.create_pet_controller.<locals>.PetController.get_pets_or_owners",
    )
    responses = create_factory(handler).create_responses(raises_validation_error=False)
    assert responses
    assert str(HTTP_400_BAD_REQUEST) not in responses
    assert str(HTTP_406_NOT_ACCEPTABLE) in responses
    assert str(HTTP_200_OK) in responses


def test_create_error_responses() -> None:
    class AlternativePetException(HTTPException):
        status_code = ValidationException.status_code

    pet_exc_response, permission_denied_exc_response, validation_exc_response = create_error_responses(
        exceptions=[
            PetException,
            PermissionDeniedException,
            AlternativePetException,
            ValidationException,
        ]
    )

    assert pet_exc_response[0] == str(PetException.status_code)
    assert pet_exc_response[1].description == HTTPStatus(PetException.status_code).description
    assert pet_exc_response[1].content
    assert pet_exc_response[1].content[MediaType.JSON]
    pet_exc_response_schema = pet_exc_response[1].content[MediaType.JSON].schema
    assert isinstance(pet_exc_response_schema, Schema)
    assert pet_exc_response_schema.examples
    assert pet_exc_response_schema.properties
    assert pet_exc_response_schema.description
    assert pet_exc_response_schema.required
    assert pet_exc_response_schema.type
    assert not pet_exc_response_schema.one_of

    assert permission_denied_exc_response[0] == str(PermissionDeniedException.status_code)
    assert (
        permission_denied_exc_response[1].description == HTTPStatus(PermissionDeniedException.status_code).description
    )
    assert permission_denied_exc_response[1].content
    assert permission_denied_exc_response[1].content[MediaType.JSON]
    schema = permission_denied_exc_response[1].content[MediaType.JSON].schema

    assert isinstance(schema, Schema)
    assert schema.examples
    assert schema.properties
    assert schema.description
    assert schema.required
    assert schema.type
    assert not schema.one_of

    assert validation_exc_response[0] == str(ValidationException.status_code)
    assert validation_exc_response[1].description == HTTPStatus(ValidationException.status_code).description
    assert validation_exc_response[1].content
    assert validation_exc_response[1].content[MediaType.JSON]

    schema = validation_exc_response[1].content[MediaType.JSON].schema
    assert isinstance(schema, Schema)
    assert schema.one_of
    assert len(schema.one_of) == 2

    for schema in schema.one_of:
        assert isinstance(schema, Schema)
        assert schema.examples
        assert schema.description
        assert schema.properties
        assert schema.required
        assert schema.type


def test_create_error_responses_with_non_http_status_code() -> None:
    class HouseNotFoundError(HTTPException):
        status_code: int = 420
        detail: str = "House not found."

    house_not_found_exc_response = next(create_error_responses(exceptions=[HouseNotFoundError]))

    assert house_not_found_exc_response[0] == str(HouseNotFoundError.status_code)
    assert house_not_found_exc_response[1].description == HouseNotFoundError.detail


def test_create_success_response_with_headers(create_factory: CreateFactoryFixture) -> None:
    @get(
        path="/test",
        response_headers=[ResponseHeader(name="special-header", value="100", description="super-duper special")],
        response_description="test",
        content_encoding="base64",
        content_media_type="image/png",
        name="test",
    )
    def handler() -> list:
        return []

    handler = get_registered_route_handler(handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert response.description == "test"

    assert response.content
    assert isinstance(handler.media_type, MediaType)
    schema = response.content[handler.media_type.value].schema
    assert isinstance(schema, Schema)
    assert schema.content_encoding == "base64"
    assert schema.content_media_type == "image/png"

    assert isinstance(response.headers, dict)
    assert isinstance(response.headers["special-header"], OpenAPIHeader)
    assert response.headers["special-header"].description == "super-duper special"
    headers_schema = response.headers["special-header"].schema
    assert isinstance(headers_schema, Schema)
    assert headers_schema.type == OpenAPIType.STRING


def test_create_success_response_with_cookies(create_factory: CreateFactoryFixture) -> None:
    @get(
        path="/test",
        response_cookies=[
            Cookie(key="first-cookie", httponly=True, samesite="strict", description="the first cookie", secure=True),
            Cookie(key="second-cookie", max_age=500, description="the second cookie"),
        ],
        name="test",
    )
    def handler() -> list:
        return []

    handler = get_registered_route_handler(handler, "test")
    response = create_factory(handler, True).create_success_response()

    assert isinstance(response.headers, dict)
    assert isinstance(response.headers["Set-Cookie"], OpenAPIHeader)
    schema = response.headers["Set-Cookie"].schema
    assert isinstance(schema, Schema)
    assert schema.to_schema() == {
        "allOf": [
            {
                "description": "the first cookie",
                "example": 'first-cookie="<string>"; HttpOnly; Path=/; SameSite=strict; Secure',
            },
            {
                "description": "the second cookie",
                "example": 'second-cookie="<string>"; Max-Age=500; Path=/; SameSite=lax',
            },
        ]
    }


def test_create_success_response_with_response_class(create_factory: CreateFactoryFixture) -> None:
    @get(path="/test", name="test")
    def handler() -> Response[DataclassPerson]:
        return Response(content=DataclassPersonFactory.build())

    handler = get_registered_route_handler(handler, "test")
    factory = create_factory(handler, True)
    response = factory.create_success_response()

    assert response.content
    reference = response.content["application/json"].schema

    assert isinstance(reference, Reference)
    assert isinstance(factory.context.schema_registry.from_reference(reference).schema, Schema)


def test_create_success_response_with_stream(create_factory: CreateFactoryFixture) -> None:
    @get(path="/test", name="test")
    def handler() -> Stream:
        return Stream(iter([]))

    handler = get_registered_route_handler(handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert response.description == "Stream Response"


def test_create_success_response_redirect(create_factory: CreateFactoryFixture) -> None:
    @get(path="/test", name="test")
    def redirect_handler() -> Redirect:
        return Redirect(path="/target")

    handler = get_registered_route_handler(redirect_handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert response.description == "Redirect Response"
    assert response.headers
    location = response.headers["location"]
    assert isinstance(location, OpenAPIHeader)
    assert isinstance(location.schema, Schema)
    assert location.schema.type == OpenAPIType.STRING
    assert location.description


def test_create_success_response_redirect_override(create_factory: CreateFactoryFixture) -> None:
    @get(path="/test", status_code=HTTP_307_TEMPORARY_REDIRECT, name="test")
    def redirect_handler() -> Redirect:
        return Redirect(path="/target")

    handler = get_registered_route_handler(redirect_handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert response.description == "Redirect Response"
    assert response.headers
    location = response.headers["location"]
    assert isinstance(location, OpenAPIHeader)
    assert isinstance(location.schema, Schema)
    assert location.schema.type == OpenAPIType.STRING
    assert location.description


def test_create_success_response_no_content_explicit_responsespec(
    create_factory: CreateFactoryFixture,
) -> None:
    @delete(
        path="/test",
        responses={HTTP_204_NO_CONTENT: ResponseSpec(None, description="Custom description")},
        name="test",
    )
    def handler() -> None:
        return None

    handler = get_registered_route_handler(handler, "test")
    factory = create_factory(handler)
    responses = factory.create_additional_responses()
    status, response = next(responses)
    assert status == "204"
    assert response.description == "Custom description"
    assert not response.content

    with pytest.raises(StopIteration):
        next(responses)


def test_create_success_response_file_data(create_factory: CreateFactoryFixture) -> None:
    @get(path="/test", name="test")
    def file_handler() -> File:
        return File(path=Path("test_responses.py"))

    handler = get_registered_route_handler(file_handler, "test")
    response = create_factory(handler, True).create_success_response()

    assert response.description == "File Download"
    assert response.headers

    assert isinstance(response.headers["content-length"], OpenAPIHeader)
    assert isinstance(response.headers["content-length"].schema, Schema)
    assert response.headers["content-length"].schema.type == OpenAPIType.STRING
    assert response.headers["content-length"].description

    assert isinstance(response.headers["last-modified"], OpenAPIHeader)
    assert isinstance(response.headers["last-modified"].schema, Schema)
    assert response.headers["last-modified"].schema.type == OpenAPIType.STRING
    assert response.headers["last-modified"].description

    assert isinstance(response.headers["etag"], OpenAPIHeader)
    assert isinstance(response.headers["etag"].schema, Schema)
    assert response.headers["etag"].schema.type == OpenAPIType.STRING
    assert response.headers["etag"].description


def test_create_success_response_template(create_factory: CreateFactoryFixture) -> None:
    @get(path="/template", name="test")
    def template_handler() -> Template:
        return Template(template_name="none")

    handler = get_registered_route_handler(template_handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert response.description == "Request fulfilled, document follows"
    assert response.content
    assert response.content[MediaType.HTML.value]


def test_create_additional_responses(create_factory: CreateFactoryFixture) -> None:
    @dataclass
    class ServerError:
        message: str

    class AuthenticationError(TypedDict):
        message: str

    class UnknownError(TypedDict):
        message: str

    @get(
        responses={
            401: ResponseSpec(data_container=AuthenticationError, description="Authentication error"),
            500: ResponseSpec(data_container=ServerError, generate_examples=False, media_type=MediaType.TEXT),
            505: ResponseSpec(data_container=UnknownError),
        }
    )
    def handler() -> DataclassPerson:
        return DataclassPersonFactory.build()

    factory = create_factory(handler)
    responses = factory.create_additional_responses()

    first_response = next(responses)
    assert first_response[0] == "401"
    assert first_response[1].description == "Authentication error"

    assert first_response[1].content
    assert isinstance(first_response[1].content["application/json"], OpenAPIMediaType)
    reference = first_response[1].content["application/json"].schema
    assert isinstance(reference, Reference)
    schema = factory.context.schema_registry.from_reference(reference).schema
    assert isinstance(schema, Schema)
    assert schema.title == "AuthenticationError"

    second_response = next(responses)
    assert second_response[0] == "500"
    assert second_response[1].description == "Additional response"

    assert second_response[1].content
    assert isinstance(second_response[1].content["text/plain"], OpenAPIMediaType)
    reference = second_response[1].content["text/plain"].schema
    assert isinstance(reference, Reference)
    schema = factory.context.schema_registry.from_reference(reference).schema
    assert isinstance(schema, Schema)
    assert schema.title == "ServerError"
    assert not schema.examples

    third_response = next(responses)
    assert third_response[0] == "505"
    assert third_response[1].description == "Additional response"

    with pytest.raises(StopIteration):
        next(responses)


def test_additional_responses_overlap_with_other_responses(create_factory: CreateFactoryFixture) -> None:
    @dataclass
    class OkResponse:
        message: str

    @get(responses={200: ResponseSpec(data_container=OkResponse, description="Overwritten response")}, name="test")
    def handler() -> DataclassPerson:
        return DataclassPersonFactory.build()

    handler = get_registered_route_handler(handler, "test")
    responses = create_factory(handler).create_responses(True)

    assert responses is not None
    assert responses["200"] is not None
    assert responses["200"].description == "Overwritten response"


def test_additional_responses_overlap_with_raises(create_factory: CreateFactoryFixture) -> None:
    @dataclass
    class ErrorResponse:
        message: str

    @get(
        raises=[ValidationException],
        responses={400: ResponseSpec(data_container=ErrorResponse, description="Overwritten response")},
        name="test",
    )
    def handler() -> DataclassPerson:
        raise ValidationException()

    handler = get_registered_route_handler(handler, "test")
    responses = create_factory(handler).create_responses(True)

    assert responses is not None
    assert responses["400"] is not None
    assert responses["400"].description == "Overwritten response"


def test_additional_responses_with_custom_examples(create_factory: CreateFactoryFixture) -> None:
    @get(responses={200: ResponseSpec(DataclassPerson, examples=[Example(value={"string": "example", "number": 1})])})
    def handler() -> DataclassPerson:
        return DataclassPersonFactory.build()

    factory = create_factory(handler)
    responses = factory.create_additional_responses()
    status_code, response = next(responses)
    assert response.content
    assert response.content["application/json"].examples == {
        "dataclassperson-example-1": Example(
            value={
                "string": "example",
                "number": 1,
            }
        ),
    }

    with pytest.raises(StopIteration):
        next(responses)


def test_create_response_for_response_subclass(create_factory: CreateFactoryFixture) -> None:
    class CustomResponse(Response[T]):
        pass

    @get(path="/test", name="test", signature_types=[CustomResponse])
    def handler() -> CustomResponse[DataclassPerson]:
        return CustomResponse(content=DataclassPersonFactory.build())

    handler = get_registered_route_handler(handler, "test")
    factory = create_factory(handler, True)
    response = factory.create_success_response()

    assert response.content
    assert isinstance(response.content["application/json"], OpenAPIMediaType)
    reference = response.content["application/json"].schema
    assert isinstance(reference, Reference)
    schema = factory.context.schema_registry.from_reference(reference).schema
    assert schema.title == "DataclassPerson"


def test_success_response_with_future_annotations(
    create_module: Callable[[str], ModuleType], create_factory: CreateFactoryFixture
) -> None:
    module = create_module(
        """
from __future__ import annotations
from litestar import get

@get(path="/test", name="test")
def handler() -> int:
    ...
"""
    )
    handler = get_registered_route_handler(module.handler, "test")
    response = create_factory(handler, True).create_success_response()
    assert next(iter(response.content.values())).schema.type == OpenAPIType.INTEGER  # type: ignore[union-attr]


def test_response_generation_with_dto(create_factory: CreateFactoryFixture) -> None:
    mock_dto = MagicMock(spec=AbstractDTO)
    mock_dto.create_openapi_schema.return_value = Schema()

    @post(path="/form-upload", return_dto=mock_dto)  # pyright: ignore
    async def handler(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    Litestar(route_handlers=[handler])

    factory = create_factory(handler)
    field_definition = FieldDefinition.from_annotation(Dict[str, Any])
    factory.create_success_response()
    mock_dto.create_openapi_schema.assert_called_once_with(
        field_definition=field_definition, handler_id=handler.handler_id, schema_creator=factory.schema_creator
    )


@pytest.mark.parametrize(
    "content_media_type, expected", ((MediaType.TEXT, MediaType.TEXT), (None, "application/octet-stream"))
)
def test_file_response_media_type(content_media_type: Any, expected: Any, create_factory: CreateFactoryFixture) -> None:
    @get("/", content_media_type=content_media_type)
    def handler() -> File:
        return File("test.txt")

    response = create_factory(handler).create_success_response()
    assert next(iter(response.content.values())).schema.content_media_type == expected  # type: ignore[union-attr]
