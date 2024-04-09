from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import pydantic as pydantic_v2
    from pydantic import v1 as pydantic_v1
    from typing_extensions import TypeAlias

PydanticVersion = Literal["v1", "v2"]
BaseModelType: TypeAlias = "type[pydantic_v1.BaseModel| pydantic_v2.BaseModel]"
