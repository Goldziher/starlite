import logging
import sys
import time
from logging.handlers import QueueHandler
from typing import TYPE_CHECKING, Any, Dict, Generator, Optional
from unittest.mock import Mock, patch

import pytest
from _pytest.logging import LogCaptureHandler, _LiveLoggingNullHandler

from litestar import Request, get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.logging.config import LoggingConfig, _get_default_handlers, default_handlers, default_picologging_handlers
from litestar.logging.picologging import QueueListenerHandler as PicologgingQueueListenerHandler
from litestar.logging.standard import QueueListenerHandler as StandardQueueListenerHandler
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from tests.helpers import cleanup_logging_impl

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


@pytest.fixture(autouse=True)
def cleanup_logging() -> Generator:
    with cleanup_logging_impl():
        yield


@pytest.mark.parametrize(
    "dict_config_class, handlers, expected_called",
    [
        ["logging.config.dictConfig", default_handlers, True],
        ["logging.config.dictConfig", default_picologging_handlers, False],
        ["picologging.config.dictConfig", default_handlers, False],
        ["picologging.config.dictConfig", default_picologging_handlers, True],
    ],
)
def test_correct_dict_config_called(
    dict_config_class: str, handlers: Dict[str, Dict[str, Any]], expected_called: bool
) -> None:
    with patch(dict_config_class) as dict_config_mock:
        log_config = LoggingConfig(handlers=handlers)
        log_config.configure()
        if expected_called:
            assert dict_config_mock.called
        else:
            assert not dict_config_mock.called


@pytest.mark.parametrize("picologging_exists", [True, False])
def test_correct_default_handlers_set(picologging_exists: bool) -> None:
    with patch("litestar.logging.config.find_spec") as find_spec_mock:
        find_spec_mock.return_value = picologging_exists
        log_config = LoggingConfig()

        if picologging_exists:
            assert log_config.handlers == default_picologging_handlers
        else:
            assert log_config.handlers == default_handlers


@pytest.mark.parametrize(
    "dict_config_class, handlers",
    [
        ["logging.config.dictConfig", default_handlers],
        ["picologging.config.dictConfig", default_picologging_handlers],
    ],
)
def test_dictconfig_startup(dict_config_class: str, handlers: Any) -> None:
    with patch(dict_config_class) as dict_config_mock:
        test_logger = LoggingConfig(
            handlers=handlers,
        )
        with create_test_client([], on_startup=[test_logger.configure]):
            assert dict_config_mock.called


def test_standard_queue_listener_logger(capsys: "CaptureFixture[str]") -> None:
    def wait_log_queue(queue: Any, sleep_time: float = 0.1, max_retries: int = 5) -> None:
        retry = 0
        while queue.qsize() > 0 and retry < max_retries:
            retry += 1
            time.sleep(sleep_time)

    def assert_log(queue: Any, expected: str, count: Optional[int] = None) -> None:
        wait_log_queue(queue)
        log_output = capsys.readouterr().err.strip()
        if count is not None:
            assert len(log_output.split("\n")) == count
        assert log_output == expected

    with patch("litestar.logging.config.find_spec") as find_spec_mock:
        find_spec_mock.return_value = False
        get_logger = LoggingConfig(
            formatters={"standard": {"format": "%(levelname)s :: %(name)s :: %(message)s"}},
            loggers={
                "test_logger": {
                    "level": "INFO",
                    "handlers": ["queue_listener"],
                    "propagate": False,
                },
            },
        ).configure()

    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)  # type: ignore[unreachable]

    handler = logger.handlers[0]  # type: ignore[unreachable]
    assert isinstance(handler, QueueHandler if sys.version_info >= (3, 12, 0) else StandardQueueListenerHandler)

    logger.info("Testing now!")
    assert_log(handler.queue, expected="INFO :: test_logger :: Testing now!", count=1)

    var = "test_var"
    logger.info("%s", var)
    assert_log(handler.queue, expected="INFO :: test_logger :: test_var", count=1)


@patch("picologging.config.dictConfig")
def test_picologging_dictconfig_when_disabled(dict_config_mock: Mock) -> None:
    test_logger = LoggingConfig(loggers={"app": {"level": "INFO", "handlers": ["console"]}}, handlers=default_handlers)
    with create_test_client([], on_startup=[test_logger.configure], logging_config=None):
        assert not dict_config_mock.called


