from flask import Flask, make_response

app = Flask(__name__)


@app.get("/")
def index():
    response = make_response("hello")
    response.set_cookie("my-cookie", "cookie-value")
    response.headers["my-header"] = "header-value"
    return response
