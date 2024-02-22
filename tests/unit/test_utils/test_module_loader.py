from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from litestar.config.compression import CompressionConfig
from litestar.utils.module_loader import import_string, module_to_os_path


def test_import_string() -> None:
    cls = import_string("litestar.config.compression.CompressionConfig")
    assert type(cls) == type(CompressionConfig)

    with pytest.raises(ImportError):
        _ = import_string("CompressionConfigNew")
        _ = import_string("litestar.config.compression.CompressionConfigNew")
        _ = import_string("imaginary_module_that_doesnt_exist.Config")  # a random nonexistent class


def test_module_path() -> None:
    the_path = module_to_os_path("litestar.config.compression")
    assert the_path.exists()

    with pytest.raises(TypeError):
        _ = module_to_os_path("litestar.config.compression.Config")
        _ = module_to_os_path("litestar.config.compression.extra.module")


def test_import_non_existing_attribute_raises() -> None:
    with pytest.raises(ImportError):
        import_string("litestar.app.some_random_string")


def test_import_string_cached(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    tmp_path.joinpath("testmodule.py").write_text("x = 'foo'")
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(tmp_path)

    assert import_string("testmodule.x") == "foo"
