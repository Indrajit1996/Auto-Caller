from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from starlette.middleware.cors import CORSMiddleware

from app.api.keystone.main import api_router as keystone_api_router
from app.api.project.main import api_router as project_api_router
from app.core.config import config
from app.core.logger import configure_logger
from app.core.scheduler import daily_midnight_trigger, scheduler
from app.jobs.expire_users import expire_users


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}" if route.tags else f"default-{route.name}"


if config.SENTRY_DSN and not config.is_local:
    sentry_sdk.init(dsn=str(config.SENTRY_DSN), enable_tracing=True)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logger()
    redis = aioredis.from_url(config.REDIS_URL)
    FastAPICache.init(
        RedisBackend(redis),
        prefix=f"{config.PROJECT_NAME}:cache",
        enable=config.CACHE_ENABLED,
    )
    scheduler.add_job(expire_users, trigger=daily_midnight_trigger)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title=config.PROJECT_NAME,
    generate_unique_id_function=custom_generate_unique_id,
    docs_url="/docs" if config.is_local else None,
    root_path=config.API_ROOT_URL,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "tagsSorter": "alpha",
        "scopesSorter": "alpha",
    },
    lifespan=lifespan,
    redirect_slashes=False,
)

# Set all CORS enabled origins
if config.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "service": config.PROJECT_NAME}


app.include_router(keystone_api_router)
app.include_router(project_api_router)
