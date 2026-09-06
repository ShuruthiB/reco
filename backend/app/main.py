from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.api.routes import api, health, demo, metrics
from app.core.config import settings
from app.core.exceptions import RecoError
from app.core.logging import get_logger, setup_logging
from app.schemas.common import ErrorDetail, ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    logger.info("Starting RECO API", extra={"environment": settings.app_env})
    yield
    logger.info("Shutting down RECO API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RECO API",
        description="Payment recovery decisioning platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(ErrorResponse(
                error=ErrorDetail(
                    code="validation_error",
                    message="Request validation failed.",
                    details={"errors": exc.errors()},
                )
            )),
        )

    @app.exception_handler(RecoError)
    async def reco_error_handler(_: Request, exc: RecoError) -> JSONResponse:
        logger.warning(
            exc.message,
            extra={"code": exc.code, "status_code": exc.status_code, "details": exc.details},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="internal_error", message="An unexpected error occurred.")
            ).model_dump(),
        )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(api.router, prefix=settings.api_prefix)
    app.include_router(demo.router, prefix=settings.api_prefix)
    app.include_router(metrics.router)
    return app


app = create_app()
