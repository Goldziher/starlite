from datetime import date, datetime
from typing import Any, Optional, Union

import pytest

from litestar import Controller, MediaType, delete, get, patch, post, put
from litestar.datastructures import ResponseHeader, State
from litestar.dto import DataclassDTO, DTOConfig, DTOData
from litestar.openapi.spec.example import Example
from litestar.params import Parameter
from tests.models import DataclassPerson, DataclassPersonFactory, DataclassPet
from tests.unit.test_openapi.utils import Gender, LuckyNumber, PetException


class PartialDataclassPersonDTO(DataclassDTO[DataclassPerson]):
    config = DTOConfig(partial=True)


def create_person_controller() -> type[Controller]:
    class PersonController(Controller):
        path = "/{service_id:int}/person"

        @get("/", sync_to_thread=False)
        def get_persons(
            self,
            # expected to be ignored
            headers: Any,
            request: Any,
            state: State,
            query: dict[str, Any],
            cookies: dict[str, Any],
            # required query parameters below
            page: int,
            name: Optional[Union[str, list[str]]],  # intentionally without default
            service_id: int,
            page_size: int = Parameter(
                query="pageSize",
                description="Page Size Description",
                title="Page Size Title",
                examples=[Example(description="example value", value=1)],
            ),
            # path parameter
            # non-required query parameters below
            from_date: Optional[Union[int, datetime, date]] = None,
            to_date: Optional[Union[int, datetime, date]] = None,
            gender: Optional[Union[Gender, list[Gender]]] = Parameter(
                examples=[Example(value=Gender.MALE), Example(value=[Gender.MALE, Gender.OTHER])]
            ),
            lucky_number: Optional[LuckyNumber] = Parameter(examples=[Example(value=LuckyNumber.SEVEN)]),
            # header parameter
            secret_header: str = Parameter(header="secret"),
            # cookie parameter
            cookie_value: int = Parameter(cookie="value"),
        ) -> list[DataclassPerson]:
            return []

        @post("/", media_type=MediaType.TEXT, sync_to_thread=False)
        def create_person(
            self, data: DataclassPerson, secret_header: str = Parameter(header="secret")
        ) -> DataclassPerson:
            return data

        @post(path="/bulk", dto=PartialDataclassPersonDTO, sync_to_thread=False)
        def bulk_create_person(
            self, data: DTOData[list[DataclassPerson]], secret_header: str = Parameter(header="secret")
        ) -> list[DataclassPerson]:
            return []

        @put(path="/bulk", sync_to_thread=False)
        def bulk_update_person(
            self, data: list[DataclassPerson], secret_header: str = Parameter(header="secret")
        ) -> list[DataclassPerson]:
            return []

        @patch(path="/bulk", dto=PartialDataclassPersonDTO, sync_to_thread=False)
        def bulk_partial_update_person(
            self, data: DTOData[list[DataclassPerson]], secret_header: str = Parameter(header="secret")
        ) -> list[DataclassPerson]:
            return []

        @get(path="/{person_id:str}", sync_to_thread=False)
        def get_person_by_id(self, person_id: str) -> DataclassPerson:
            """Description in docstring."""
            return DataclassPersonFactory.build(id=person_id)

        @patch(
            path="/{person_id:str}",
            description="Description in decorator",
            dto=PartialDataclassPersonDTO,
            sync_to_thread=False,
        )
        def partial_update_person(self, person_id: str, data: DTOData[DataclassPerson]) -> DataclassPerson:
            """Description in docstring."""
            return DataclassPersonFactory.build(id=person_id)

        @put(path="/{person_id:str}", sync_to_thread=False)
        def update_person(self, person_id: str, data: DataclassPerson) -> DataclassPerson:
            """Multiline docstring example.

            Line 3.
            """
            return data

        @delete(path="/{person_id:str}", sync_to_thread=False)
        def delete_person(self, person_id: str) -> None:
            return None

        @get(path="/dataclass", sync_to_thread=False)
        def get_person_dataclass(self) -> DataclassPerson:
            return DataclassPerson(
                first_name="Moishe", last_name="zuchmir", id="1", optional=None, complex={}, pets=None
            )

    return PersonController


def create_pet_controller() -> type[Controller]:
    class PetController(Controller):
        path = "/pet"

        @get(sync_to_thread=False)
        def pets(self) -> list[DataclassPet]:
            return []

        @get(
            path="/owner-or-pet",
            response_headers=[ResponseHeader(name="x-my-tag", value="123")],
            raises=[PetException],
            sync_to_thread=False,
        )
        def get_pets_or_owners(self) -> list[Union[DataclassPerson, DataclassPet]]:
            return []

    return PetController


@pytest.fixture
def person_controller(disable_warn_implicit_sync_to_thread: None) -> type[Controller]:
    """Fixture without a top-level mark."""
    return create_person_controller()


@pytest.fixture
def pet_controller(disable_warn_implicit_sync_to_thread: None) -> type[Controller]:
    """Fixture without a top-level mark."""
    return create_pet_controller()
