from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from utils.base_view import BaseAPIView as APIView
from apps.vendor.models import Vendor
from .models import Product, ProductPurchase, Stock, StockItem
from .serializers import StockSerializer, StockItemSerializer

from .serializers import (
    ProductSerializer,
    ProductPurchaseSerializer
)

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

        return self.error(
            message="Product creation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ProductListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Product.objects.prefetch_related("items").all()

        serializer = ProductSerializer(queryset, many=True)

        return self.success(
            message="Product list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={
                "total": queryset.count()
            }
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
        

# =========================
# CREATE + LIST PURCHASE
# =========================

class OrderListCreateAPIView(APIView):

    def get(self, request):
        orders = OrderItem.objects.prefetch_related('items').all()

        data = []
        for order in orders:
            data.append({
                "vendor_id": order.vendor_id,
                "order_date": order.order_date,
                "notes": order.notes,
                "items": [
                    {
                        "product_id": item.product_id,
                        "size": item.size,
                        "color": item.color,
                        "quantity": item.quantity,
                        "unit_cost": item.unit_cost,
                        "sell_price": item.sell_price,
                    }
                    for item in order.items.all()
                ]
            })

        return self.success(
            message="Order list fetched successfully",
            data=data
        )

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return self.success(
                message="Order created successfully",
                data=data
            )
        return self.error(serializer.errors)



class OrderDetailAPIView(APIView):

    def get(self, request, pk):
        order = get_object_or_404(
            ProductItem.objects.prefetch_related('items'),
            pk=pk
        )

        data = {
            "vendor_id": order.vendor_id,
            "order_date": order.order_date,
            "notes": order.notes,
            "items": [
                {
                    "product_id": item.product_id,
                    "size": item.size,
                    "color": item.color,
                    "quantity": item.quantity,
                    "unit_cost": item.unit_cost,
                    "sell_price": item.sell_price,
                }
                for item in order.items.all()
            ]
        }

        return self.success(
            message="Order fetched successfully",
            data=data
        )

    @transaction.atomic
    def put(self, request, pk):
        order = get_object_or_404(OrderItem, pk=pk)

        # remove old items & reset totals
        order.items.all().delete()
        order.total_cost = 0
        order.total_sell = 0
        order.total_profit = 0
        order.save()

        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return self.success(
                message="Order updated successfully",
                data=data
            )
        return self.error(serializer.errors)

    @transaction.atomic
    def delete(self, request, pk):
        order = get_object_or_404(OrderItem, pk=pk)
        order.delete()

        return self.success(
            message="Order deleted successfully",
            data=None
        )


class StockListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stocks = Stock.objects.filter(
            product__vendor__owner=request.user
        ).order_by("-updated_at")
        
        serializer = StockSerializer(stocks, many=True)

        return self.success(
            message="Stock list fetched",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"total": stocks.count()}
        )
        
class StockDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, stock_id):
        try:
            stock = Stock.objects.prefetch_related("items").get(id=stock_id)
            stock_items = stock.items.all()
            serializer = StockItemSerializer(stock_items, many=True, context = {'request': request})
            return self.success(
                message="Stock fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        except Stock.DoesNotExist:
            return self.error(
                message="Stock not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.error(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
class ProductPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ProductPurchaseSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success(
            message="Purchase created successfully",
            status_code=status.HTTP_201_CREATED
        )

    