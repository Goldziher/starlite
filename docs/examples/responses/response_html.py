from litestar import MediaType, get


@get(path="/page", media_type=MediaType.HTML)
def health_check() -> str:
    return """
    <html>
        <body>
            <div>
                <span>Hello World!</span>
            </div>
        </body>
    </html>
    """
