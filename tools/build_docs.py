from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

REDIRECT_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <title>Page Redirection</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={target}">
        <script type="text/javascript">window.location.href = "{target}"</script>
    </head>
    <body>
        You are being redirected. If this does not work, click <a href='{target}'>this link</a>
    </body>
</html>
"""

parser = argparse.ArgumentParser()
parser.add_argument("--version", required=False)
parser.add_argument("--environment", required=False)
parser.add_argument("output")


class VersionSpec(TypedDict):
    versions: list[str]
    latest: str


@contextmanager
def checkout(branch: str) -> None:
    subprocess.run(["git", "checkout", branch], check=True)  # noqa: S603 S607
    yield
    subprocess.run(["git", "checkout", "-"], check=True)  # noqa: S603 S607


def load_version_spec() -> VersionSpec:
    versions_file = Path("docs/_static/versions.json")
    if versions_file.exists():
        return json.loads(versions_file.read_text())
    return {"versions": [], "latest": ""}


def build(output_dir: str, version: str | None, environment: str = "local") -> None:
    if version is None:
        version = importlib.metadata.version("litestar").rsplit(".")[0]
    else:
        os.environ["_LITESTAR_DOCS_BUILD_VERSION"] = version

    if environment is not None:
        os.environ["_LITESTAR_DOCS_BUILD_ENVIRONMENT"] = environment

    subprocess.run(["make", "docs"], check=True)  # noqa: S603 S607

    output_dir = Path(output_dir)
    output_dir.mkdir()
    output_dir.joinpath(".nojekyll").touch(exist_ok=True)

    version_spec = load_version_spec()
    is_latest = version == version_spec["latest"]

    docs_src_path = Path("docs/_build/html")

    output_dir.joinpath("index.html").write_text(REDIRECT_TEMPLATE.format(target="latest"))

    if is_latest:
        shutil.copytree(docs_src_path, output_dir / "latest", dirs_exist_ok=True)
    shutil.copytree(docs_src_path, output_dir / version, dirs_exist_ok=True)

    # copy existing versions into our output dir to preserve them when cleaning the branch
    with checkout("gh-pages"):
        for other_version in [*version_spec["versions"], "latest"]:
            other_version_path = Path(other_version)
            other_version_target_path = output_dir / other_version
            if other_version_path.exists() and not other_version_target_path.exists():
                shutil.copytree(other_version_path, other_version_target_path)


def main() -> None:
    args = parser.parse_args()
    build(output_dir=args.output, version=args.version, environment=args.environment)


if __name__ == "__main__":
    main()
