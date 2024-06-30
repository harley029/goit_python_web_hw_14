from pathlib import Path
import time
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from redis import Redis
import redis.asyncio as redis
from sqlalchemy import text
from contextlib import asynccontextmanager

from ipaddress import ip_address
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db, get_redis_client
from src.routes import contacts, auth, users
from src.conf.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes the FastAPILimiter middleware with the provided Redis client.
    This middleware is used to limit the number of requests a client can make within a certain time period.

    Parameters:
        app (FastAPI): The FastAPI application instance.

    Returns:
        None

    Yields:
        None

    Raises:
        None

    This function is called during the lifespan of the FastAPI application. It initializes the FastAPILimiter middleware with the provided Redis client, which is used to limit the number of requests a client can make within a certain time period. After the initialization, it yields control back to the application.
    """
    redis_client = await redis.from_url(f"{settings.redis_url}")
    await FastAPILimiter.init(redis_client)
    try:
        yield
    finally:
        await redis_client.close()


BASE_DIR = Path(__file__).parent

templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")

app = FastAPI(lifespan=lifespan)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
    # ip_address("127.0.0.1"),
]
@app.middleware("http")
async def ban_ips(request: Request, call_next: Callable):
    """
    This middleware checks if the client's IP address is in the list of banned IPs.
    If it is, it returns a 403 Forbidden response with a message indicating that the client is banned.
    Otherwise, it calls the next middleware or route handler in the application.

    Parameters:
    request (Request): The incoming HTTP request.
    call_next (Callable): A callback function that represents the next middleware or route handler in the application.

    Returns:
    Response: If the client's IP address is not banned, the response returned by the next middleware or route handler is returned.
    If the client's IP address is banned, a JSONResponse with a 403 Forbidden status code and a message indicating that the client is banned is returned.

    Raises:
    None
    """
    ip = ip_address(request.client.host)
    if ip in banned_ips:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"}
        )
    response = await call_next(request)
    return response


app.mount("/static", StaticFiles(directory=BASE_DIR / "src" / "static"), name="static")

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    This middleware adds a header to the response with the time taken to process the request.

    Parameters:
    request (Request): The incoming HTTP request.
    call_next (Callable): A callback function that represents the next middleware or route handler in the application.

    Returns:
    Response: The response object with an additional header "X-Process-Time" containing the time taken to process the request.

    Raises:
    None
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ------ method is depricated, lifespan instead ---------------
# @app.on_event("startup")
# async def startup():
#     r = await redis.Redis(
#         host=settings.redis_host,
#         port=settings.redis_port,
#         db=0
#     )
#     await FastAPILimiter.init(r)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    This function is a route handler for the "/" endpoint. It renders the home page of the application using the Jinja2 templating engine.

    Parameters:
    - request (Request): The incoming HTTP request object.

    Returns:
    - Response: A response object containing the rendered HTML content of the "index.html" template.
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Build by PythonWeb #22 Team"}
    )


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    This function is a route handler for the "/api/healthchecker" endpoint. It checks the connection to the database and returns a success message if the connection is established.

    Parameters:
    - db (AsyncSession): A dependency representing the database session. It is obtained using the `get_db` function.

    Returns:
    - dict: A dictionary containing a message indicating that the connection to the database is established.

    Raises:
    - HTTPException: If there is an error connecting to the database, an HTTPException with a status code of 500 and a message indicating the error is raised.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Connection to database is established. Welcome to fastapi"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to database")


@app.get("/api/redis_healthchecker")
async def redis_healthchecker(
    key="test", value="test", redis_client: Redis = Depends(get_redis_client)
):
    """
    This function is a route handler for the "/api/redis_healthchecker" endpoint. It checks the connection to the Redis database and returns a success message if the connection is established.

    Parameters:
    - key (str): A string representing the key to be set in the Redis database. Default is "test".
    - value (str): A string representing the value to be set for the given key in the Redis database. Default is "test".
    - redis_client (Redis): A dependency representing the Redis client. It is obtained using the `get_redis_client` function.

    Returns:
    - dict: A dictionary containing a message indicating that the connection to the Redis database is established.

    Raises:
    - HTTPException: If there is an error connecting to the Redis database, an HTTPException with a status code of 500 and a message indicating the error is raised.
    """
    try:
        await redis_client.set(key, value, ex=5)
        value = await redis_client.get(key)
        if value is None:
            raise HTTPException(
                status_code=500, detail="Radis Database is not configured correctly"
            )
        return {"message": "Connection to Radis is established."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to Radis")
