from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import anyio
import fastapi
from fastapi import APIRouter, Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.configuration import (
    AppSettings,
    ClientSideCacheSettings,
    DatabaseSettings,
    EnvironmentOption,
    EnvironmentSettings,
)
from app.data.database import Base
from app.data.database import async_engine as engine
from app.middleware.client_cache_middleware import ClientCacheMiddleware
from app.routers.dependencies import get_current_superuser


# -------------- database --------------
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------- application --------------
async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


def lifespan_factory(
    settings: (
        DatabaseSettings | AppSettings | ClientSideCacheSettings | EnvironmentSettings
    ),
    create_tables_on_start: bool = True,
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for a FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa: ARG001
        await set_threadpool_tokens()

        if isinstance(settings, DatabaseSettings) and create_tables_on_start:
            await create_tables()

        yield

    return lifespan


# -------------- application --------------
def create_application(
    router: APIRouter,
    settings: (
        DatabaseSettings | AppSettings | ClientSideCacheSettings | EnvironmentSettings
    ),
    **kwargs: Any,
) -> FastAPI:
    """
    Creates and configures a FastAPI application based on the
    provided settings.

    This function initializes a FastAPI application
    and configures it with various settings
    and handlers based on the type of the `settings` object provided.

    Parameters
    ----------
    router : APIRouter
        The APIRouter object containing the routes to be
        included in the FastAPI application.

    settings
        An instance representing the settings
        for configuring the FastAPI application.
        It determines the configuration applied:

        - AppSettings: Configures basic app metadata like name, description,
            contact, and license info.
        - DatabaseSettings:
            Adds event handlers for initializing database tables
                during startup.
        - ClientSideCacheSettings:
            Integrates middleware for client-side caching.
        - EnvironmentSettings:
            Conditionally sets documentation URLs and integrates custom
                routes for API documentation
          based on the environment type.

    **kwargs
        Additional keyword arguments passed directly to
            the FastAPI constructor.

    Returns
    -------
    FastAPI
        A fully configured FastAPI application instance.

    The function configures the FastAPI application with
    different features and behaviors based on the provided settings.
    It includes setting up database connections, Redis pools
    for caching, queue, and rate limiting, client-side caching,
    and customizing the API documentation
    based on the environment settings.
    """
    # --- before creating application ---
    if isinstance(settings, AppSettings):
        to_update = {
            "title": settings.APP_NAME,
            "description": settings.APP_DESCRIPTION,
            "contact": {
                "name": settings.CONTACT_NAME,
                "email": settings.CONTACT_EMAIL,
            },
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    lifespan = lifespan_factory(settings, create_tables_on_start=settings.CREATE_TABLE)

    application = FastAPI(lifespan=lifespan, **kwargs)
    application.include_router(router)

    if isinstance(settings, ClientSideCacheSettings):
        application.add_middleware(
            ClientCacheMiddleware, max_age=settings.CLIENT_CACHE_MAX_AGE
        )

    if isinstance(settings, EnvironmentSettings):
        if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
            docs_router = APIRouter()
            if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> dict[str, Any]:
                out: dict = get_openapi(
                    title=application.title,
                    version=application.version,
                    routes=application.routes,
                )
                return out

            application.include_router(docs_router)

    return application
