from pathlib import Path

from litestar import get
from litestar.response import File


@get(path="/file-download")
def handle_file_download() -> File:
    return File(
        path=Path(Path(__file__).resolve().parent, "report").with_suffix(".pdf"),
        filename="report.pdf",
    )
