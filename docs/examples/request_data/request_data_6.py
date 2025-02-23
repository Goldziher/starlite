from typing import Annotated

from litestar import Litestar, MediaType, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body


@post(path="/", media_type=MediaType.TEXT)
async def handle_file_upload(
    data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> str:
    content = await data.read()
    filename = data.filename
    return f"{filename}, {content.decode()}"


app = Litestar(route_handlers=[handle_file_upload])
