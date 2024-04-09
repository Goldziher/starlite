from __future__ import annotations

import pytest

from litestar.dto.field import DTO_FIELD_META_KEY, extract_dto_field
from litestar.exceptions import ImproperlyConfiguredException
from litestar.typing import FieldDefinition


def test_extract_dto_field_unexpected_type() -> None:
    with pytest.raises(ImproperlyConfiguredException):
        extract_dto_field(FieldDefinition.from_annotation(int), {DTO_FIELD_META_KEY: object()})
