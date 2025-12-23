from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .serializers import InvoiceListSerializer, InvoiceDetailSerializer, AdminInvoiceListSerializer, AdminInvoiceDetailSerializer, InvoiceSerializer
from .models import Invoice, AdminInvoice

class InvoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Invoices fetched successfully.",
            "meta": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "data": data
        })


class InvoiceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices_qs = Invoice.objects.filter(user=request.user)
        paginator = InvoicePagination()
        paginated_qs = paginator.paginate_queryset(invoices_qs, request)
        serializer = InvoiceListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        try:
            serializer = InvoiceSerializer(data=request.data)
            if serializer.is_valid():
                invoice = serializer.save(user=request.user)
                return Response({
                    "status": "success",
                    "status_code": status.HTTP_201_CREATED,
                    "message": "Invoice created successfully.",
                    "data": InvoiceSerializer(invoice).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invoice creation failed.",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred during invoice creation.",
                "data": {"detail": str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class InvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceDetailSerializer
    
    def get(self, request, pk):
        try:
            obj = Invoice.objects.get(pk=pk, user=request.user)
        except Invoice.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Invoice not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        invoice = InvoiceDetailSerializer(obj)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Invoice details fetched successfully.",
            "data": invoice.data
        })
        

class BillingInvoiceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        invoices_qs = AdminInvoice.objects.filter(assigned_to=request.user)
        paginator = InvoicePagination()
        paginated_qs = paginator.paginate_queryset(invoices_qs, request)
        serializer = AdminInvoiceListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class BillingInvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            obj = AdminInvoice.objects.get(pk=pk, assigned_to=request.user)
        except AdminInvoice.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Invoice not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        invoice = AdminInvoiceDetailSerializer(obj)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Invoice details fetched successfully.",
            "data": invoice.data
        })