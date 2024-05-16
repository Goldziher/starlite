from fastapi import Depends, FastAPI, Request


async def authenticate(request: Request) -> None: ...


app = FastAPI()


@app.get("/", dependencies=[Depends(authenticate)])
async def index() -> dict[str, str]: ...
