from rest_framework.pagination import PageNumberPagination

class AutoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_page_size(self, request):
        raw_page_size = request.query_params.get(self.page_size_query_param)

        if raw_page_size == "max":
            return self.max_page_size

        try:
            return int(raw_page_size)
        except (TypeError, ValueError):
            return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        page_size = self.get_page_size(request)

        # page_size >= max → return all data
        if page_size and page_size >= self.max_page_size:
            self.page = None
            return None

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_data(self, request, queryset_or_list):
        page = self.paginate_queryset(queryset_or_list, request)

        # No pagination (ALL data)
        if page is None:
            items = list(queryset_or_list)
            return {
                "items": items,
                "pagination": {
                    "count": len(items),
                    "page": 1,
                    "page_count": 1,
                    "page_size": len(items),
                    "next": None,
                    "previous": None,
                }
            }

        # Normal pagination
        return {
            "items": page,
            "pagination": {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_count": self.page.paginator.num_pages,
                "page_size": self.get_page_size(request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            }
        }
