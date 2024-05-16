from flask import Flask, abort

app = Flask(__name__)


@app.get("/")
def index():
    abort(400, "this did not work")
