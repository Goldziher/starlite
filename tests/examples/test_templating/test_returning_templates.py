import pytest
from docs.examples.templating.returning_templates_jinja import app as jinja_app
from docs.examples.templating.returning_templates_mako import app as mako_app
from docs.examples.templating.returning_templates_minijinja import app as minijinja_app

from litestar.testing import TestClient

apps_with_expected_responses = [
    (jinja_app, "Jinja", "Hello <strong>Jinja</strong>", "Hello <strong>Jinja</strong> using strings"),
    (mako_app, "Mako", "Hello <strong>Mako</strong>\n", "Hello <strong>Mako</strong> using strings"),
    (minijinja_app, "Minijinja", "Hello <strong>Minijinja</strong>", "Hello <strong>Minijinja</strong> using strings"),
]


@pytest.mark.parametrize("app, app_name, file_response, string_response", apps_with_expected_responses)
@pytest.mark.parametrize("template_type", ["file", "string", None])
def test_returning_templates(app, app_name, file_response, string_response, template_type):
    with TestClient(app) as client:
        response = client.get(f"/{template_type}", params={"name": app_name})
        if template_type == "file":
            assert response.text == file_response
        elif template_type == "string":
            assert response.text.strip() == string_response
        else:
            # Test the scenario where template_type is None
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal Server Error", "status_code": 500}
