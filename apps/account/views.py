from utils.base_view import BaseAPIView as APIView
from rest_framework import status
from django.db.models import Sum
from django.utils import timezone
from rest_framework.response import Response
from django.db.models import Q
from .base import BaseAPIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import (
    Income,
    Sells,
    Refund,
    DebitCredit,
    ProfitLossReport,Payment
)
from .serializers import (
    IncomeSerializer, 
    CustomerRefundSerializer,
    DebitCreditSerializer,
    ProfitLossReportSerializer,
    CustomerSellsSerializer,PaymentSerializer
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
        return Response({
            "message": "Income fetched successfully",
            "data": {
                "summary": summary,
                "table": serializer.data,
                }, 
            "meta": {"model": "Income"},
            }, status=status.HTTP_200_OK)
        # return self.success(
        #     message="Income fetched successfully",
        #     status_code=200,
        #     data={
        #         "summary": summary,
        #         "table": serializer.data,
        #     },
        #     meta={"model": "Income"},
        # )


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
        refunds = Refund.objects.filter(owner=request.user)
        serializer = CustomerRefundSerializer(refunds, many=True)

        # Return using self.success()
        return self.success(
            message="Refund orders fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "CustomerRefund"},
        )
    

# Debit Credit section

class DebitCreditReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = DebitCredit.objects.filter(owner=request.user)

        serializer = DebitCreditSerializer(queryset, many=True)

        totals = queryset.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )

        summary = {
            "total_debit": totals['total_debit'] or 0,
            "total_credit": totals['total_credit'] or 0,
            "balance": (totals['total_debit'] or 0) - (totals['total_credit'] or 0),
        }

        return self.success(
            message="Debit Credit report fetched successfully",
            status_code=status.HTTP_200_OK,
            data={
                "summary": summary,
                "table": serializer.data,
            }
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

        total_expenses = queryset.aggregate(
            total=Sum('expenses')
        )['total'] or 0

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

# payment API

class PaymentAPIView(APIView):


    def get(self, request):
        payments = Payment.objects.filter(owner=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return self.success(
            message="Refund orders fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"model": "Payment"},
        )
    

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(owner=request.user)
            return self.success(
                message="Payment saved successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data,
                meta={"model": "Payment"},
            )
        else:
            return self.error(
                message="Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
