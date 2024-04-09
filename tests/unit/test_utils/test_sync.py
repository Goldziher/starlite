from litestar.utils.sync import ensure_async_callable


async def test_function_wrapper_wraps_method_correctly() -> None:
    class MyClass:
        def __init__(self) -> None:
            self.value = 0

        def my_method(self, value: int) -> None:
            self.value = value

    instance = MyClass()

    wrapped_method = ensure_async_callable(instance.my_method)

    await wrapped_method(1)
    assert instance.value == 1

    await wrapped_method(value=10)
    assert instance.value == 10


async def test_function_wrapper_wraps_async_method_correctly() -> None:
    class MyClass:
        def __init__(self) -> None:
            self.value = 0

        async def my_method(self, value: int) -> None:
            self.value = value

    instance = MyClass()

    wrapped_method = ensure_async_callable(instance.my_method)

    await wrapped_method(1)  # type: ignore[unused-coroutine]
    assert instance.value == 1

    await wrapped_method(value=10)  # type: ignore[unused-coroutine]
    assert instance.value == 10


async def test_function_wrapper_wraps_function_correctly() -> None:
    obj = {"value": 0}

    def my_function(new_value: int) -> None:
        obj["value"] = new_value

    wrapped_function = ensure_async_callable(my_function)

    await wrapped_function(1)
    assert obj["value"] == 1

    await wrapped_function(new_value=10)
    assert obj["value"] == 10


async def test_function_wrapper_wraps_async_function_correctly() -> None:
    obj = {"value": 0}

    async def my_function(new_value: int) -> None:
        obj["value"] = new_value

    wrapped_function = ensure_async_callable(my_function)

    await wrapped_function(1)  # type: ignore[unused-coroutine]
    assert obj["value"] == 1

    await wrapped_function(new_value=10)  # type: ignore[unused-coroutine]
    assert obj["value"] == 10


async def test_function_wrapper_wraps_class_correctly() -> None:
    class MyCallable:
        value = 0

        def __call__(self, new_value: int) -> None:
            self.value = new_value

    instance = MyCallable()

    wrapped_class = ensure_async_callable(instance)

    await wrapped_class(1)
    assert instance.value == 1

    await wrapped_class(new_value=10)
    assert instance.value == 10


async def test_function_wrapper_wraps_async_class_correctly() -> None:
    class MyCallable:
        value = 0

        async def __call__(self, new_value: int) -> None:
            self.value = new_value

    instance = MyCallable()

    wrapped_class = ensure_async_callable(instance)

    await wrapped_class(1)  # type: ignore[unused-coroutine]
    assert instance.value == 1

    await wrapped_class(new_value=10)  # type: ignore[unused-coroutine]
    assert instance.value == 10
