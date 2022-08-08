import sys
import warnings
from datetime import datetime
from typing import Any, Callable, Dict, List, Type, cast

import pytest
from pydantic_factories import ModelFactory

from starlite import DTOFactory, ImproperlyConfiguredException
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.plugins.tortoise_orm import TortoiseORMPlugin
from tests import Person, Species, VanillaDataClassPerson
from tests.plugins.sql_alchemy_plugin import Pet
from tests.plugins.tortoise_orm import Tournament


@pytest.mark.parametrize(
    "model, exclude, field_mapping, plugins",
    [
        [Person, [], {"complex": "ultra"}, []],
        [VanillaDataClassPerson, [], {"complex": "ultra"}, []],
        [Pet, ["age"], {"species": "kind"}, [SQLAlchemyPlugin()]],
    ],
)
def test_conversion_to_model_instance(model: Any, exclude: list, field_mapping: dict, plugins: list) -> None:
    MyDTO = DTOFactory(plugins=plugins)("MyDTO", model, exclude=exclude, field_mapping=field_mapping)

    class DTOModelFactory(ModelFactory[MyDTO]):  # type: ignore
        __model__ = MyDTO
        __allow_none_optionals__ = False

    dto_instance = DTOModelFactory.build()
    model_instance = dto_instance.to_model_instance()  # type: ignore

    for key in dto_instance.__fields__:  # type: ignore
        if key not in MyDTO.dto_field_mapping:
            assert model_instance.__getattribute__(key) == dto_instance.__getattribute__(key)  # type: ignore
        else:
            original_key = MyDTO.dto_field_mapping[key]
            assert model_instance.__getattribute__(original_key) == dto_instance.__getattribute__(key)  # type: ignore


@pytest.mark.skipif(sys.version_info < (3, 9), reason="dataclasses behave differently in lower versions")
@pytest.mark.parametrize(
    "model, exclude, field_mapping, plugins",
    [
        [Person, ["id"], {"complex": "ultra"}, []],
        [VanillaDataClassPerson, ["id"], {"complex": "ultra"}, []],
        [Pet, ["age"], {"species": "kind"}, [SQLAlchemyPlugin()]],
    ],
)
def test_conversion_from_model_instance(
    model: Any, exclude: List[Any], field_mapping: Dict[str, Any], plugins: List[Any]
) -> None:
    DTO = DTOFactory(plugins=plugins)("MyDTO", model, exclude=exclude, field_mapping=field_mapping)

    if issubclass(model, (Person, VanillaDataClassPerson)):
        model_instance = model(
            first_name="moishe",
            last_name="zuchmir",
            id=1,
            optional="some-value",
            complex={"key": [{"key": "value"}]},
            pets=None,
        )
    else:
        model_instance = cast("Type[Pet]", model)(  # type: ignore[call-arg]
            id=1,
            species=Species.MONKEY,
            name="Mike",
            age=3,
            owner_id=1,
        )
    dto_instance = DTO.from_model_instance(model_instance=model_instance)
    for key in dto_instance.__fields__:
        if key not in DTO.dto_field_mapping:
            assert model_instance.__getattribute__(key) == dto_instance.__getattribute__(key)
        else:
            original_key = DTO.dto_field_mapping[key]
            assert model_instance.__getattribute__(original_key) == dto_instance.__getattribute__(key)


@pytest.mark.asyncio()
async def test_async_conversion_from_model_instance(scaffold_tortoise: Callable) -> None:
    DTO = DTOFactory(plugins=[TortoiseORMPlugin()])("TournamentDTO", Tournament)

    tournament = Tournament(name="abc", id=1, created_at=datetime.now())

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ImproperlyConfiguredException):
            DTO.from_model_instance(tournament)

    dto_instance = await DTO.from_model_instance_async(tournament)
    assert dto_instance.name == "abc"  # type: ignore
    assert dto_instance.id == 1  # type: ignore
