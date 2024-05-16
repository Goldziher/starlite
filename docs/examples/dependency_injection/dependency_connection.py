from dependencies import CONNECTION, app

from litestar.testing import TestClient

with TestClient(app=app) as client:
    print(client.get("/").json())  # {"open": True}
    print(CONNECTION)  # {"open": False}
