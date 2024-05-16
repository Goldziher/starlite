from flask import Flask, request

app = Flask(__name__)


@app.get("/")
def index():
    print(request.method)
