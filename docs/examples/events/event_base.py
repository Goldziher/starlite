from dataclasses import dataclass

from db import user_repository

from litestar import Litestar, Request, post
from litestar.events import listener
from utils.email import send_welcome_mail


@listener("user_created")
async def send_welcome_email_handler(email: str) -> None:
    # do something here to send an email
    await send_welcome_mail(email)


@dataclass
class CreateUserDTO:
    first_name: str
    last_name: str
    email: str


@post("/users")
async def create_user_handler(data: UserDTO, request: Request) -> None:
    # do something here to create a new user
    # e.g. insert the user into a database
    await user_repository.insert(data)

    # assuming we have now inserted a user, we want to send a welcome email.
    # To do this in a none-blocking fashion, we will emit an event to a listener, which will send the email,
    # using a different async block than the one where we are returning a response.
    request.app.emit("user_created", email=data.email)


app = Litestar(route_handlers=[create_user_handler], listeners=[send_welcome_email_handler])
