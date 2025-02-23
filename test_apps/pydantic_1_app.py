import unittest

import pydantic

from litestar import post
from litestar.testing import create_test_client


class Foo(pydantic.BaseModel):
    bar: str
    baz: list[str]


@post("/")
async def handler(data: Foo) -> Foo:
    return data


class TestApp(unittest.TestCase):
    def test_app(self) -> None:
        assert pydantic.__version__.startswith("1."), pydantic.__version__

        with create_test_client([handler]) as client:
            data = {"bar": "baz", "baz": ["a", "b", "c"]}
            res = client.post("/", json=data)
            self.assertEqual(res.json(), data)
