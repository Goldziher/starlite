from flask import Flask

app = Flask(__name__)


@app.get("/")
def index():
    return "not found", 404
