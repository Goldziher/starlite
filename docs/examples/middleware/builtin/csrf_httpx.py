import httpx

with httpx.Client() as client:
    get_response = client.get("http://localhost:8000/")

    # "csrftoken" is the default cookie name
    csrf = get_response.cookies["csrftoken"]

    # "x-csrftoken" is the default header name
    post_response_using_header = client.post("http://localhost:8000/1", headers={"x-csrftoken": csrf})
    assert post_response_using_header.status_code == 201

    # "_csrf_token" is the default *non* configurable form-data key
    post_response_using_form_data = client.post("http://localhost:8000/1", data={"_csrf_token": csrf})
    assert post_response_using_form_data.status_code == 201

    # despite the header being passed, this request will fail as it does not have a cookie in its session
    # note the usage of ``httpx.post`` instead of ``client.post``
    post_response_with_no_persisted_cookie = httpx.post("http://localhost:8000/1", headers={"x-csrftoken": csrf})
    assert post_response_with_no_persisted_cookie.status_code == 403
    assert "CSRF token verification failed" in post_response_with_no_persisted_cookie.text
