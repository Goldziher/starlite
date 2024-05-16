from litestar import Response, get


@get("/users", dto=UserDTO, sync_to_thread=False)
def get_users() -> Response[User]:
    return Response(
        content=User(
            id=1,
            name="Litestar User",
            password="xyz",
            created_at=datetime.now(),
        ),
        headers={"X-Total-Count": "1"},
    )
