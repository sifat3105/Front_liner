from rest_framework.views import APIView
from rest_framework import status
from .response import ApiResponse


class BaseAPIView(APIView):

    def success(self, message="Success", data=None, meta=None, status_code=status.HTTP_200_OK):
        return ApiResponse.success(
            message=message, 
            data=data,
            meta=meta,
            status_code=status_code
        )

    def error(self, message="Error", errors=None, meta=None, status_code=status.HTTP_400_BAD_REQUEST):
        return ApiResponse.error(
            message=message, 
            errors=errors,
            meta=meta,
            status_code=status_code
        )
