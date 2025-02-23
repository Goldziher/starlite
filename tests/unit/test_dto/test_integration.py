from __future__ import annotations

from unittest.mock import MagicMock

from litestar import Controller, Litestar, Router, post
from litestar.dto import AbstractDTO, DTOConfig
from litestar.dto._backend import DTOBackend
from litestar.testing import create_test_client

from . import Model


def test_dto_defined_on_handler(ModelDataDTO: type[AbstractDTO]) -> None:
    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(route_handlers=handler) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_controller(ModelDataDTO: type[AbstractDTO]) -> None:
    class MyController(Controller):
        dto = ModelDataDTO

        @post()
        def handler(self, data: Model) -> Model:
            assert data == Model(a=1, b="2")
            return data

    with create_test_client(route_handlers=MyController) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_router(ModelDataDTO: type[AbstractDTO]) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    router = Router(path="/", route_handlers=[handler], dto=ModelDataDTO)

    with create_test_client(route_handlers=router) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_dto_defined_on_app(ModelDataDTO: type[AbstractDTO]) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(route_handlers=handler, dto=ModelDataDTO) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_set_dto_none_disables_inherited_dto(ModelDataDTO: type[AbstractDTO]) -> None:
    @post(dto=None, signature_namespace={"dict": dict})
    def handler(data: dict[str, str]) -> dict[str, str]:
        assert data == {"hello": "world"}
        return data

    mock_dto = MagicMock(spec=ModelDataDTO)

    with create_test_client(route_handlers=handler, dto=mock_dto) as client:  # pyright:ignore
        response = client.post("/", json={"hello": "world"})
        assert response.status_code == 201
        assert response.json() == {"hello": "world"}
        mock_dto.assert_not_called()


def test_dto_and_return_dto(ModelDataDTO: type[AbstractDTO], ModelReturnDTO: type[AbstractDTO]) -> None:
    @post()
    def handler(data: Model) -> Model:
        assert data == Model(a=1, b="2")
        return data

    with create_test_client(route_handlers=handler, dto=ModelDataDTO, return_dto=ModelReturnDTO) as client:
        response = client.post("/", json={"what": "ever"})
        assert response.status_code == 201
        assert response.json() == {"a": 1, "b": "2"}


def test_enable_experimental_backend_override_in_dto_config(ModelDataDTO: type[AbstractDTO]) -> None:
    ModelDataDTO.config = DTOConfig(experimental_codegen_backend=False)

    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        return data

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["POST"]

    backend = resolved_handler.data_dto._dto_backends[resolved_handler.handler_id]["data_backend"]  # type: ignore[union-attr]
    assert isinstance(backend, DTOBackend)


def test_use_codegen_backend_by_default(ModelDataDTO: type[AbstractDTO]) -> None:
    ModelDataDTO.config = DTOConfig()

    @post(dto=ModelDataDTO, signature_types=[Model])
    def handler(data: Model) -> Model:
        return data

    app = Litestar(route_handlers=[handler])
    resolved_handler = app.route_handler_method_map["/"]["POST"]

    backend = resolved_handler.data_dto._dto_backends[resolved_handler.handler_id]["data_backend"]  # type: ignore[union-attr]
    assert isinstance(backend, DTOBackend)
