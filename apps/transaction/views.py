from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from .models import Transaction
from .serializers import TransactionSerializer


    
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Transactions fetched successfully.",
            "meta": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "data": data
        })


class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        queryset = Transaction.objects.filter(user=user).order_by("-created_at")

        # === SEARCH (transaction_id, description, purpose, category) ===
        search = request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(description__icontains=search) |
                Q(purpose__icontains=search) |
                Q(category__icontains=search)
            )

        # === STATUS FILTER ===
        status_param = request.GET.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        # === CATEGORY FILTER ===
        category_param = request.GET.get("category")
        if category_param:
            queryset = queryset.filter(category=category_param)

        # === DATE RANGE FILTER ===
        start_date = request.GET.get("startDate")
        end_date = request.GET.get("endDate")

        if start_date:
            start = parse_datetime(start_date)
            if start:
                queryset = queryset.filter(created_at__gte=start)

        if end_date:
            end = parse_datetime(end_date)
            if end:
                queryset = queryset.filter(created_at__lte=end)

        # === PAGINATION ===
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TransactionSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
