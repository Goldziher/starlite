from litestar.handlers import WebsocketRouteHandler, websocket


def test_custom_handler_class() -> None:
    class MyHandlerClass(WebsocketRouteHandler):
        pass

    @websocket("/", handler_class=MyHandlerClass)
    async def handler() -> None:
        pass

    assert isinstance(handler, MyHandlerClass)
