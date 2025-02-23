from litestar import get
from litestar.background_tasks import BackgroundTask, BackgroundTasks
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client


async def test_background_tasks_regular_execution() -> None:
    values: list[int] = []

    def extend_values(values_to_extend: list[int]) -> None:
        values.extend(values_to_extend)

    tasks = BackgroundTasks(
        [BackgroundTask(extend_values, [1, 2, 3]), BackgroundTask(extend_values, values_to_extend=[4, 5, 6])]
    )

    @get("/", background=tasks)
    def handler() -> None:
        return None

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert values == [1, 2, 3, 4, 5, 6]


async def test_background_tasks_task_group_execution() -> None:
    values: list[int] = []

    def extend_values(values_to_extend: list[int]) -> None:
        values.extend(values_to_extend)

    tasks = BackgroundTasks(
        [BackgroundTask(extend_values, [1, 2, 3]), BackgroundTask(extend_values, values_to_extend=[4, 5, 6])],
        run_in_task_group=True,
    )

    @get("/", background=tasks)
    def handler() -> None:
        return None

    with create_test_client(handler) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert set(values) == {1, 2, 3, 4, 5, 6}
