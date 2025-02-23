from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict

from litestar import Litestar, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body


class FormData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    cv: UploadFile
    diploma: UploadFile


@post(path="/")
async def handle_file_upload(
    data: Annotated[FormData, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> dict[str, Any]:
    cv_content = await data.cv.read()
    diploma_content = await data.diploma.read()

    return {"cv": cv_content.decode(), "diploma": diploma_content.decode()}


app = Litestar(route_handlers=[handle_file_upload])
