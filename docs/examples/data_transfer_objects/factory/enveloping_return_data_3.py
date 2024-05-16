from litestar import get


@get("/users", dto=UserDTO, sync_to_thread=False)
def get_users() -> WithCount[User]:
    return WithCount(
        count=1,
        data=[
            User(
                id=1,
                name="Litestar User",
                password="xyz",
                created_at=datetime.now(),
            ),
        ],
    )
