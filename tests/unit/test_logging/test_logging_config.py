import importlib
import logging
import sys
import time
from collections.abc import Generator
from importlib.util import find_spec
from logging.handlers import QueueHandler
from queue import Queue
from typing import TYPE_CHECKING, Any, Optional, Union, cast
from unittest.mock import patch

import pytest
from _pytest.logging import LogCaptureHandler, _LiveLoggingNullHandler

from litestar import Request, get
from litestar.exceptions import ImproperlyConfiguredException
from litestar.logging.config import (
    LoggingConfig,
    _get_default_handlers,
    _get_default_logging_module,
    default_handlers,
    default_picologging_handlers,
)
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from tests.helpers import cleanup_logging_impl

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


@pytest.fixture(autouse=True)
def cleanup_logging() -> Generator:
    _ = pytest.importorskip("picologging")
    with cleanup_logging_impl():
        yield


def test__get_default_handlers() -> None:
    assert _get_default_handlers(logging_module="logging") == default_handlers
    assert _get_default_handlers(logging_module="picologging") == default_picologging_handlers


def test__get_default_logging_module() -> None:
    assert find_spec("picologging")  # picologging should be installed in the test environment, simply checking that
    assert _get_default_logging_module() == "picologging"
    with patch("litestar.logging.config.find_spec") as find_spec_mock:
        find_spec_mock.return_value = None
        assert _get_default_logging_module() == "logging"


@pytest.mark.parametrize(
    "logging_module, dict_config_callable, expected_called, expected_default_handlers",
    [
        ["logging", "logging.config.dictConfig", True, default_handlers],
        ["logging", "picologging.config.dictConfig", False, default_handlers],
        ["picologging", "picologging.config.dictConfig", True, default_picologging_handlers],
        ["picologging", "logging.config.dictConfig", False, default_picologging_handlers],
    ],
)
def test_correct_dict_config_called(
    logging_module: str,
    dict_config_callable: str,
    expected_called: bool,
    expected_default_handlers: dict[str, dict[str, Any]],
) -> None:
    with patch(dict_config_callable) as dict_config_mock:
        log_config = LoggingConfig(logging_module=logging_module)
        log_config.configure()
        if expected_called:
            assert dict_config_mock.called
        else:
            assert not dict_config_mock.called


@pytest.mark.parametrize(
    "picologging_exists, expected_default_handlers",
    [
        [True, default_picologging_handlers],
        [False, default_handlers],
    ],
)
def test_correct_default_handlers_set(picologging_exists: bool, expected_default_handlers: Any) -> None:
    with patch("litestar.logging.config.find_spec") as find_spec_mock:
        find_spec_mock.return_value = picologging_exists
        log_config = LoggingConfig()
        assert log_config.handlers == expected_default_handlers


@pytest.mark.parametrize(
    "logging_module, expected_handlers",
    [
        ["logging", default_handlers],
        ["picologging", default_picologging_handlers],
    ],
)
def test_correct_default_handlers_set_logging_module(logging_module: str, expected_handlers: Any) -> None:
    log_config = LoggingConfig(logging_module=logging_module)
    assert log_config.handlers == expected_handlers


@pytest.mark.parametrize(
    "logging_module, dict_config_not_called",
    [
        ["logging", "picologging.config.dictConfig"],
        ["picologging", "logging.config.dictConfig"],
    ],
)
def test_dictconfig_on_startup(logging_module: str, dict_config_not_called: str) -> None:
    with patch(f"{logging_module}.config.dictConfig") as dict_config_mock:
        with patch(dict_config_not_called) as dict_config_not_called_mock:
            test_logger = LoggingConfig(
                logging_module=logging_module,
                loggers={"app": {"level": "INFO", "handlers": ["console"]}},
            )

            with create_test_client([], on_startup=[test_logger.configure], logging_config=None):
                assert dict_config_mock.called
                assert dict_config_mock.call_count == 1
                assert dict_config_not_called_mock.call_count == 0


