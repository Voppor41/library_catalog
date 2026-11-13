import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from library_catalog.api.dependencies import get_openlibrary_client

from .api.v1.routers import books, health, users
from .core.config import settings
from .core.database import dispose_engine
from .core.exceptions import register_exception_handlers
from .core.logging_config import setup_logging
from .core.redis_config import close_redis_client, init_redis_client

logger = logging.getLogger(__name__)

# ========== LIFECYCLE EVENTS ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI.

    Выполняется при:
    - startup: настройка логирования
    - shutdown: закрытие подключений к БД
    """

    setup_logging()
    await init_redis_client()
    ol_client = get_openlibrary_client()
    app.state.openlibrary_client = ol_client
    logger.info("Application started")

    try:
        yield
    finally:
        # Shutdown
        await ol_client.close()
        await close_redis_client()
        await dispose_engine()
        logger.info("Application stopped")


# ========== CREATE APP ==========

app = FastAPI(
    title=settings.app_name,
    description="REST API для управления библиотечным каталогом",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - started_at
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s %.3f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
        request_id,
    )
    return response

# ========== MIDDLEWARE ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== EXCEPTION HANDLERS ==========

register_exception_handlers(app)

# ========== ROUTERS ==========

# Версия 1 API
app.include_router(
    books.router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    users.router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    health.router,
    prefix=settings.api_v1_prefix,
)

# ========== ROOT ENDPOINT ==========

@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "Welcome to Library Catalog API",
        "docs": settings.docs_url,
        "version": "1.0.0",
    }


# ========== RUN ==========

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
