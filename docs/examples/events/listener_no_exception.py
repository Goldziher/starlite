@listener("user_deleted")
async def send_farewell_email_handler(email: str, **kwargs) -> None:
    await send_farewell_email(email)


@listener("user_deleted")
async def notify_customer_support(reason: str, **kwargs) -> None:
    await client.post("some-url", reason)
