import os
import sys
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

AI_MODULE_DIR = os.path.join(ROOT_DIR, "ai-module")
if AI_MODULE_DIR not in sys.path:
    sys.path.insert(0, AI_MODULE_DIR)

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.response import api_response
from app.routes.auth import router as auth_router
from app.routes.transactions import router as transactions_router
from app.routes.account import router as account_router
from app.routes.voice import router as voice_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_file)
    logger.info(
        "Starting API service api_base_path=%s cors_origins=%s log_level=%s",
        settings.api_base_path,
        settings.cors_origins,
        settings.log_level,
    )

    app = FastAPI(title="Multilingual Voice-Enabled Banking Support System", version="0.1.0")

    origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != [""] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        started_at = time.perf_counter()
        logger.info("Request started method=%s path=%s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.exception(
                "Request failed method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "Request completed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTP exception method=%s path=%s status_code=%s detail=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=api_response(False, data={}, message=str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception method=%s path=%s error_type=%s",
            request.method,
            request.url.path,
            exc.__class__.__name__,
        )
        exc_name = exc.__class__.__name__
        exc_msg = str(exc).lower()
        if exc_name == "ServerSelectionTimeoutError" or "serverselectiontimeouterror" in exc_name.lower():
            return JSONResponse(
                status_code=503,
                content=api_response(False, data={}, message="Database unavailable. Please ensure MongoDB is running."),
            )
        if "connection refused" in exc_msg or "timed out" in exc_msg or "network is unreachable" in exc_msg:
            return JSONResponse(
                status_code=503,
                content=api_response(False, data={}, message="Database unavailable. Please ensure MongoDB is running."),
            )
        return JSONResponse(
            status_code=500,
            content=api_response(False, data={}, message="Internal server error"),
        )

    @app.get("/")
    async def health():
        logger.debug("Health check requested")
        return api_response(True, data={"service": "ok"}, message="Service is running")

    app.include_router(auth_router, prefix=settings.api_base_path)
    app.include_router(transactions_router, prefix=settings.api_base_path)
    app.include_router(account_router, prefix=settings.api_base_path)
    app.include_router(voice_router, prefix=settings.api_base_path)
    return app


app = create_app()

