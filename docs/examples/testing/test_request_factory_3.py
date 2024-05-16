import pytest
from my_app.guards import secret_token_guard
from my_app.secret import secret_endpoint

from litestar.exceptions import NotAuthorizedException
from litestar.testing import RequestFactory

request = RequestFactory().get("/")


def test_secret_token_guard_failure_scenario():
    copied_endpoint_handler = secret_endpoint.copy()
    copied_endpoint_handler.opt["secret"] = None
    with pytest.raises(NotAuthorizedException):
        secret_token_guard(request=request, route_handler=copied_endpoint_handler)


def test_secret_token_guard_success_scenario():
    copied_endpoint_handler = secret_endpoint.copy()
    copied_endpoint_handler.opt["secret"] = "super-secret"
    secret_token_guard(request=request, route_handler=copied_endpoint_handler)
