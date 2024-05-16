from pathlib import Path

from litestar import Litestar, get


@get("/user/{username:str}")
def show_user_profile(username: str) -> str:
    return f"User {username}"


@get("/post/{post_id:int}")
def show_post(post_id: int) -> str:
    return f"Post {post_id}"


@get("/path/{subpath:path}")
def show_subpath(subpath: Path) -> str:
    return f"Subpath {subpath}"


app = Litestar([show_user_profile, show_post, show_subpath])
