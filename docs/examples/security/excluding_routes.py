session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    # we must pass a config for a session backend.
    # all session backends are supported
    session_backend_config=ServerSideSessionConfig(),
    # exclude any URLs that should not have authentication.
    # We exclude the documentation URLs, signup and login.
    exclude=["/login", "/signup", "/schema"],
)
