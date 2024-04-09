# ruff: noqa: UP006, UP007
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from os import path
from os.path import dirname, join, realpath
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional

import msgspec
import pytest
from typing_extensions import Annotated

from litestar import Request, post
from litestar.datastructures.upload_file import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from litestar.testing import create_test_client

from . import Form


@dataclass
class FormData:
    name: UploadFile
    age: UploadFile
    programmer: UploadFile


@post("/form")
async def form_handler(request: Request) -> Dict[str, Any]:
    data = await request.form()
    output = {}
    for key, value in data.items():
        if isinstance(value, UploadFile):
            content = await value.read()
            output[key] = {
                "filename": value.filename,
                "content": content.decode(),
                "content_type": value.content_type,
            }
        else:
            output[key] = value
    return output


@post("/form")
async def form_multi_item_handler(request: Request) -> DefaultDict[str, list]:
    data = await request.form()
    output = defaultdict(list)
    for key, value in data.multi_items():
        for v in value:
            if isinstance(v, UploadFile):
                content = await v.read()
                output[key].append(
                    {
                        "filename": v.filename,
                        "content": content.decode(),
                        "content_type": v.content_type,
                    }
                )
            else:
                output[key].append(v)
    return output


@post("/form")
async def form_with_headers_handler(request: Request) -> Dict[str, Any]:
    data = await request.form()
    output = {}
    for key, value in data.items():
        if isinstance(value, UploadFile):
            content = await value.read()
            output[key] = {
                "filename": value.filename,
                "content": content.decode(),
                "content_type": value.content_type,
                "headers": [[name.lower(), value] for name, value in value.headers.items()],
            }
        else:
            output[key] = value
    return output


@pytest.mark.parametrize("t_type", [FormData, Dict[str, UploadFile], List[UploadFile], UploadFile])
def test_request_body_multi_part(t_type: type) -> None:
    test_path = "/test"
    data = asdict(Form(name="Moishe Zuchmir", age=30, programmer=True, value="100"))

    @post(path=test_path, signature_namespace={"t_type": t_type})
    def test_method(data: Annotated[t_type, Body(media_type=RequestEncodingType.MULTI_PART)]) -> None:  # type: ignore[valid-type]
        assert data

    with create_test_client(test_method) as client:
        response = client.post(test_path, files={k: str(v).encode("utf-8") for k, v in data.items()})
        assert response.status_code == HTTP_201_CREATED


def test_request_body_multi_part_mixed_field_content_types() -> None:
    @dataclass()
    class MultiPartFormWithMixedFields:
        image: UploadFile
        tags: List[int]

    @post(path="/form", signature_types=[MultiPartFormWithMixedFields])
    async def test_method(data: MultiPartFormWithMixedFields = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        file_data = await data.image.read()
        assert file_data == b"data"
        assert data.tags == [1, 2, 3]

    with create_test_client(test_method) as client:
        response = client.post(
            "/form",
            files={"image": ("image.png", b"data")},
            data={
                "tags": ["1", "2", "3"],
            },
        )
        assert response.status_code == HTTP_201_CREATED


def test_multipart_request_files(tmpdir: Any) -> None:
    path1 = path.join(tmpdir, "test.txt")
    Path(path1).write_bytes(b"<file content>")

    with create_test_client(form_handler) as client, open(path1, "rb") as f:
        response = client.post("/form", files={"test": f})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


def test_multipart_request_files_with_content_type(tmpdir: Any) -> None:
    path1 = path.join(tmpdir, "test.txt")
    Path(path1).write_bytes(b"<file content>")

    with create_test_client(form_handler) as client, open(path1, "rb") as f:
        response = client.post("/form", files={"test": ("test.txt", f, "text/plain")})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


def test_multipart_request_multiple_files(tmpdir: Any) -> None:
    path1 = path.join(tmpdir, "test1.txt")
    Path(path1).write_bytes(b"<file1 content>")

    path2 = path.join(tmpdir, "test2.txt")
    Path(path2).write_bytes(b"<file2 content>")

    with create_test_client(form_handler) as client, open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post("/form", files={"test1": f1, "test2": ("test2.txt", f2, "text/plain")})
        assert response.json() == {
            "test1": {"filename": "test1.txt", "content": "<file1 content>", "content_type": "text/plain"},
            "test2": {"filename": "test2.txt", "content": "<file2 content>", "content_type": "text/plain"},
        }


def test_multipart_request_multiple_files_with_headers(tmpdir: Any) -> None:
    path1 = path.join(tmpdir, "test1.txt")
    Path(path1).write_bytes(b"<file1 content>")

    path2 = path.join(tmpdir, "test2.txt")
    Path(path2).write_bytes(b"<file2 content>")

    with create_test_client(form_with_headers_handler) as client, open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/form",
            files=[
                ("test1", (None, f1)),
                ("test2", ("test2.txt", f2, "text/plain", {"x-custom": "f2"})),
            ],
        )
        assert response.json() == {
            "test1": "<file1 content>",
            "test2": {
                "filename": "test2.txt",
                "content": "<file2 content>",
                "content_type": "text/plain",
                "headers": [["content-disposition", "form-data"], ["x-custom", "f2"], ["content-type", "text/plain"]],
            },
        }


