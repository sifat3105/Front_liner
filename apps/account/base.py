from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class BaseAPIView(APIView):
    """
    Base APIView with reusable success and error response methods
    """

    def success(self, message="Success", data=None, meta=None, status_code=status.HTTP_200_OK):
        """
        Standard success response
        """
        response = {
            "success": True,
            "message": message,
            "data": data or {},
        }
        if meta is not None:
            response["meta"] = meta
        return Response(response, status=status_code)

    def error(self, message="Error", errors=None, meta=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Standard error response
        """
        response = {
            "success": False,
            "message": message,
            "errors": errors or {},
        }
        if meta is not None:
            response["meta"] = meta
        return Response(response, status=status_code)
