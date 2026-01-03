from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from utils.base_view import BaseAPIView as APIView
from django.db.models import Sum, F, Value,DecimalField
from django.db.models.functions import Coalesce
from .models import Vendor,VendorInvoice
from .serializers import VendorSerializer,VendorPaymentHistorySerializer


class VendorRegistrationAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VendorSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=request.user)

            return self.success(
                message="Vendor registered successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
                meta={"model": "Vendor"},
            )

        return self.error(
            message="Vendor registration failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class VendorListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendors = Vendor.objects.filter(
            owner=request.user
        ).order_by('-created_at')

        serializer = VendorSerializer(vendors, many=True)

        return self.success(
            message="Vendor list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={
                "total_vendors": vendors.count()
            }
        )
    

class VendorDetailUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):

        vendor = Vendor.objects.filter(id=vendor_id,owner=request.user).first()

        if not vendor:
            return self.error(
                message="Vendor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = VendorSerializer(vendor)

        return self.success(
            message="Vendor details fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"model": "Vendor"},
        )

    def patch(self, request, vendor_id):

        vendor = Vendor.objects.filter(
            id=vendor_id,
            owner=request.user
        ).first()

        if not vendor:
            return self.error(
                message="Vendor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = VendorSerializer(
            vendor,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return self.success(
                message="Vendor updated successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
                meta={"model": "Vendor"},
            )

        return self.error(
            message="Vendor update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )



class VendorPaymentHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices = (
            VendorInvoice.objects
            .filter(vendor__owner=request.user)
            .annotate(
                payment=Coalesce(
                    Sum('payments__payment_amount'),
                    Value(0, output_field=DecimalField())
                ),
                due_payment=F('invoice_amount') - Coalesce(
                    Sum('payments__payment_amount'),
                    Value(0, output_field=DecimalField())
                )
            )
            .order_by('-invoice_date')
        )

        serializer = VendorPaymentHistorySerializer(invoices, many=True)

        return self.success(
            message="Vendor payment history fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={
                "total": invoices.count()
            }
        )



class VendorDueListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices = (
            VendorInvoice.objects
            .filter(vendor__owner=request.user)
            .annotate(
                payment=Coalesce(
                    Sum('payments__payment_amount'),
                    Value(0, output_field=DecimalField())
                ),
                due_payment=F('invoice_amount') - Coalesce(
                    Sum('payments__payment_amount'),
                    Value(0, output_field=DecimalField())
                )
            )
            .filter(due_payment__gt=0)
            .order_by('-invoice_date')
        )

        serializer = VendorPaymentHistorySerializer(invoices, many=True)

        return self.success(
            message="Vendor due list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={
                "total_due": invoices.count()
            }
        )