@pytest.mark.parametrize(
    "logging_module_str, expected_handler_class_str, expected_listener_class_str",
    [
        [
            "logging",
            "logging.handlers.QueueHandler"
            if sys.version_info >= (3, 12, 0)
            else "litestar.logging.standard.QueueListenerHandler",
            "litestar.logging.standard.LoggingQueueListener",
        ],
        [
            "picologging",
            "litestar.logging.picologging.QueueListenerHandler",
            "picologging.handlers.QueueListener",  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]
        ],
    ],
)
def test_default_queue_listener_handler(
    logging_module_str: str,
    expected_handler_class_str: Union[str, Any],
    expected_listener_class_str: str,
    capsys: "CaptureFixture[str]",
) -> None:
    logging_module = importlib.import_module(logging_module_str)
    if expected_handler_class_str == "litestar.logging.standard.QueueListenerHandler":
        from litestar.logging.standard import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "litestar.logging.picologging.QueueListenerHandler":
        from litestar.logging.picologging import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "logging.handlers.QueueHandler":
        from logging.handlers import QueueHandler as QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    else:
        expected_handler_class = importlib.import_module(expected_handler_class_str)
    if expected_listener_class_str == "litestar.logging.standard.LoggingQueueListener":
        from litestar.logging.standard import LoggingQueueListener

        expected_listener_class = LoggingQueueListener
    elif expected_listener_class_str == "picologging.handlers.QueueListener":
        from picologging.handlers import QueueListener  # pyright: ignore[reportMissingImports]

        expected_listener_class = QueueListener
    else:
        expected_listener_class = importlib.import_module(expected_listener_class_str)

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

    get_logger = LoggingConfig(
        logging_module=logging_module.__name__,
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
    assert type(logger) is logging_module.Logger

    handler = logger.handlers[0]  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]
    assert type(handler) is expected_handler_class
    assert type(handler.queue) is Queue

    assert type(handler.listener) is expected_listener_class
    assert type(handler.listener.handlers[0]) is logging_module.StreamHandler

    logger.info("Testing now!")
    assert_log(handler.queue, expected="INFO :: test_logger :: Testing now!", count=1)

    var = "test_var"
    logger.info("%s", var)
    assert_log(handler.queue, expected="INFO :: test_logger :: test_var", count=1)


def test_get_logger_without_logging_config() -> None:
    with create_test_client(logging_config=None) as client:
        with pytest.raises(
            ImproperlyConfiguredException,
            match="cannot call '.get_logger' without passing 'logging_config' to the Litestar constructor first",
        ):
            client.app.get_logger()


@pytest.mark.parametrize(
    "logging_module_str, expected_handler_class_str",
    [
        [
            "logging",
            "logging.handlers.QueueHandler"
            if sys.version_info >= (3, 12, 0)
            else "litestar.logging.standard.QueueListenerHandler",
        ],
        ["picologging", "litestar.logging.picologging.QueueListenerHandler"],
    ],
)
def test_default_loggers(logging_module_str: str, expected_handler_class_str: str) -> None:
    logging_module = importlib.import_module(logging_module_str)
    if expected_handler_class_str == "litestar.logging.standard.QueueListenerHandler":
        from litestar.logging.standard import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "litestar.logging.picologging.QueueListenerHandler":
        from litestar.logging.picologging import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "logging.handlers.QueueHandler":
        from logging.handlers import QueueHandler as QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    else:
        expected_handler_class = importlib.import_module(expected_handler_class_str)
    with create_test_client(logging_config=LoggingConfig(logging_module=logging_module_str)) as client:
        root_logger = client.app.get_logger()
        assert isinstance(root_logger, logging_module.Logger)
        assert root_logger.name == "root"
        assert type(root_logger.handlers[0]) is expected_handler_class

        litestar_logger = client.app.logger
        assert type(litestar_logger) is logging_module.Logger
        assert litestar_logger.name == "litestar"
        assert type(litestar_logger.handlers[0]) is expected_handler_class

        # same handler instance
        assert root_logger.handlers[0] is litestar_logger.handlers[0]


