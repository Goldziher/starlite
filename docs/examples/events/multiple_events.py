from litestar.events import listener


@listener("user_created", "password_changed")
async def send_email_handler(email: str, message: str) -> None:
    # do something here to send an email

    await send_email(email, message)
