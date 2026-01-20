from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(BaseAPIException):
    """Resource topilmadi"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestException(BaseAPIException):
    """Noto'g'ri so'rov"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(BaseAPIException):
    """Autentifikatsiya xatosi"""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(BaseAPIException):
    """Ruxsat yo'q"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(BaseAPIException):
    """Konflikt (masalan, duplicate entry)"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class InsufficientStockException(BaseAPIException):
    """Omborda mahsulot yetarli emas"""
    def __init__(self, detail: str = "Insufficient stock"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidShiftException(BaseAPIException):
    """Noto'g'ri smena ma'lumotlari"""
    def __init__(self, detail: str = "Invalid shift data"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class PermissionDeniedException(ForbiddenException):
    """Ruxsat yo'q"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail)