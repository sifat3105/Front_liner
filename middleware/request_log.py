# middleware/request_log.py
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("django.request")

class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        return None

    def process_response(self, request, response):
        try:
            logger.info({
                "request_id": getattr(request, "request_id", None),
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
            })
        except Exception:
            # never break response on logging
            pass
        return response
