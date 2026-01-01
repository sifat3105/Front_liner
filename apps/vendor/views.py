from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from utils.base_view import BaseAPIView as APIView
from .models import Vendor
from .serializers import VendorSerializer


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