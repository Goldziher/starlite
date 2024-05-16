from flask import Flask, redirect, url_for

app = Flask(__name__)


@app.get("/")
def index():
    return "hello"


@app.get("/hello")
def hello():
    return redirect(url_for("index"))
