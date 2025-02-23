from __future__ import annotations

import os
from os.path import commonpath
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Literal

from litestar.exceptions import ImproperlyConfiguredException, NotFoundException
from litestar.file_system import BaseLocalFileSystem, FileSystemAdapter
from litestar.handlers import get, head
from litestar.response.file import ASGIFileResponse
from litestar.router import Router
from litestar.status_codes import HTTP_404_NOT_FOUND
from litestar.types import Empty, FileInfo
from litestar.utils import normalize_path

__all__ = ("create_static_files_router",)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from litestar.datastructures import CacheControlHeader
    from litestar.openapi.spec import SecurityRequirement
    from litestar.types import (
        AfterRequestHookHandler,
        AfterResponseHookHandler,
        BeforeRequestHookHandler,
        EmptyType,
        ExceptionHandlersMap,
        Guard,
        Middleware,
        PathType,
    )


def create_static_files_router(
    path: str,
    directories: Sequence[PathType],
    file_system: Any = None,
    send_as_attachment: bool = False,
    html_mode: bool = False,
    name: str = "static",
    after_request: AfterRequestHookHandler | None = None,
    after_response: AfterResponseHookHandler | None = None,
    before_request: BeforeRequestHookHandler | None = None,
    cache_control: CacheControlHeader | None = None,
    exception_handlers: ExceptionHandlersMap | None = None,
    guards: Sequence[Guard] | None = None,
    include_in_schema: bool | EmptyType = Empty,
    middleware: Sequence[Middleware] | None = None,
    opt: Mapping[str, Any] | None = None,
    security: Sequence[SecurityRequirement] | None = None,
    tags: Sequence[str] | None = None,
    router_class: type[Router] = Router,
    resolve_symlinks: bool = True,
) -> Router:
    """Create a router with handlers to serve static files.

    Args:
        path: Path to serve static files under
        directories: Directories to serve static files from
        file_system: A *file system* implementing
            :class:`~litestar.types.FileSystemProtocol`.
            `fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_ can be passed
            here as well
        send_as_attachment: Whether to send the file as an attachment
        html_mode: When in HTML:
            - Serve an ``index.html`` file from ``/``
            - Serve ``404.html`` when a file could not be found
        name: Name to pass to the generated handlers
        after_request: ``after_request`` handlers passed to the router
        after_response: ``after_response`` handlers passed to the router
        before_request: ``before_request`` handlers passed to the router
        cache_control: ``cache_control`` passed to the router
        exception_handlers: Exception handlers passed to the router
        guards: Guards  passed to the router
        include_in_schema: Include the routes / router in the OpenAPI schema
        middleware: Middlewares passed to the router
        opt: Opts passed to the router
        security: Security options passed to the router
        tags: ``tags`` passed to the router
        router_class: The class used to construct a router from
        resolve_symlinks: Resolve symlinks of ``directories``
    """

    if file_system is None:
        file_system = BaseLocalFileSystem()

    directories = tuple(os.path.normpath(Path(p).resolve() if resolve_symlinks else Path(p)) for p in directories)

    _validate_config(path=path, directories=directories, file_system=file_system)
    path = normalize_path(path)

    headers = None
    if cache_control:
        headers = {cache_control.HEADER_NAME: cache_control.to_header()}

    resolved_directories = tuple(Path(p).resolve() if resolve_symlinks else Path(p) for p in directories)
    adapter = FileSystemAdapter(file_system)

    @get("{file_path:path}", name=name)
    async def get_handler(file_path: PurePath) -> ASGIFileResponse:
        return await _handler(
            path=file_path.as_posix(),
            is_head_response=False,
            directories=resolved_directories,
            adapter=adapter,
            is_html_mode=html_mode,
            send_as_attachment=send_as_attachment,
            headers=headers,
        )

    @head("/{file_path:path}", name=f"{name}/head")
    async def head_handler(file_path: PurePath) -> ASGIFileResponse:
        return await _handler(
            path=file_path.as_posix(),
            is_head_response=True,
            directories=resolved_directories,
            adapter=adapter,
            is_html_mode=html_mode,
            send_as_attachment=send_as_attachment,
            headers=headers,
        )

    handlers = [get_handler, head_handler]

    if html_mode:

        @get("/", name=f"{name}/index")
        async def index_handler() -> ASGIFileResponse:
            return await _handler(
                path="/",
                is_head_response=False,
                directories=resolved_directories,
                adapter=adapter,
                is_html_mode=True,
                send_as_attachment=send_as_attachment,
                headers=headers,
            )

        handlers.append(index_handler)

    return router_class(
        after_request=after_request,
        after_response=after_response,
        before_request=before_request,
        cache_control=cache_control,
        exception_handlers=exception_handlers,
        guards=guards,
        include_in_schema=include_in_schema,
        middleware=middleware,
        opt=opt,
        path=path,
        route_handlers=handlers,
        security=security,
        tags=tags,
    )


