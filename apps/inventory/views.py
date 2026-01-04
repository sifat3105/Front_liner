from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from utils.base_view import BaseAPIView as APIView
from apps.vendor.models import Vendor

from .models import Order, Size, Color
from .serializers import (
    ProductSerializer,
    SizeSerializer,
    ColorSerializer
)


# =========================
# PRODUCT
# =========================
class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Product created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        # error এর জন্যও success() ব্যবহার
        return self.success(
            message="Product creation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ProductListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendor_id = request.GET.get("vendor_id")
        search = request.GET.get("search")
        status_filter = request.GET.get("status")

        products = Order.objects.filter(
            vendor__owner=request.user
        ).order_by("-created")

        if vendor_id:
            products = products.filter(
                vendor_id=vendor_id,
                vendor__owner=request.user
            )

        if search:
            products = products.filter(
                Q(product__icontains=search) |
                Q(brand__icontains=search)
            )

        if status_filter:
            products = products.filter(status=status_filter)

        serializer = ProductSerializer(products, many=True)
        return self.success(
            message="Product list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"total": products.count()}
        )

# =========================
# SIZE
# =========================
class SizeListCreateAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = SizeSerializer(Size.objects.all(), many=True)
        return self.success(
            message="Size list fetched",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = SizeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Size created",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        return self.success(
            message="Size creation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# =========================
# COLOR
# =========================
class ColorListCreateAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ColorSerializer(Color.objects.all(), many=True)
        return self.success(
            message="Color list fetched",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = ColorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Color created",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        return self.success(
            message="Color creation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
