from __future__ import annotations

from unittest.mock import patch

import pytest

from litestar.datastructures import UploadFile
from litestar.datastructures.multi_dicts import FormMultiDict, ImmutableMultiDict, MultiDict

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("multi_class", [MultiDict, ImmutableMultiDict])
def test_multi_to_dict(multi_class: type[MultiDict | ImmutableMultiDict]) -> None:
    multi = multi_class([("key", "value"), ("key", "value2"), ("key2", "value3")])

    assert multi.dict() == {"key": ["value", "value2"], "key2": ["value3"]}


@pytest.mark.parametrize("multi_class", [MultiDict, ImmutableMultiDict])
def test_multi_multi_items(multi_class: type[MultiDict | ImmutableMultiDict]) -> None:
    data = [("key", "value"), ("key", "value2"), ("key2", "value3")]
    multi = multi_class(data)

    assert sorted(multi.multi_items()) == sorted(data)


def test_multi_dict_as_immutable() -> None:
    data = [("key", "value"), ("key", "value2"), ("key2", "value3")]
    multi = MultiDict[str](data)  # pyright: ignore
    assert multi.immutable().dict() == ImmutableMultiDict(data).dict()


def test_immutable_multi_dict_as_mutable() -> None:
    data = [("key", "value"), ("key", "value2"), ("key2", "value3")]
    multi = ImmutableMultiDict[str](data)  # pyright: ignore
    assert multi.mutable_copy().dict() == MultiDict(data).dict()


async def test_form_multi_dict_close() -> None:
    multi = FormMultiDict(
        [
            ("foo", UploadFile(filename="foo", content_type="text/plain")),
            ("bar", UploadFile(filename="foo", content_type="text/plain")),
        ]
    )
    with patch("litestar.datastructures.multi_dicts.UploadFile.close") as mock_close:
        await multi.close()
        assert mock_close.call_count == 2
    # calls the real UploadFile.close method to clean up
    await multi.close()


@pytest.mark.parametrize("type_", [MultiDict, ImmutableMultiDict])
def test_copy(type_: type[MultiDict | ImmutableMultiDict]) -> None:
    d = type_([("foo", "bar"), ("foo", "baz")])
    copy = d.copy()
    assert set(d.multi_items()) == set(copy.multi_items())
    assert isinstance(d, type_)
