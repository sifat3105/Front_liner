from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .response import ApiResponse

class AutoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_data(self, request, data):
        page = self.paginate_queryset(data, request)
        return {
            "items": page,
            "pagination": {
                "count": self.page.paginator.count if hasattr(self, 'page') else len(data),
                "page": self.page.number if hasattr(self, 'page') else 1,
                "page_count": self.page.paginator.num_pages if hasattr(self, 'page') else 1,
                "page_size": self.get_page_size(request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            }
        }



class BaseAPIView(APIView):
    pagination_class = AutoPagination

    def success(self, message="Success", data=None, meta=None, cookies=None, status_code=status.HTTP_200_OK):

        paginated_data = data

        if getattr(self, "request", None) and self.request.method.upper() == "GET":
            if isinstance(data, list) :
                paginator = self.pagination_class()
                paginator.request = self.request
                paginated_data = paginator.get_paginated_data(self.request, data)

        return ApiResponse.success(
            message=message,
            data=paginated_data,
            status_code=status_code,
            meta=meta,
            cookies=cookies
        )

    def error(self, message="Error", errors=None, meta=None, status_code=status.HTTP_400_BAD_REQUEST):
        return ApiResponse.error(
            message=message,
            errors=errors,
            status_code=status_code,
            meta=meta
        )
