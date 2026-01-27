from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback
from typing import Union

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled exceptions and return structured JSON.
    Prevents raw 500 Internal Server Error text responses.
    """
    logger.error(f"❌ Global Exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc) if "production" not in str(logging.getLogger().level) else "An unexpected error occurred. Please try again.",
            "path": request.url.path
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors (422) to keep response format consistent.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": exc.errors(),
            "path": request.url.path
        }
    )