def test_get_logger_without_logging_config() -> None:
    with create_test_client(logging_config=None) as client:
        with pytest.raises(
            ImproperlyConfiguredException,
            match="cannot call '.get_logger' without passing 'logging_config' to the Litestar constructor first",
        ):
            client.app.get_logger()


def test_get_default_logger() -> None:
    with create_test_client(logging_config=LoggingConfig(handlers=default_handlers)) as client:
        expected_handler_class = QueueHandler if sys.version_info >= (3, 12, 0) else StandardQueueListenerHandler
        assert isinstance(client.app.logger.handlers[0], expected_handler_class)
        new_logger = client.app.get_logger()
        assert isinstance(new_logger.handlers[0], expected_handler_class)


def test_get_picologging_logger() -> None:
    with create_test_client(logging_config=LoggingConfig(handlers=default_picologging_handlers)) as client:
        assert isinstance(client.app.logger.handlers[0], PicologgingQueueListenerHandler)
        new_logger = client.app.get_logger()
        assert isinstance(new_logger.handlers[0], PicologgingQueueListenerHandler)


@pytest.mark.parametrize(
    "handlers, listener",
    [
        [default_handlers, QueueHandler if sys.version_info >= (3, 12, 0) else StandardQueueListenerHandler],
        [default_picologging_handlers, PicologgingQueueListenerHandler],
    ],
)
def test_connection_logger(handlers: Any, listener: Any) -> None:
    @get("/")
    def handler(request: Request) -> Dict[str, bool]:
        return {"isinstance": isinstance(request.logger.handlers[0], listener)}  # type: ignore[attr-defined]

    with create_test_client(route_handlers=[handler], logging_config=LoggingConfig(handlers=handlers)) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.json()["isinstance"]


def test_validation() -> None:
    logging_config = LoggingConfig(handlers={}, loggers={})
    assert logging_config.handlers["queue_listener"] == _get_default_handlers()["queue_listener"]
    assert logging_config.loggers["litestar"]


@pytest.mark.parametrize(
    "handlers, listener",
    [
        [default_handlers, QueueHandler if sys.version_info >= (3, 12, 0) else StandardQueueListenerHandler],
        [default_picologging_handlers, PicologgingQueueListenerHandler],
    ],
)
def test_root_logger(handlers: Any, listener: Any) -> None:
    logging_config = LoggingConfig(handlers=handlers)
    get_logger = logging_config.configure()
    root_logger = get_logger()
    assert isinstance(root_logger.handlers[0], listener)  # type: ignore[attr-defined]


@pytest.mark.parametrize("handlers", [default_handlers, default_picologging_handlers])
def test_root_logger_no_config(handlers: Any) -> None:
    logging_config = LoggingConfig(handlers=handlers, configure_root_logger=False)
    get_logger = logging_config.configure()
    root_logger = get_logger()
    if isinstance(root_logger, logging.Logger):  # type: ignore[unreachable]
        # pytest automatically configures some handlers
        for handler in root_logger.handlers:  # type: ignore[unreachable]
            assert isinstance(handler, (_LiveLoggingNullHandler, LogCaptureHandler))
    else:
        assert len(root_logger.handlers) == 0  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "handlers, expected_handler_class",
    [
        [default_handlers, QueueHandler if sys.version_info >= (3, 12, 0) else StandardQueueListenerHandler],
        [default_picologging_handlers, PicologgingQueueListenerHandler],
    ],
)
def test_customizing_handler(handlers: Any, expected_handler_class: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    log_format = "%(levelname)s :: %(name)s :: %(message)s"
    formatters = {"standard": {"format": log_format}}
    logging_config = LoggingConfig(formatters=formatters, handlers=handlers)
    get_logger = logging_config.configure()
    root_logger = get_logger()
    root_logger_handler = root_logger.handlers[0]  # type: ignore[attr-defined]
    assert isinstance(root_logger_handler, expected_handler_class)
    if type(root_logger_handler) is QueueHandler:
        formatter = root_logger_handler.listener.handlers[0].formatter  # type: ignore[attr-defined]
    else:
        formatter = root_logger_handler.formatter
    assert formatter._fmt == log_format
