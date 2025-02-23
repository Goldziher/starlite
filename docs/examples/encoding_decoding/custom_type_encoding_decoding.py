from typing import Any

from msgspec import Struct

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


def tenant_user_type_predicate(type: type) -> bool:
    return type is TenantUser


def tenant_user_enc_hook(u: TenantUser) -> Any:
    return u.to_combined_str()


def tenant_user_dec_hook(tenant_user_id_str: str) -> TenantUser:
    return TenantUser.from_string(tenant_user_id_str)


def general_dec_hook(type: type, obj: Any) -> Any:
    if tenant_user_type_predicate(type):
        return tenant_user_dec_hook(obj)

    raise NotImplementedError(f"Encountered unknown type during decoding: {type!s}")


class UserAsset(Struct):
    user: TenantUser
    name: str


@post("/asset", sync_to_thread=False)
def create_asset(
    data: UserAsset,
) -> UserAsset:
    assert isinstance(data.user, TenantUser)
    return data


app = Litestar(
    [create_asset],
    type_encoders={TenantUser: tenant_user_enc_hook},  # tell litestar how to encode TenantUser
    type_decoders=[(tenant_user_type_predicate, general_dec_hook)],  # tell litestar how to decode TenantUser
)

# run: /asset -X POST -H "Content-Type: application/json" -d '{"name":"SomeAsset","user":"TenantA_Somebody"}'
