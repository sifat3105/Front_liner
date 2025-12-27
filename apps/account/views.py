from utils.base_view import BaseAPIView as APIView
from rest_framework import status
from django.db.models import Sum
from django.utils import timezone
from rest_framework.response import Response
from django.db.models import Q
from .base import BaseAPIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import (
    Income,
    Payments,
    CustomerRefund,
    VoucherEntry,
    ProfitLossReport,
    Receiver, Product,
    Invoice, Payment,Sells
)

from .serializers import (
    IncomeSerializer, 
    PaymentsSerializer,
    CustomerRefundSerializer,
    VoucherEntrySerializer,
    ProfitLossReportSerializer,
    ReceiverSerializer, ProductSerializer, 
    InvoiceSerializer, PaymentSerializer,
    CustomerSellsSerializer,
)


# Income section APIView
class IncomeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Income.objects.filter(owner=request.user).order_by('-created_at')
        serializer = IncomeSerializer(queryset, many=True)
        total_income = queryset.aggregate(total=Sum('amount'))['total'] or 0

        # Monthly income
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        monthly_income = queryset.filter(date__gte=first_day_of_month).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Daily income
        daily_income = queryset.filter(date=today).aggregate(
            total=Sum('amount')
        )['total'] or 0

        summary = {
            "total_income": total_income,
            "monthly_income": monthly_income,
            "daily_income": daily_income,
        }

        # Step 4: Return response
        return self.success(
            message="Income fetched successfully",
            status_code=200,
            data={
                "summary": summary,
                "table": serializer.data,
            },
            meta={"model": "Income"},
        )
class PaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Payments.objects.filter(owner=request.user).order_by('-date')
        serializer = PaymentsSerializer(items, many=True)

        return self.success(
            message="Payments fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "Payment"},
        )


# Sell Orders section 
class CustomerSellsListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sells = Sells.objects.filter(owner=request.user)
        serializer = CustomerSellsSerializer(sells, many=True)

        # Return using self.success()
        return self.success(
            message="Sell orders fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "Sells"},
        )



# Refund Orders section 
class CustomerRefundListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        refunds = CustomerRefund.objects.filter(owner=request.user)
        serializer = CustomerRefundSerializer(refunds, many=True)

        # Return using self.success()
        return self.success(
            message="Refund orders fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "CustomerRefund"},
        )
    

# Debit Credit section
class VoucherEntryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    # GET : List all vouchers
    def get(self, request):
        vouchers = VoucherEntry.objects.filter(owner=request.user).order_by('-id')
        serializer = VoucherEntrySerializer(vouchers, many=True)

        return self.success(
            message="Vouchers fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "VoucherEntry"},
        )

    # POST : Create voucher
    def post(self, request):
        serializer = VoucherEntrySerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return self.success(
                message="Voucher created successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data,
                meta={"model": "VoucherEntry"},
            )

        return self.error(
            message="Validation error",
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
        )

    # PUT : Update voucher
    def put(self, request, pk):
        voucher = get_object_or_404(
            VoucherEntry,
            pk=pk,
            owner=request.user
        )

        serializer = VoucherEntrySerializer(
            voucher,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return self.success(
                message="Voucher updated successfully",
                status_code=status.HTTP_200_OK,
                data=serializer.data,
                meta={"model": "VoucherEntry"},
            )

        return self.error(
            message="Validation error",
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
        )

    # DELETE : Delete voucher
    def delete(self, request, pk):
        voucher = get_object_or_404(
            VoucherEntry,
            pk=pk,
            owner=request.user
        )
        voucher.delete()

        return self.success(
            message="Voucher deleted successfully",
            status_code=status.HTTP_200_OK,
            data={},
            meta={"model": "VoucherEntry"},
        )


# Profit & Loss (P&L) sectiont
class ProfitLossReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch user-wise reports
        queryset = ProfitLossReport.objects.filter(
            owner=request.user
        ).order_by('-date')

        # Serialize table data
        serializer = ProfitLossReportSerializer(queryset, many=True)

        # ---- Summary Calculation ----
        total_revenue = queryset.aggregate(
            total=Sum('revenue')
        )['total'] or 0

        total_expenses = (
            (queryset.aggregate(total=Sum('expenses'))['total'] or 0) +
            (queryset.aggregate(total=Sum('operating_expenses'))['total'] or 0)
        )

        net_profit = total_revenue - total_expenses

        summary = {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
        }

        return self.success(
            message="Profit & Loss data fetched successfully",
            status_code=status.HTTP_200_OK,
            data={
                "summary": summary,
                "table": serializer.data,
            },
            meta={"model": "ProfitLossReport"},
        )



# Receiver API
class ReceiverListCreateAPIView(BaseAPIView):
    def post(self, request):

        name = request.data.get('name')
        receiver_type = request.data.get('receiver_type')

        if not name:
            return self.error(
                errors={"name": "This field is required"},
                message="Name is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # check if receiver already exists (case insensitive)
        receiver = Receiver.objects.filter(name__iexact=name).first()

        if receiver:
            # receiver exists → return existing
            serializer = ReceiverSerializer(receiver)
            return self.success(
                data=serializer.data,
                message="Receiver already exists"
            )

        # receiver not exist → create new
        if receiver_type not in ['user', 'supplier']:
            return self.error(
                errors={"receiver_type": "Must be 'user' or 'supplier'"},
                message="Receiver type required for new receiver",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_receiver = Receiver.objects.create(
            name=name,
            receiver_type=receiver_type
        )
        serializer = ReceiverSerializer(new_receiver)

        return self.success(
            data=serializer.data,
            message="Receiver created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
# Product API
class ProductSearchAPIView(BaseAPIView):
    def get(self, request):
        search = request.GET.get('search')

        if not search:
            return self.error(
                errors={"search": "This field is required"},
                message="Search parameter missing",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        products = Product.objects.filter(Q(name__icontains=search) |Q(id__icontains=search)).order_by('name')
        serializer = ProductSerializer(products, many=True)

        return self.success(
            data=serializer.data,
            message="Products fetched successfully"
        )

# Invoice API
class InvoiceListCreateAPIView(BaseAPIView):
    def get(self, request):
        invoices = Invoice.objects.all()
        serializer = InvoiceSerializer(invoices, many=True)
        return self.success(data=serializer.data, message="Invoices fetched successfully")

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(data=serializer.data, message="Invoice created successfully", status_code=status.HTTP_201_CREATED)
        return self.error(errors=serializer.errors, message="Invoice creation failed")

# payment API
class PaymentCreateAPIView(BaseAPIView):

    def post(self, request):
        invoice=request.data.get('invoice')
        if invoice: 
            type="supplier"
        else :
            type="user"
        receiver_name =request.data.get('receiver_name')
        receiver, _= Receiver.objects.get_or_create(name=receiver_name, receiver_type=type)
        data=request.data.copy()
        data.pop('receiver_name', None)

        serializer = PaymentSerializer(
            data=data,
            context={'receiver': receiver}
        )

        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Payment created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return self.error(
            message="Payment failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

