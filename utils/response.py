import uuid
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    def _base(payload, status_code):
        payload["status_code"] = status_code
        payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
        payload["request_id"] = str(uuid.uuid4())
        return Response(payload, status=status_code)
    
    @staticmethod
    def success(message="Success", data=None, status_code=status.HTTP_200_OK, meta=None):
        return Response({
            "status": "success",    
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4()),
            "data": data or {},
            "meta": meta or {}
        }, status=status_code)

    @staticmethod
    def error(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST, meta=None):
        return Response({
            "status": "error",
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4()),
            "errors": errors or {},
            "meta": meta or {}
        }, status=status_code)
