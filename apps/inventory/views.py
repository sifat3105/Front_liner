from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from apps import transaction
from utils.base_view import BaseAPIView as APIView
from apps.vendor.models import Vendor
from .models import Product, ProductPurchase, Stock, StockItem, ProductItem, PurchaseReturn
from .serializers import StockSerializer, StockItemSerializer, PurchaseReturnSerializer

from .serializers import (
    ProductSerializer,
    ProductPurchaseSerializer
)
import json

from django.db import transaction

class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data

        vendor_id = data.get("vendor_id")
        if not vendor_id:
            return self.error(
                message="vendor_id is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        vendor = Vendor.objects.filter(
            id=vendor_id,
            owner=request.user
        ).first()

        if not vendor:
            return self.error(
                message="Invalid vendor or vendor does not belong to you",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        items = data.get("items")

        if not items:
            return self.error(
                message="items is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(items, str):
            try:
                items = json.loads(items)
            except json.JSONDecodeError:
                return self.error(
                    message="Invalid JSON format for items",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        if isinstance(items, list) and len(items) == 1 and isinstance(items[0], list):
            items = items[0]

        if not isinstance(items, list) or not items:
            return self.error(
                message="items must be a non-empty list",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        product = Product.objects.create(
            vendor=vendor,
            product=data.get("product"),
            short_description=data.get("short_description"),
            brand=data.get("brand"),
            status=data.get("status", "draft"),
            image=data.get("image"),
        )


        total_quantity = 0
        product_items = []

        for index, item in enumerate(items):
            required_fields = ["size", "color", "quantity", "unit_cost", "sell_price"]
            missing = [f for f in required_fields if f not in item]

            if missing:
                return self.error(
                    message=f"Missing fields in item {index + 1}: {missing}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            quantity = int(item.get("quantity", 0))
            total_quantity += quantity

            obj=ProductItem.objects.create(
                product=product,
                size=item["size"],
                color=item["color"],
                quantity=quantity,
                unit_cost=item["unit_cost"],
                sell_price=item["sell_price"],
            )
            product_items.append(obj)


        stock, _ = Stock.objects.get_or_create(
            product=product,
            defaults={
                "opening": total_quantity,
                "purchase": 0,
                "customer_return": 0,
                "sales": 0,
                "supplier_return": 0,
                "damage": 0,
                "balance": total_quantity,
                "amount": 0,
            }
        )

        
        for item in product_items:
            stock_item, _ = StockItem.objects.get_or_create(
                stock=stock,
                product_item=item,
            )
            stock_item.opening += item.quantity
            stock_item.save()
        


        return self.success(
            message="Product created successfully",
            data={
                "id": product.id,
                "product": product.product,
                "sku": product.sku,
                "quantity": total_quantity
            },
            status_code=status.HTTP_201_CREATED
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
    
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
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
            
    @transaction.atomic
    def patch(self, request, pk):
        data = request.data

        # -----------------------
        # 1. Get product safely
        # -----------------------
        product = Product.objects.filter(
            id=pk,
            vendor__owner=request.user
        ).select_for_update().first()

        if not product:
            return self.error(
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # -----------------------
        # 2. Update product fields (partial)
        # -----------------------
        updatable_fields = [
            "product",
            "short_description",
            "brand",
            "status"
        ]

        for field in updatable_fields:
            if field in data:
                setattr(product, field, data.get(field))

        # Image (optional)
        if "image" in data:
            product.image = data.get("image")

        product.save()

        # -----------------------
        # 3. Handle items (optional)
        # -----------------------
        if "items" in data:
            items = data.get("items")

            # Parse JSON string
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return self.error(
                        message="Invalid JSON format for items",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            if isinstance(items, list) and len(items) == 1 and isinstance(items[0], list):
                items = items[0]

            if not isinstance(items, list):
                return self.error(
                    message="items must be a list",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            product.items.all().delete()

            total_quantity = 0

            for index, item in enumerate(items):
                required_fields = ["size", "color", "quantity", "unit_cost", "sell_price"]
                missing = [f for f in required_fields if f not in item]

                if missing:
                    return self.error(
                        message=f"Missing fields in item {index + 1}: {missing}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                quantity = int(item["quantity"])
                total_quantity += quantity

                ProductItem.objects.create(
                    product=product,
                    size=item["size"],
                    color=item["color"],
                    quantity=quantity,
                    unit_cost=item["unit_cost"],
                    sell_price=item["sell_price"],
                )

            Stock.objects.update_or_create(
                product=product,
                defaults={
                    "opening": total_quantity,
                    "balance": total_quantity
                }
            )

        return self.success(
            message="Product updated successfully",
            data={
                "id": product.id,
                "product": product.product,
                "sku": product.sku
            },
            status_code=status.HTTP_200_OK
        )
        
    def delete(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
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
class ProductPurchaseCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    


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
        
        
        
class PurchaseReturnAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        purchase_returns = PurchaseReturn.objects.filter(
            purchase_order__vendor__owner=request.user
        ).prefetch_related("items").order_by("-return_date")
        data = PurchaseReturnSerializer(purchase_returns, many=True).data
        
        return self.success(
            message="Purchase return list fetched" if data else "No purchase returns found",
            data=data,
            status_code=status.HTTP_200_OK,
            meta={"action": "list"}
        )
        
        
    def post(self, request):
        serializer = PurchaseReturnSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success(
            message="Purchase return created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
        

    