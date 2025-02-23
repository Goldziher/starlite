from typing import Any, Optional

import pytest
from hypothesis import given
from hypothesis import strategies as st

from litestar import HttpMethod, MediaType, Response
from litestar.exceptions import ImproperlyConfiguredException
from litestar.handlers.http_handlers import HTTPRouteHandler
from litestar.handlers.http_handlers._utils import get_default_status_code
from litestar.utils import normalize_path


def dummy_method() -> None:
    pass


@given(
    http_method=st.one_of(st.sampled_from(HttpMethod), st.lists(st.sampled_from(HttpMethod))),
    media_type=st.sampled_from(MediaType),
    include_in_schema=st.booleans(),
    response_class=st.one_of(st.just(Response)),
    response_headers=st.builds(frozenset),
    status_code=st.one_of(st.none(), st.integers(min_value=200, max_value=204)),
    path=st.one_of(st.none(), st.text()),
)
def test_route_handler_kwarg_handling(
    http_method: Any,
    media_type: MediaType,
    include_in_schema: bool,
    response_class: Optional[type[Response]],
    response_headers: Any,
    status_code: Any,
    path: Any,
) -> None:
    if not http_method:
        with pytest.raises(ImproperlyConfiguredException):
            HTTPRouteHandler(http_method=http_method, fn=dummy_method)
    else:
        result = HTTPRouteHandler(
            http_method=http_method,
            media_type=media_type,
            include_in_schema=include_in_schema,
            response_class=response_class,
            response_headers=response_headers,
            status_code=status_code,
            path=path,
            fn=dummy_method,
        )
        if isinstance(http_method, list):
            assert all(method in result.http_methods for method in http_method)
        else:
            assert http_method in result.http_methods
        assert result.media_type == media_type
        assert result.include_in_schema == include_in_schema
        assert result.response_class == response_class
        assert result.response_headers == response_headers
        if not path:
            assert result.paths == {"/"}
        else:
            assert next(iter(result.paths)) == normalize_path(path)
        assert result.status_code == status_code or get_default_status_code(http_methods=result.http_methods)
