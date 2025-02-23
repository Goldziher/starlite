# ruff: noqa: TC004, F401
# pyright: reportUnusedImport=false
import importlib
import sys
from pathlib import Path
from typing import Union

import pytest


def purge_module(module_names: list[str], path: Union[str, Path]) -> None:
    for name in module_names:
        if name in sys.modules:
            del sys.modules[name]
    Path(importlib.util.cache_from_source(path)).unlink(missing_ok=True)  # type: ignore[arg-type]


def test_deprecated_htmx_request() -> None:
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HTMXDetails from 'litestar.contrib.htmx.request' is deprecated"
    ):
        from litestar.contrib.htmx.request import HTMXDetails

    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HTMXDetails from 'litestar.contrib.htmx.request' is deprecated"
    ):
        from litestar.contrib.htmx.request import HTMXDetails


def test_deprecated_htmx_response() -> None:
    purge_module(["litestar.contrib.htmx.response"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HTMXTemplate from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import HTMXTemplate

    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HXLocation from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import HXLocation

    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HXStopPolling from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import HXStopPolling

    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing ClientRedirect from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import ClientRedirect
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing ClientRefresh from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import ClientRefresh
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing PushUrl from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import PushUrl
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing ReplaceUrl from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import ReplaceUrl
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(DeprecationWarning, match="importing Reswap from 'litestar.contrib.htmx.response' is deprecated"):
        from litestar.contrib.htmx.response import Reswap
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing Retarget from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import Retarget
    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing TriggerEvent from 'litestar.contrib.htmx.response' is deprecated"
    ):
        from litestar.contrib.htmx.response import TriggerEvent


def test_deprecated_htmx_types() -> None:
    purge_module(["litestar.contrib.htmx.types"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing HtmxHeaderType from 'litestar.contrib.htmx.types' is deprecated"
    ):
        from litestar.contrib.htmx.types import HtmxHeaderType

    purge_module(["litestar.contrib.htmx.types"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing TriggerEventType from 'litestar.contrib.htmx.types' is deprecated"
    ):
        from litestar.contrib.htmx.types import TriggerEventType

    purge_module(["litestar.contrib.htmx.request"], __file__)
    with pytest.warns(
        DeprecationWarning, match="importing LocationType from 'litestar.contrib.htmx.types' is deprecated"
    ):
        from litestar.contrib.htmx.types import LocationType
