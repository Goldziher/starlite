from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer, WithJsonSchema

from litestar import Litestar, post


class TenantUser:
    """Custom Type that represents a user associated to a tenant

    Parsed from / serialized to a combined tenant + user id string of the form

        TENANTPREFIX_USERID

    i.e. separated by underscore.
    """

    tenant_prefix: str
    user_id: str

    def __init__(self, tenant_prefix: str, user_id: str) -> None:
        self.tenant_prefix = tenant_prefix
        self.user_id = user_id

    @classmethod
    def from_string(cls, s: str) -> "TenantUser":
        splits = s.split("_", maxsplit=1)
        if len(splits) < 2:
            raise ValueError(
                "Could not split up tenant user id string. "
                "Expecting underscore for separation of tenant prefix and user id."
            )
        return cls(tenant_prefix=splits[0], user_id=splits[1])

    def to_combined_str(self) -> str:
        return self.tenant_prefix + "_" + self.user_id


PydAnnotatedTenantUser = Annotated[
    TenantUser,
    BeforeValidator(lambda x: TenantUser.from_string(x)),
    PlainSerializer(lambda x: x.to_combined_str(), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class UserAsset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user: PydAnnotatedTenantUser
    name: str


@post("/asset", sync_to_thread=False)
def create_asset(
    data: UserAsset,
) -> UserAsset:
    assert isinstance(data.user, TenantUser)
    return data


app = Litestar(
    [create_asset],
)

# run: /asset -X POST -H "Content-Type: application/json" -d '{"name":"SomeAsset","user":"TenantA_Somebody"}'
