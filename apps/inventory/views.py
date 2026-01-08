from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from utils.base_view import BaseAPIView as APIView
from apps.vendor.models import Vendor
from .models import Product, Size, Color,ProductPurchase

from .serializers import (
    ProductSerializer,
    SizeSerializer,
    ColorSerializer,
    ProductPurchaseSerializer
)


# =========================
# PRODUCT
# =========================
class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data['colors'])
        print(list(request.data['colors']))
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

        products = Product.objects.filter(
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

        serializer = ProductSerializer(products, many=True, context={'request': request})
        return self.success(
            message="Product list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"total": products.count()}
        )
        
class ProductDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductSerializer(product, context={'request': request})
            return self.success(
                message="Product fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return self.error(
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.error(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def patch(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return self.error(
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        data = ProductSerializer(
            product,
            data=request.data,
            partial=True,
            context={'request': request}
        ).data
        
        return self.success(
            message="Product updated successfully",
            data=data,
            status_code=status.HTTP_200_OK
        )
        
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return self.error(
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        product.delete()
        
        return self.success(
            message="Product deleted successfully",
            status_code=status.HTTP_200_OK
        )
        

# # SIZE
# class SizeListCreateAPIView(APIView):
#     # permission_classes = [IsAuthenticated]

#     def get(self, request):
#         serializer = SizeSerializer(Size.objects.all(), many=True)
#         return self.success(
#             message="Size list fetched",
#             data=serializer.data,
#             status_code=status.HTTP_200_OK
#         )

#     def post(self, request):
#         serializer = SizeSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return self.success(
#                 message="Size created",
#                 data=serializer.data,
#                 status_code=status.HTTP_201_CREATED
#             )
#         return self.success(
#             message="Size creation failed",
#             data=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )

# # COLOR
# class ColorListCreateAPIView(APIView):
#     # permission_classes = [IsAuthenticated]

#     def get(self, request):
#         serializer = ColorSerializer(Color.objects.all(), many=True)
#         return self.success(
#             message="Color list fetched",
#             data=serializer.data,
#             status_code=status.HTTP_200_OK
#         )

#     def post(self, request):
#         serializer = ColorSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return self.success(
#                 message="Color created",
#                 data=serializer.data,
#                 status_code=status.HTTP_201_CREATED
#             )
#         return self.success(
#             message="Color creation failed",
#             data=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )





# =========================
# CREATE + LIST PURCHASE
# =========================
class ProductPurchaseCreateAPIView(APIView):

    def post(self, request):
        serializer = ProductPurchaseSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return self.success(
                message="Purchase created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return self.success(
            message="Purchase creation failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ProductPurchaseListAPIView(APIView):

    def get(self, request):
        purchases = ProductPurchase.objects.filter(
            vendor__owner=request.user
        ).order_by("-order_date")

        serializer = ProductPurchaseSerializer(purchases, many=True)

        return self.success(
            message="Purchase list fetched",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"total": purchases.count()}
        )
