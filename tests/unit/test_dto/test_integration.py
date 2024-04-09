from __future__ import annotations

from typing import Dict
from unittest.mock import MagicMock

import pytest

from litestar import Controller, Litestar, Router, post
from litestar.config.app import ExperimentalFeatures
from litestar.dto import AbstractDTO, DTOConfig
from litestar.dto._backend import DTOBackend
from litestar.dto._codegen_backend import DTOCodegenBackend
from litestar.testing import create_test_client

from . import Model


@pytest.fixture()
def experimental_features(use_experimental_dto_backend: bool) -> list[ExperimentalFeatures] | None:
    if use_experimental_dto_backend:
        return [ExperimentalFeatures.DTO_CODEGEN]
    return None


def test_dto_defined_on_handler(
    ModelDataDTO: type[AbstractDTO], experimental_features: list[ExperimentalFeatures]
) -> None:
    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(route_handlers=handler, experimental_features=experimental_features) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_controller(
    ModelDataDTO: type[AbstractDTO], experimental_features: list[ExperimentalFeatures]
) -> None:
    class MyController(Controller):
        dto = ModelDataDTO

        @post()
        def handler(self, data: Model) -> Model:
            assert data == Model(a=1, b="2")
            return data

    with create_test_client(route_handlers=MyController, experimental_features=experimental_features) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_router(
    ModelDataDTO: type[AbstractDTO], experimental_features: list[ExperimentalFeatures]
) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    router = Router(path="/", route_handlers=[handler], dto=ModelDataDTO)

    with create_test_client(route_handlers=router, experimental_features=experimental_features) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_app(ModelDataDTO: type[AbstractDTO], experimental_features: list[ExperimentalFeatures]) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(
        route_handlers=handler, dto=ModelDataDTO, experimental_features=experimental_features
    ) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_set_dto_none_disables_inherited_dto(
    ModelDataDTO: type[AbstractDTO], experimental_features: list[ExperimentalFeatures]
) -> None:
    @post(dto=None, signature_namespace={"dict": Dict})
    def handler(data: dict[str, str]) -> dict[str, str]:
        assert data == {"hello": "world"}
        return data

    mock_dto = MagicMock(spec=ModelDataDTO)

    with create_test_client(
        route_handlers=handler,
        dto=mock_dto,  # pyright:ignore
        experimental_features=experimental_features,
    ) as client:
        response = client.post("/", json={"hello": "world"})
        assert response.status_code == 201
        assert response.json() == {"hello": "world"}
        mock_dto.assert_not_called()


def test_dto_and_return_dto(
    ModelDataDTO: type[AbstractDTO],
    ModelReturnDTO: type[AbstractDTO],
    experimental_features: list[ExperimentalFeatures],
) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(
        route_handlers=handler, dto=ModelDataDTO, return_dto=ModelReturnDTO, experimental_features=experimental_features
    ) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_enable_experimental_backend(ModelDataDTO: type[AbstractDTO], use_experimental_dto_backend: bool) -> None:
    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        return data

    Litestar(
        route_handlers=[handler],
        experimental_features=[ExperimentalFeatures.DTO_CODEGEN] if use_experimental_dto_backend else None,
    )

    backend = handler.resolve_data_dto()._dto_backends[handler.handler_id]["data_backend"]  # type: ignore[union-attr]
    if use_experimental_dto_backend:
        assert isinstance(backend, DTOCodegenBackend)
    else:
        assert isinstance(backend, DTOBackend)


def test_enable_experimental_backend_override_in_dto_config(ModelDataDTO: type[AbstractDTO]) -> None:
    ModelDataDTO.config = DTOConfig(experimental_codegen_backend=False)

    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        return data

    Litestar(
        route_handlers=[handler],
        experimental_features=[ExperimentalFeatures.DTO_CODEGEN],
    )

    backend = handler.resolve_data_dto()._dto_backends[handler.handler_id]["data_backend"]  # type: ignore[union-attr]
    assert isinstance(backend, DTOBackend)


def test_use_codegen_backend_by_default(ModelDataDTO: type[AbstractDTO]) -> None:
    ModelDataDTO.config = DTOConfig()

    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        return data

    Litestar(route_handlers=[handler])

    backend = handler.resolve_data_dto()._dto_backends[handler.handler_id]["data_backend"]  # type: ignore[union-attr]
    assert isinstance(backend, DTOBackend)
