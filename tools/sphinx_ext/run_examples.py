from __future__ import annotations

import importlib
import logging
import multiprocessing
import os
import re
import shlex
import socket
import subprocess
import sys
import time
from contextlib import contextmanager, redirect_stderr
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import httpx
import uvicorn
from auto_pytabs.sphinx_ext import CodeBlockOverride, LiteralIncludeOverride
from docutils.nodes import Node, admonition, literal_block, title
from docutils.parsers.rst import directives
from sphinx.addnodes import highlightlang

from litestar import Litestar

if TYPE_CHECKING:
    from sphinx.application import Sphinx


RGX_RUN = re.compile(r"# +?run:(.*)")


logger = logging.getLogger("sphinx")

ignore_missing_output = os.getenv("LITESTAR_DOCS_IGNORE_MISSING_EXAMPLE_OUTPUT", "") == "1"


class StartupError(RuntimeError):
    pass


def _load_app_from_path(path: Path) -> Litestar:
    module = importlib.import_module(str(path.with_suffix("")).replace("/", "."))
    for obj in module.__dict__.values():
        if isinstance(obj, Litestar):
            return obj
    raise RuntimeError(f"No Litestar app found in {path}")


def _get_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Bind to a free port provided by the host
        try:
            sock.bind(("localhost", 0))
        except OSError as e:
            raise StartupError("Could not find an open port") from e
        else:
            return sock.getsockname()[1]


@contextmanager
def run_app(path: Path) -> Generator[int, None, None]:
    """Run an example app from a python file.

    The first ``Litestar`` instance found in the file will be used as target to run.
    """

    port = _get_available_port()
    app = _load_app_from_path(path)

    def run() -> None:
        with redirect_stderr(Path(os.devnull).open()):
            uvicorn.run(app, port=port, access_log=False)

    count = 0
    while count < 100:
        proc = multiprocessing.Process(target=run)
        proc.start()
        try:
            for _ in range(100):
                try:
                    httpx.get(f"http://127.0.0.1:{port}", timeout=0.1)
                    break
                except httpx.TransportError:
                    time.sleep(0.1)
            else:
                raise StartupError(f"App {path} failed to come online")

            yield port
            break
        except StartupError:
            time.sleep(0.2)
            count += 1
            port = _get_available_port()
        finally:
            proc.kill()

    else:
        raise StartupError(f"App {path} failed to come online")


def extract_run_args(content: str) -> tuple[str, list[list[str]]]:
    """Extract run args from a python file.

    Return the file content stripped of the run comments and a list of argument lists
    """
    new_lines = []
    run_configs = []
    for line in content.splitlines():
        if run_stmt_match := RGX_RUN.match(line):
            run_stmt = run_stmt_match.group(1).lstrip()
            run_configs.append(shlex.split(run_stmt))
        else:
            new_lines.append(line)
    return "\n".join(new_lines), run_configs


def exec_examples(app_file: Path, run_configs: list[list[str]]) -> str:
    """Start a server with the example application, run the specified requests against it
    and return their results
    """

    results = []

    with run_app(app_file) as port:
        for run_args in run_configs:
            url_path, *options = run_args
            args = ["curl", "-s", f"http://127.0.0.1:{port}{url_path}", *options]
            clean_args = ["curl", f"http://127.0.0.1:8000{url_path}", *options]

            proc = subprocess.run(  # noqa: PLW1510
                args,  # noqa: S603
                capture_output=True,
                text=True,
            )
            stdout = proc.stdout.splitlines()
            if not stdout:
                logger.debug(proc.stderr)
                if not ignore_missing_output:
                    logger.error(f"Example: {app_file}:{args} yielded no results")
                continue

            result = "\n".join(("> " + (" ".join(clean_args)), *stdout))
            results.append(result)

    return "\n".join(results)


class LiteralInclude(LiteralIncludeOverride):
    option_spec = {**LiteralIncludeOverride.option_spec, "no-run": directives.flag}

    def run(self) -> list[Node]:
        cwd = Path.cwd()
        docs_dir = cwd / "docs"
        language = self.options.get("language")
        file_path = Path(self.env.relfn2path(self.arguments[0])[1])

        if (language != "python" and file_path.suffix != ".py") or "no-run" in self.options:
            return super().run()

        content = file_path.read_text()
        clean_content, run_args = extract_run_args(content)

        if not run_args:
            return super().run()

        tmp_file = self.env.tmp_examples_path / str(file_path.relative_to(docs_dir)).replace("/", "_")

        self.arguments[0] = f"/{tmp_file.relative_to(docs_dir)!s}"
        tmp_file.write_text(clean_content)

        nodes = super().run()

        result = exec_examples(file_path.relative_to(cwd), run_args)

        nodes.append(
            admonition(
                "",
                title("", "Run it"),
                highlightlang(
                    "",
                    literal_block("", result),
                    lang="shell",
                    force=False,
                    linenothreshold=sys.maxsize,
                ),
                literal_block("", result),
            )
        )

        return nodes


def setup(app: Sphinx) -> dict[str, bool]:
    app.add_directive("literalinclude", LiteralInclude, override=True)
    app.add_directive("code-block", CodeBlockOverride, override=True)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
