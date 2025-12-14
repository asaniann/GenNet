"""
Global error handler middleware for FastAPI applications
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from shared.exceptions import GenNetException, create_error_response, InternalServerError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "type": "ValidationError",
                "message": "Request validation failed",
                "metadata": {"errors": errors}
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "type": "HTTPException",
                "message": exc.detail,
                "metadata": {}
            }
        }
    )


async def gennet_exception_handler(request: Request, exc: GenNetException):
    """Handle GenNet custom exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # Log the full traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}",
        extra={"path": request.url.path, "method": request.method}
    )
    
    # Return a generic error response (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            InternalServerError("An unexpected error occurred"),
            include_traceback=False  # Don't expose traceback in production
        )
    )


def setup_error_handlers(app):
    """
    Setup all error handlers for a FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(GenNetException, gennet_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

