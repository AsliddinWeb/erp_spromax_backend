from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def _error_response(status_code: int, message: str, details=None) -> JSONResponse:
    body = {"success": False, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTPException -> {"success": false, "message": "..."}"""
    return _error_response(exc.status_code, str(exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation xatosi -> aniq maydon xatolari bilan"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})

    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Kiritilgan ma'lumotlar noto'g'ri",
        details=errors,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Kutilmagan xatoliklar — debug rejimida to'liq stack, productionda yashirilgan"""
    import os
    from app.config import settings

    if settings.DEBUG:
        import traceback
        detail = traceback.format_exc()
    else:
        detail = None

    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Ichki server xatoligi yuz berdi",
        details=detail,
    )