@pytest.mark.parametrize(
    "logging_module_str, expected_handler_class_str",
    [
        [
            "logging",
            "logging.handlers.QueueHandler"
            if sys.version_info >= (3, 12, 0)
            else "litestar.logging.standard.QueueListenerHandler",
        ],
        ["picologging", "litestar.logging.picologging.QueueListenerHandler"],
    ],
)
def test_connection_logger(logging_module_str: str, expected_handler_class_str: str) -> None:
    logging_module = importlib.import_module(logging_module_str)
    if expected_handler_class_str == "litestar.logging.standard.QueueListenerHandler":
        from litestar.logging.standard import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "litestar.logging.picologging.QueueListenerHandler":
        from litestar.logging.picologging import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "logging.handlers.QueueHandler":
        from logging.handlers import QueueHandler as QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    else:
        expected_handler_class = importlib.import_module(expected_handler_class_str)

    @get("/")
    def handler(request: Request) -> dict[str, bool]:
        return {"isinstance": isinstance(request.logger.handlers[0], expected_handler_class)}  # type: ignore[attr-defined]

    with create_test_client(
        route_handlers=[handler],
        logging_config=LoggingConfig(logging_module=logging_module.__name__),
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.json()["isinstance"]


@pytest.mark.parametrize("logging_module_str", ["logging", "picologging", None])
def test_validation(logging_module_str: Optional[str]) -> None:
    logging_module = importlib.import_module(logging_module_str) if logging_module_str else None
    if logging_module is None:
        logging_config = LoggingConfig(
            formatters={},
            handlers={},
            loggers={},
        )
    else:
        logging_config = LoggingConfig(
            logging_module=logging_module.__name__,
            formatters={},
            handlers={},
            loggers={},
        )

    expected_default_handlers = _get_default_handlers(logging_config.logging_module)

    assert logging_config.formatters["standard"]
    assert len(logging_config.formatters) == 1

    assert logging_config.handlers["queue_listener"] == expected_default_handlers["queue_listener"]
    assert logging_config.handlers["console"] == expected_default_handlers["console"]
    assert len(logging_config.handlers) == 2

    assert logging_config.loggers["litestar"]
    assert logging_config.loggers["litestar"]["handlers"] == ["queue_listener"]
    assert len(logging_config.loggers) == 1


@pytest.mark.parametrize(
    "logging_module_str, expected_handler_class_str",
    [
        [
            "logging",
            "logging.handlers.QueueHandler"
            if sys.version_info >= (3, 12, 0)
            else "litestar.logging.standard.QueueListenerHandler",
        ],
        ["picologging", "litestar.logging.picologging.QueueListenerHandler"],
    ],
)
def test_root_logger(logging_module_str: str, expected_handler_class_str: str) -> None:
    logging_module = importlib.import_module(logging_module_str)
    if expected_handler_class_str == "litestar.logging.standard.QueueListenerHandler":
        from litestar.logging.standard import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "litestar.logging.picologging.QueueListenerHandler":
        from litestar.logging.picologging import QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    elif expected_handler_class_str == "logging.handlers.QueueHandler":
        from logging.handlers import QueueHandler as QueueListenerHandler

        expected_handler_class = QueueListenerHandler
    else:
        expected_handler_class = importlib.import_module(expected_handler_class_str)

    logging_config = LoggingConfig(logging_module=logging_module.__name__)
    get_logger = logging_config.configure()
    root_logger = get_logger()
    assert root_logger.name == "root"  # type: ignore[attr-defined]
    assert isinstance(root_logger, logging_module.Logger)
    root_logger_handler = root_logger.handlers[0]  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]
    assert root_logger_handler.name == "queue_listener"
    assert isinstance(root_logger_handler, cast("Any", expected_handler_class))


@pytest.mark.parametrize("logging_module_str", ["logging", "picologging"])
def test_root_logger_no_config(logging_module_str: str) -> None:
    logging_module = importlib.import_module(logging_module_str)
    logging_config = LoggingConfig(logging_module=logging_module_str, configure_root_logger=False)
    get_logger = logging_config.configure()
    root_logger = get_logger()

    assert isinstance(root_logger, logging_module.Logger)

    handlers = root_logger.handlers  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]
    if logging_module == logging:
        # pytest automatically configures some handlers
        for handler in handlers:
            assert isinstance(handler, (_LiveLoggingNullHandler, LogCaptureHandler))
    else:
        assert len(handlers) == 0