def test_multi_items(tmpdir: Any) -> None:
    path1 = path.join(tmpdir, "test1.txt")
    Path(path1).write_bytes(b"<file1 content>")

    path2 = path.join(tmpdir, "test2.txt")
    Path(path2).write_bytes(b"<file2 content>")

    with create_test_client(form_multi_item_handler) as client, open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/form",
            data={"test1": "abc"},
            files=[("test1", f1), ("test1", ("test2.txt", f2, "text/plain"))],
        )
        assert response.json() == {
            "test1": [
                "abc",
                {"filename": "test1.txt", "content": "<file1 content>", "content_type": "text/plain"},
                {"filename": "test2.txt", "content": "<file2 content>", "content_type": "text/plain"},
            ]
        }


def test_multipart_request_mixed_files_and_data() -> None:
    with create_test_client(form_handler) as client:
        response = client.post(
            "/form",
            content=(
                # data
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b'Content-Disposition: form-data; name="field0"\r\n\r\n'
                b"value0\r\n"
                # file
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b'Content-Disposition: form-data; name="file"; filename="file.txt"\r\n'
                b"Content-Type: text/plain\r\n\r\n"
                b"<file content>\r\n"
                # data
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b'Content-Disposition: form-data; name="field1"\r\n\r\n'
                b"value1\r\n"
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"},
        )
        assert response.json() == {
            "file": {
                "filename": "file.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            },
            "field0": "value0",
            "field1": "value1",
        }


def test_multipart_request_with_charset_for_filename() -> None:
    with create_test_client(form_handler) as client:
        response = client.post(
            "/form",
            content=(
                # file
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b'Content-Disposition: form-data; name="file"; filename="\xe6\x96\x87\xe6\x9b\xb8.txt"\r\n'
                b"Content-Type: text/plain\r\n\r\n"
                b"<file content>\r\n"
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; charset=utf-8; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"},
        )
        assert response.json() == {
            "file": {
                "filename": "文書.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


def test_multipart_request_without_charset_for_filename() -> None:
    with create_test_client(form_handler) as client:
        response = client.post(
            "/form",
            content=(
                # file
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b'Content-Disposition: form-data; name="file"; filename="\xe7\x94\xbb\xe5\x83\x8f.jpg"\r\n'
                b"Content-Type: image/jpeg\r\n\r\n"
                b"<file content>\r\n"
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"},
        )
        assert response.json() == {
            "file": {
                "filename": "画像.jpg",
                "content": "<file content>",
                "content_type": "image/jpeg",
            }
        }


def test_multipart_request_with_asterisks_filename() -> None:
    with create_test_client(form_handler) as client:
        response = client.post(
            "/form",
            content=(
                # file
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
                b"Content-Disposition: form-data; name='file'; filename*=utf-8''Na%C3%AFve%20file.jpg\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                b"<file content>\r\n"
                b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"},
        )
        assert response.json() == {
            "'file'": {"filename": "Naïve file.jpg", "content": "<file content>", "content_type": "image/jpeg"}
        }


def test_multipart_request_with_encoded_value() -> None:
    with create_test_client(form_handler) as client:
        response = client.post(
            "/form",
            content=(
                b"--20b303e711c4ab8c443184ac833ab00f\r\n"
                b"Content-Disposition: form-data; "
                b'name="value"\r\n\r\n'
                b"Transf\xc3\xa9rer\r\n"
                b"--20b303e711c4ab8c443184ac833ab00f--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; charset=utf-8; boundary=20b303e711c4ab8c443184ac833ab00f"},
        )
        assert response.json() == {"value": "Transférer"}


def test_urlencoded_request_data() -> None:
    with create_test_client(form_handler) as client:
        response = client.post("/form", data={"some": "data"})
        assert response.json() == {"some": "data"}


def test_no_request_data() -> None:
    with create_test_client(form_handler) as client:
        response = client.post("/form")
        assert response.json() == {}


def test_urlencoded_percent_encoding() -> None:
    with create_test_client(form_handler) as client:
        response = client.post("/form", data={"some": "da ta"})
        assert response.json() == {"some": "da ta"}


def test_urlencoded_percent_encoding_keys() -> None:
    with create_test_client(form_handler) as client:
        response = client.post("/form", data={"so me": "data"})
        assert response.json() == {"so me": "data"}


def test_postman_multipart_form_data() -> None:
    postman_body = b'----------------------------850116600781883365617864\r\nContent-Disposition: form-data; name="attributes"; filename="test-attribute_5.tsv"\r\nContent-Type: text/tab-separated-values\r\n\r\n"Campaign ID"\t"Plate Set ID"\t"No"\n\r\n----------------------------850116600781883365617864\r\nContent-Disposition: form-data; name="fasta"; filename="test-sequence_correct_5.fasta"\r\nContent-Type: application/octet-stream\r\n\r\n>P23G01_IgG1-1411:H:Q10C3:1/1:NID18\r\nCAGGTATTGAA\r\n\r\n----------------------------850116600781883365617864--\r\n'
    postman_headers = {
        "Content-Type": "multipart/form-data; boundary=--------------------------850116600781883365617864",
        "user-agent": "PostmanRuntime/7.26.0",
        "accept": "*/*",
        "cache-control": "no-cache",
        "host": "10.0.5.13:80",
        "accept-encoding": "gzip, deflate, br",
        "connection": "keep-alive",
        "content-length": "2455",
    }

    with create_test_client(form_handler) as client:
        response = client.post("/form", content=postman_body, headers=postman_headers)
        assert response.json() == {
            "attributes": {
                "filename": "test-attribute_5.tsv",
                "content": '"Campaign ID"\t"Plate Set ID"\t"No"\n',
                "content_type": "text/tab-separated-values",
            },
            "fasta": {
                "filename": "test-sequence_correct_5.fasta",
                "content": ">P23G01_IgG1-1411:H:Q10C3:1/1:NID18\r\nCAGGTATTGAA\r\n",
                "content_type": "application/octet-stream",
            },
        }


def test_image_upload() -> None:
    @post("/", signature_types=[UploadFile])
    async def hello_world(data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        await data.read()

    with open(join(dirname(realpath(__file__)), "flower.jpeg"), "rb") as f, create_test_client(
        route_handlers=[hello_world]
    ) as client:
        data = f.read()
        response = client.post("/", files={"data": data})
        assert response.status_code == HTTP_201_CREATED


@pytest.mark.parametrize("file_count", (1, 2))
def test_upload_multiple_files(file_count: int) -> None:
    @post("/")
    async def handler(data: List[UploadFile] = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        assert len(data) == file_count

        for file in data:
            assert await file.read() == b"1"

    with create_test_client([handler]) as client:
        files_to_upload = [("file", b"1") for _ in range(file_count)]
        response = client.post("/", files=files_to_upload)

        assert response.status_code == HTTP_201_CREATED


@dataclass
class Files:
    file_list: List[UploadFile]


@pytest.mark.parametrize("file_count", (1, 2))
def test_upload_multiple_files_in_model(file_count: int) -> None:
    @post("/")
    async def handler(data: Files = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        assert len(data.file_list) == file_count

        for file in data.file_list:
            assert await file.read() == b"1"

    with create_test_client([handler]) as client:
        files_to_upload = [("file_list", b"1") for _ in range(file_count)]
        response = client.post("/", files=files_to_upload)

        assert response.status_code == HTTP_201_CREATED


def test_optional_formdata() -> None:
    @post("/", signature_types=[UploadFile])
    async def hello_world(data: Optional[UploadFile] = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        if data is not None:
            await data.read()

    with create_test_client(route_handlers=[hello_world]) as client:
        response = client.post("/")
        assert response.status_code == HTTP_201_CREATED


@pytest.mark.parametrize("limit", (1000, 100, 10))
def test_multipart_form_part_limit(limit: int) -> None:
    @post("/", signature_types=[UploadFile])
    async def hello_world(data: List[UploadFile] = Body(media_type=RequestEncodingType.MULTI_PART)) -> None:
        assert len(data) == limit

    with create_test_client(route_handlers=[hello_world], multipart_form_part_limit=limit) as client:
        data = {str(i): "a" for i in range(limit)}
        response = client.post("/", files=data)
        assert response.status_code == HTTP_201_CREATED

        data = {str(i): "a" for i in range(limit)}
        data[str(limit + 1)] = "b"
        response = client.post("/", files=data)
        assert response.status_code == HTTP_400_BAD_REQUEST


def test_multipart_form_part_limit_body_param_precedence() -> None:
    app_limit = 100
    route_limit = 10

    @post("/", signature_types=[UploadFile])
    async def hello_world(
        data: List[UploadFile] = Body(media_type=RequestEncodingType.MULTI_PART, multipart_form_part_limit=route_limit),
    ) -> None:
        assert len(data) == route_limit

    with create_test_client(route_handlers=[hello_world], multipart_form_part_limit=app_limit) as client:
        data = {str(i): "a" for i in range(route_limit)}
        response = client.post("/", files=data)
        assert response.status_code == HTTP_201_CREATED

        data = {str(i): "a" for i in range(route_limit + 1)}
        response = client.post("/", files=data)
        assert response.status_code == HTTP_400_BAD_REQUEST


@dataclass
class ProductForm:
    name: str
    int_field: int
    options: str
    optional_without_default: Optional[float]
    optional_with_default: Optional[int] = None


def test_multipart_handling_of_none_values() -> None:
    @post("/", signature_types=[ProductForm])
    def handler(
        data: Annotated[ProductForm, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> None:
        assert data

    with create_test_client(route_handlers=[handler]) as client:
        response = client.post(
            "/",
            content=(
                b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                b'Content-Disposition: form-data; name="name"\r\n'
                b"Content-Type: application/octet-stream\r\n\r\n"
                b"moishe zuchmir\r\n"
                b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                b'Content-Disposition: form-data; name="int_field"\r\n'
                b"Content-Type: application/octet-stream\r\n\r\n"
                b"1\r\n"
                b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                b'Content-Disposition: form-data; name="options"\r\n'
                b"Content-Type: application/octet-stream\r\n\r\n"
                b"[1,2,3,4]\r\n"
                b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                b'Content-Disposition: form-data; name="optional_without_default"\r\n'
                b"Content-Type: application/octet-stream\r\n\r\n\r\n"
                b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                b'Content-Disposition: form-data; name="optional_with_default"\r\n'
                b"Content-Type: application/octet-stream\r\n\r\n\r\n"
                b"--1f35df74046888ceaa62d8a534a076dd--\r\n"
            ),
            headers={"Content-Type": "multipart/form-data; boundary=1f35df74046888ceaa62d8a534a076dd"},
        )
        assert response.status_code == HTTP_201_CREATED


class AddProductFormMsgspec(msgspec.Struct):
    name: str
    amount: Annotated[int, msgspec.Meta(lt=10, ge=1)]


@pytest.mark.parametrize("form_type", [RequestEncodingType.URL_ENCODED, RequestEncodingType.MULTI_PART])
def test_multipart_and_url_encoded_behave_the_same(form_type) -> None:  # type: ignore[no-untyped-def]
    @post(path="/form", signature_namespace={"form_object": AddProductFormMsgspec, "form_type": form_type})
    async def form_(request: Request, data: Annotated[AddProductFormMsgspec, Body(media_type=form_type)]) -> int:
        assert isinstance(data.name, str)
        return data.amount

    with create_test_client(
        route_handlers=[
            form_,
        ]
    ) as client:
        if form_type == RequestEncodingType.URL_ENCODED:
            response = client.post(
                "/form",
                data={
                    "name": 1,
                    "amount": 1,
                },
            )
        else:
            response = client.post(
                "/form",
                content=(
                    b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                    b'Content-Disposition: form-data; name="name"\r\n'
                    b"Content-Type: application/octet-stream\r\n\r\n"
                    b"1\r\n"
                    b"--1f35df74046888ceaa62d8a534a076dd\r\n"
                    b'Content-Disposition: form-data; name="amount"\r\n'
                    b"Content-Type: application/octet-stream\r\n\r\n"
                    b"1\r\n"
                    b"--1f35df74046888ceaa62d8a534a076dd--\r\n"
                ),
                headers={"Content-Type": "multipart/form-data; boundary=1f35df74046888ceaa62d8a534a076dd"},
            )
        assert response.status_code == HTTP_201_CREATED
