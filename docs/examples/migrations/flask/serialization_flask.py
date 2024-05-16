from flask import Flask, Response

app = Flask(__name__)


@app.get("/json")
def get_json():
    return {"hello": "world"}


@app.get("/text")
def get_text():
    return "hello, world!"


@app.get("/html")
def get_html():
    return Response("<strong>hello, world</strong>", mimetype="text/html")