@pytest.mark.parametrize(
    "logging_module_str, configure_root_logger, expected_root_logger_handler_class_str",
    [
        [
            "logging",
            True,
            "logging.handlers.QueueHandler"
            if sys.version_info >= (3, 12, 0)
            else "litestar.logging.standard.QueueListenerHandler",
        ],
        ["logging", False, None],
        ["picologging", True, "litestar.logging.picologging.QueueListenerHandler"],
        ["picologging", False, None],
    ],
)
def test_customizing_handler(
    logging_module_str: str,
    configure_root_logger: bool,
    expected_root_logger_handler_class_str: "Optional[str]",
    capsys: "CaptureFixture[str]",
) -> None:
    logging_module = importlib.import_module(logging_module_str)
    if expected_root_logger_handler_class_str is None:
        expected_root_logger_handler_class = None
    elif expected_root_logger_handler_class_str == "litestar.logging.standard.QueueListenerHandler":
        from litestar.logging.standard import QueueListenerHandler

        expected_root_logger_handler_class = QueueListenerHandler
    elif expected_root_logger_handler_class_str == "litestar.logging.picologging.QueueListenerHandler":
        from litestar.logging.picologging import QueueListenerHandler

        expected_root_logger_handler_class = QueueListenerHandler
    elif expected_root_logger_handler_class_str == "logging.handlers.QueueHandler":
        from logging.handlers import QueueHandler as QueueListenerHandler

        expected_root_logger_handler_class = QueueListenerHandler
    else:
        expected_root_logger_handler_class = importlib.import_module(expected_root_logger_handler_class_str)

    log_format = "%(levelname)s :: %(name)s :: %(message)s"

    logging_config = LoggingConfig(
        logging_module=logging_module.__name__,
        formatters={
            "standard": {"format": log_format},
        },
        handlers={
            "console_stdout": {
                "class": f"{logging_module.__name__}.StreamHandler",
                "stream": "ext://sys.stdout",
                "level": "DEBUG",
                "formatter": "standard",
            },
        },
        loggers={
            "test_logger": {
                "level": "DEBUG",
                "handlers": ["console_stdout"],
                "propagate": False,
            },
            "litestar": {
                "level": "DEBUG",
                "handlers": ["console_stdout"],
                "propagate": False,
            },
        },
        configure_root_logger=configure_root_logger,
    )

    # picologging seems to be broken, cannot make it log on stdout?
    # https://github.com/microsoft/picologging/issues/205
    if logging_module_str == "picologging":
        del logging_config.handlers["console_stdout"]["stream"]

    get_logger = logging_config.configure()
    root_logger = get_logger()

    if configure_root_logger is True:
        assert isinstance(root_logger, logging_module.Logger)
        assert root_logger.level == logging_module.INFO  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]

        root_logger_handler = root_logger.handlers[0]  # pyright: ignore[reportGeneralTypeIssues,reportAttributeAccessIssue]
        assert root_logger_handler.name == "queue_listener"
        assert type(root_logger_handler) is expected_root_logger_handler_class

        if type(root_logger_handler) is QueueHandler:
            formatter = root_logger_handler.listener.handlers[0].formatter  # type: ignore[attr-defined]
        else:
            formatter = root_logger_handler.formatter
        if formatter is not None:
            assert formatter._fmt == log_format
    else:
        # Root logger shouldn't be configured but pytest adds some handlers (for the standard `logging` module)
        for handler in root_logger.handlers:  # type: ignore[attr-defined]
            assert isinstance(handler, (_LiveLoggingNullHandler, LogCaptureHandler))

    def assert_logger(logger: Any) -> None:
        assert type(logger) is logging_module.Logger
        assert logger.level == logging_module.DEBUG
        assert len(logger.handlers) == 1
        assert type(logger.handlers[0]) is logging_module.StreamHandler
        assert logger.handlers[0].name == "console_stdout"
        assert logger.handlers[0].formatter._fmt == log_format

        logger.info("Hello from '%s'", logging_module.__name__)
        if logging_module_str == "picologging":
            log_output = capsys.readouterr().err.strip()
        else:
            log_output = capsys.readouterr().out.strip()
        assert log_output == f"INFO :: {logger.name} :: Hello from '{logging_module.__name__}'"

    assert_logger(get_logger("litestar"))
    assert_logger(get_logger("test_logger"))


@pytest.mark.parametrize("logging_module", ["logging", "picologging"])
def test_excluded_fields(logging_module: str) -> None:
    # according to https://docs.python.org/3/library/logging.config.html#dictionary-schema-details
    allowed_fields = {
        "version",
        "formatters",
        "filters",
        "handlers",
        "loggers",
        "root",
        "incremental",
        "disable_existing_loggers",
    }

    if logging_module == "picologging":
        allowed_fields.remove("incremental")

    with patch(f"{logging_module}.config.dictConfig") as dict_config_mock:
        LoggingConfig(logging_module=logging_module).configure()
        assert dict_config_mock.called
        for key in dict_config_mock.call_args.args[0].keys():
            assert key in allowed_fields


@pytest.mark.parametrize(
    "traceback_line_limit, expected_warning_deprecation_called",
    [
        [-1, False],
        [20, True],
    ],
)
def test_traceback_line_limit_deprecation(traceback_line_limit: int, expected_warning_deprecation_called: bool) -> None:
    with patch("litestar.logging.config.warn_deprecation") as mock_warning_deprecation:
        LoggingConfig(traceback_line_limit=traceback_line_limit)
        assert mock_warning_deprecation.called is expected_warning_deprecation_called
