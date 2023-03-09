from __future__ import annotations

import ast
import importlib
import inspect
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
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import httpx
import uvicorn
from auto_pytabs.sphinx_ext import CodeBlockOverride, LiteralIncludeOverride
from docutils.nodes import Element, Node, admonition, literal_block, title
from docutils.utils import get_source_line
from sphinx.addnodes import highlightlang, pending_xref

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

from starlite import Starlite

RGX_RUN = re.compile(r"# +?run:(.*)")

AVAILABLE_PORTS = list(range(9000, 9999))


logger = logging.getLogger("sphinx")


def _load_app_from_path(path: Path) -> Starlite:
    module = importlib.import_module(str(path.with_suffix("")).replace("/", "."))
    for obj in module.__dict__.values():
        if isinstance(obj, Starlite):
            return obj
    raise RuntimeError(f"No Starlite app found in {path}")


@contextmanager
def run_app(path: Path) -> Generator[int, None, None]:
    """Run an example app from a python file.

    The first ``Starlite`` instance found in the file will be used as target to run.
    """
    while AVAILABLE_PORTS:
        port = AVAILABLE_PORTS.pop()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                break
    else:
        raise RuntimeError("Could not find an open port")

    app = _load_app_from_path(path)

    def run() -> None:
        with redirect_stderr(Path(os.devnull).open()):
            uvicorn.run(app, port=port, access_log=False)

    proc = multiprocessing.Process(target=run)
    proc.start()
    for _ in range(50):
        try:
            httpx.get(f"http://127.0.0.1:{port}", timeout=0.1)
        except httpx.TransportError:
            time.sleep(0.1)
        else:
            break
    try:
        yield port
    finally:
        proc.kill()
    AVAILABLE_PORTS.append(port)


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

            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
            )
            stdout = proc.stdout.splitlines()
            if not stdout:
                logger.error(f"Example: {app_file}:{args} yielded no results")
                continue

            result = "\n".join(line for line in ("> " + (" ".join(clean_args)), *stdout))
            results.append(result)

    return "\n".join(results)


class LiteralInclude(LiteralIncludeOverride):
    def run(self) -> list[Node]:
        cwd = Path.cwd()
        docs_dir = cwd / "docs"
        language = self.options.get("language")
        file = Path(self.env.relfn2path(self.arguments[0])[1])

        if (language != "python" and file.suffix != ".py") or self.options.get("no-run"):
            return super().run()

        content = file.read_text()
        clean_content, run_args = extract_run_args(content)

        if not run_args:
            return super().run()

        tmp_file = self.env.tmp_examples_path / str(file.relative_to(docs_dir)).replace("/", "_")

        self.arguments[0] = "/" + str(tmp_file.relative_to(docs_dir))
        tmp_file.write_text(clean_content)

        nodes = super().run()

        result = exec_examples(file.relative_to(cwd), run_args)

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


@cache
def _get_module_ast(source_file: str) -> ast.AST | ast.Module:
    return ast.parse(Path(source_file).read_text())


def _get_import_nodes(nodes: list[ast.stmt]) -> Generator[ast.Import | ast.ImportFrom, None, None]:
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
        elif isinstance(node, ast.If) and node.test.id == "TYPE_CHECKING":
            yield from _get_import_nodes(node.body)


@cache
def get_module_global_imports(module_import_path: str, reference_target_source_obj: str) -> set[str]:
    """Return a set of names that are imported globally within the containing module of ``reference_target_source_obj``,
    including imports in ``if TYPE_CHECKING`` blocks.
    """
    module = importlib.import_module(module_import_path)
    obj = getattr(module, reference_target_source_obj)
    tree = _get_module_ast(inspect.getsourcefile(obj))

    import_nodes = _get_import_nodes(tree.body)
    return {path.asname or path.name for import_node in import_nodes for path in import_node.names}


def on_warn_missing_reference(app: Sphinx, domain: str, node: Node) -> bool | None:
    ignore_refs = app.config["ignore_missing_refs"]
    if node.tagname != "pending_xref":  # type: ignore[attr-defined]
        return None

    if not hasattr(node, "attributes"):
        return None

    attributes = node.attributes  # type: ignore[attr-defined]
    target = attributes["reftarget"]

    reference_target_source_obj = attributes.get("py:class", attributes.get("py:meth", attributes.get("py:func")))

    if reference_target_source_obj:
        global_names = get_module_global_imports(attributes["py:module"], reference_target_source_obj)

        if target in global_names:
            # autodoc has issues with if TYPE_CHECKING imports, and randomly with type aliases in annotations,
            # so we ignore those errors if we can validate that such a name exists in the containing modules global
            # scope or an if TYPE_CHECKING block.
            # see: https://github.com/sphinx-doc/sphinx/issues/11225 and https://github.com/sphinx-doc/sphinx/issues/9813
            # for reference
            return True

    # for various other autodoc issues that can't be resolved automatically, we check the exact path to be able
    # to suppress specific warnings
    source_line = get_source_line(node)[0]
    source = source_line.split(" ")[-1]
    if target in ignore_refs.get(source, []):
        return True

    return None


def on_missing_reference(app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: Element):
    if not hasattr(node, "attributes"):
        return None

    attributes = node.attributes  # type: ignore[attr-defined]
    target = attributes["reftarget"]
    py_domain = env.domains["py"]

    # autodoc sometimes incorrectly resolves these types, so we try to resolve them as py:data fist and fall back to any
    new_node = py_domain.resolve_xref(env, node["refdoc"], app.builder, "data", target, node, contnode)
    if new_node is None:
        resolved_xrefs = py_domain.resolve_any_xref(env, node["refdoc"], app.builder, target, node, contnode)
        for ref in resolved_xrefs:
            if ref:
                return ref[1]
    return new_node


def on_env_before_read_docs(app: Sphinx, env: BuildEnvironment, docnames: set[str]) -> None:
    tmp_examples_path = Path.cwd() / "docs/_build/_tmp_examples"
    tmp_examples_path.mkdir(exist_ok=True, parents=True)
    env.tmp_examples_path = tmp_examples_path


def setup(app: Sphinx) -> dict[str, bool]:
    app.add_directive("literalinclude", LiteralInclude, override=True)
    app.add_directive("code-block", CodeBlockOverride, override=True)
    app.connect("env-before-read-docs", on_env_before_read_docs)
    app.connect("missing-reference", on_missing_reference)
    app.connect("warn-missing-reference", on_warn_missing_reference)
    app.add_config_value("ignore_missing_refs", default={}, rebuild=False)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
