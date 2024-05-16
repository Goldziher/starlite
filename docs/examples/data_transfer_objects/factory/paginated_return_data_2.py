from litestar import get
from litestar.pagination import ClassicPagination


@get("/users", dto=UserDTO, sync_to_thread=False)
def get_users() -> ClassicPagination[User]:
    return ClassicPagination(
        page_size=10,
        total_pages=1,
        current_page=1,
        items=[
            User(
                id=1,
                name="Litestar User",
                password="xyz",
                created_at=datetime.now(),
            ),
        ],
    )
