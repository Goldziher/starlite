@listener("user_deleted")
async def send_farewell_email_handler(email: str) -> None:
    await send_farewell_email(email)


@listener("user_deleted")
async def notify_customer_support(reason: str) -> None:
    # do something here to send an email
    await client.post("some-url", reason)


@dataclass
class DeleteUserDTO:
    email: str
    reason: str


@post("/users")
async def delete_user_handler(data: UserDTO, request: Request) -> None:
    await user_repository.delete({"email": email})
    request.app.emit("user_deleted", email=data.email, reason="deleted")