async def _handler(
    *,
    path: str,
    is_head_response: bool,
    directories: tuple[Path, ...],
    send_as_attachment: bool,
    adapter: FileSystemAdapter,
    is_html_mode: bool,
    headers: dict[str, str] | None,
) -> ASGIFileResponse:
    split_path = path.split("/")
    filename = split_path[-1]
    joined_path = Path(*split_path)
    resolved_path, fs_info = await _get_fs_info(directories=directories, file_path=joined_path, adapter=adapter)
    content_disposition_type: Literal["inline", "attachment"] = "attachment" if send_as_attachment else "inline"

    if is_html_mode and fs_info and fs_info["type"] == "directory":
        filename = "index.html"
        resolved_path, fs_info = await _get_fs_info(
            directories=directories,
            file_path=Path(resolved_path or joined_path) / filename,
            adapter=adapter,
        )

    if fs_info and fs_info["type"] == "file":
        return ASGIFileResponse(
            file_path=resolved_path or joined_path,
            file_info=fs_info,
            file_system=adapter.file_system,
            filename=filename,
            content_disposition_type=content_disposition_type,
            is_head_response=is_head_response,
            headers=headers,
        )

    if is_html_mode:
        # for some reason coverage doesn't catch these two lines
        filename = "404.html"  # pragma: no cover
        resolved_path, fs_info = await _get_fs_info(  # pragma: no cover
            directories=directories,
            file_path=filename,
            adapter=adapter,
        )

        if fs_info and fs_info["type"] == "file":
            return ASGIFileResponse(
                file_path=resolved_path or joined_path,
                file_info=fs_info,
                file_system=adapter.file_system,
                filename=filename,
                status_code=HTTP_404_NOT_FOUND,
                content_disposition_type=content_disposition_type,
                is_head_response=is_head_response,
                headers=headers,
            )

    raise NotFoundException(
        f"no file or directory match the path {resolved_path or joined_path} was found"
    )  # pragma: no cover


async def _get_fs_info(
    directories: Sequence[PathType],
    file_path: PathType,
    adapter: FileSystemAdapter,
) -> tuple[Path, FileInfo] | tuple[None, None]:
    """Return the resolved path and a :class:`stat_result <os.stat_result>`"""
    for directory in directories:
        try:
            joined_path = Path(directory, file_path)
            file_info = await adapter.info(joined_path)
            normalized_file_path = os.path.normpath(joined_path)
            directory_path = str(directory)
            if (
                file_info
                and commonpath([directory_path, file_info["name"], joined_path]) == directory_path
                and os.path.commonpath([directory, normalized_file_path]) == directory_path
                and (file_info := await adapter.info(joined_path))
            ):
                return joined_path, file_info
        except FileNotFoundError:
            continue
    return None, None


def _validate_config(path: str, directories: tuple[PathType, ...], file_system: Any) -> None:
    if not path:
        raise ImproperlyConfiguredException("path must be a non-zero length string")

    if not directories or not any(bool(d) for d in directories):
        raise ImproperlyConfiguredException("directories must include at least one path")

    if "{" in path:
        raise ImproperlyConfiguredException("path parameters are not supported for static files")

    if not (callable(getattr(file_system, "info", None)) and callable(getattr(file_system, "open", None))):
        raise ImproperlyConfiguredException("file_system must adhere to the FileSystemProtocol type")
