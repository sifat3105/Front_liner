from rest_framework.views import exception_handler
from .response import ApiResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return ApiResponse.error(
            message=str(exc),
            errors=response.data,
            status_code=response.status_code,
            meta={"exception": exc.__class__.__name__}
        )

    # For unknown exceptions
    return ApiResponse.error(
        message="Internal server error",
        errors={"detail": str(exc)},
        status_code=500,
        meta={"exception": exc.__class__.__name__}
    )
