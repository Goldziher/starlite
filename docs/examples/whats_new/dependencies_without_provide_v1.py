async def some_dependency() -> str: ...


app = Litestar(dependencies={"some": Provide(some_dependency)})
