from litestar.middleware.logging import LoggingMiddlewareConfig

logging_middleware_config = LoggingMiddlewareConfig(
    request_cookies_to_obfuscate={"my-custom-session-key"},
    response_cookies_to_obfuscate={"my-custom-session-key"},
    request_headers_to_obfuscate={"my-custom-header"},
    response_headers_to_obfuscate={"my-custom-header"},
)
