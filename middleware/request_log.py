import uuid
from django.utils.deprecation import MiddlewareMixin
from .utils.request_csv_logger import log_to_csv
from .utils.ip import get_client_ip


class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        request.client_ip = get_client_ip(request)

    def process_response(self, request, response):
        try:
            log_to_csv(
                request_id=getattr(request, "request_id", None),
                ip=getattr(request, "client_ip", None),
                method=request.method,
                path=request.path,
                status=response.status_code,
                message=response.data.get("message", None),
                user_email=request.user.email if request.user.is_authenticated else None,
            )
        except Exception:
            pass

        # SAME RESPONSE — nothing modified
        return response
