from rest_framework import serializers
from .models import (
    Product, ProductPurchaseItem,ProductPurchase, ProductItem, Stock, StockItem, PurchaseReturn, PurchaseReturnItem,
    LossAndDamage, LossAndDamageItem, clean_text
    )
from apps.vendor.models import Vendor
from rest_framework.exceptions import ValidationError
from django.db import transaction
class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "size", "color", "quantity", "unit_cost", "sell_price")


import json
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    items = ProductItemSerializer(many=True)

    vendor_id = serializers.IntegerField(write_only=True)
    vendor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "vendor_id",
            "id",
            "vendor",
            "product",
            "image",
            "short_description",
            "brand",
            "quantity",
            "sku",
            "items",
            "status",
        )
        read_only_fields = ("id", "sku", "created_at")



# ITEM SERIALIZER
class ProductPurchaseItemSerializer(serializers.ModelSerializer):

    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(), 
        write_only=True
    )
    product = serializers.StringRelatedField(read_only=True)

    unit_cost = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False)
    total = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False,read_only=True)

    class Meta:
        model = ProductPurchaseItem
        fields = ("product_id", "id","product","variant","quantity","unit_cost","total",)
        read_only_fields = ("total",)



class ProductPurchaseSerializer(serializers.ModelSerializer):
    vendor_id = serializers.IntegerField(write_only=True)
    vendor_name = serializers.CharField(source="vendor.shop_name", read_only=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    class Meta:
        model = ProductPurchase
        fields = (
            "id",
            "vendor_name",
            "order_date",
            "vendor_id",
            "total_acount",
            "items",
            "notes",
        )
        read_only_fields = ["order_date", "total_acount"]

    def create(self, validated_data):
        vendor_id = validated_data.pop("vendor_id")
        items_data = validated_data.pop("items")

        # ---------- Vendor validation ----------
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or not owned by you"
            })

        # ---------- Required fields ----------
        required_fields = ["product", "size", "color", "unit_cost", "sell_price"]

        total_unit = 0
        total_item = len(items_data)
        total_acount = 0

        # ---------- Atomic transaction ----------
        with transaction.atomic():

            purchase = ProductPurchase.objects.create(
                vendor=vendor,
                **validated_data
            )

            for index, item in enumerate(items_data):

                # support both "quntity" (legacy) and "quantity"
                quantity = item.get("quantity", item.get("quntity"))

                # field validation
                for field in required_fields:
                    if field not in item or item[field] in ("", None):
                        raise serializers.ValidationError({
                            "items": f"Item {index + 1}: '{field}' is required."
                        })

                if quantity in ("", None):
                    raise serializers.ValidationError({
                        "items": f"Item {index + 1}: 'quantity' is required."
                    })

                product_id = item["product"]
                size = item["size"]
                color = item["color"]
                unit_cost = item["unit_cost"]
                sell_price = item["sell_price"]

                total_unit += int(quantity)
                total_acount += int(quantity) * unit_cost

                # ---------- Product ----------
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise serializers.ValidationError({
                        "items": f"Item {index + 1}: Product not found."
                    })
                
                stock = Stock.objects.select_for_update().get(product=product)

                # ---------- ProductItem (lock row) ----------
                product_item, created = ProductItem.objects.select_for_update().get_or_create(
                    product=product,
                    size=size,
                    color=color,
                    defaults={
                        "quantity": quantity,
                        "unit_cost": unit_cost,
                        "sell_price": sell_price,
                    }
                )

                if not created:
                    product_item.quantity += quantity
                    product_item.unit_cost += unit_cost
                    product_item.sell_price += sell_price
                    product_item.save(update_fields=["quantity", "unit_cost", "sell_price"])
                
                stock_item, _ = StockItem.objects.select_for_update().get_or_create(
                    stock=stock,
                    product_item=product_item
                )
                if _ :
                    stock_item.opening+=quantity
                else:
                    stock_item.purchase+=quantity
                    stock_item.save()
                

            # ---------- Summary ----------
            purchase.items = {
                "unit": total_unit,
                "items": total_item
            }
            purchase.total_acount = total_acount
            purchase.save(update_fields=["items", "total_acount"])
            
        return purchase

class PurchaseItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    unit_cost = serializers.DecimalField(
        source="product.unit_cost",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductPurchaseItem
        fields = [
            "id",
            "product"
            "quantity",
            "unit_cost",
            "total_price"
        ]

class PurchaseListSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)
    vendor_name = serializers.CharField(source="vendor.shop_name", read_only=True)
    
    class Meta:
        model = ProductPurchase
        fields = (
            "id",
            "vendor_name",
            "notes",
            "order_date",
            "items",
        )


    
    
class StockSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.product", read_only=True)

    class Meta:
        model = Stock
        fields = (
            "id",
            "sku",
            "product_name",
            "opening",
            "purchase",
            "customer_return",
            "sales",
            "supplier_return",
            "damage",
            "balance",
            "amount",
            "updated_at",
        )
        read_only_fields = ("balance", "updated_at")
        

class StockItemSerializer(serializers.ModelSerializer):
    stock_qty = serializers.ReadOnlyField()
    available = serializers.ReadOnlyField()
    value = serializers.ReadOnlyField()
    attributes = serializers.SerializerMethodField()
    barcode = serializers.URLField(source="product_item.barcode.url")
    qr_code = serializers.URLField(source="product_item.qr_code.url")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source="product_item.sell_price")
    cost_price = serializers.DecimalField(max_digits=10, decimal_places=2, source="product_item.unit_cost")
    sku = serializers.CharField(source="product_item.sku", read_only=True)
    weight = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            'id',
            'sku',
            'attributes',
            'barcode',
            'qr_code',
            'price',
            'cost_price',
            'opening',
            'purchase',
            'sales',
            'returns',
            'damage',
            'stock_qty',
            'available',
            'value',
            'weight',
            'status',
            
        ]
        read_only_fields = fields 
        
        
    def get_attributes(self, obj):
        return {
            "size": obj.product_item.size,
            "color": obj.product_item.color,
        }
        
    def get_weight(self, obj):
        return "NA"
    
    def get_status(self, obj):
        return "In Stock" if obj.stock_qty > 0 else "Out of Stock"

    
    

class PurchaseReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product_item.product.product", read_only=True)
    unit_cost = serializers.DecimalField(
        source="product_item.unit_cost",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseReturnItem
        fields = [
            "id",
            "product_name",
            "product_item",
            "quantity",
            "unit_cost",
            "total_price"
        ]

    def get_total_price(self, obj):
        return obj.quantity * obj.product_item.unit_cost
    
    
class PurchaseReturnSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()
    po_number = serializers.SerializerMethodField()
    items = PurchaseReturnItemSerializer(many=True)
    total_amount = serializers.SerializerMethodField()
    class Meta:
        model = PurchaseReturn
        fields = [
            "id",
            "return_number",
            "vendor_name",
            "po_number",
            "purchase_order",
            "return_date",
            "reason",
            "items",
            "total_items",
            "total_qty",
            "total_amount",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "return_number",
            "total_items",
            "total_qty",
            "created_at",
            "updated_at"
        ]
        
    def get_vendor_name(self, obj):
        return obj.purchase_order.vendor.shop_name if obj.purchase_order else ""
    
    def get_po_number(self, obj):
        return obj.purchase_order.purchase_id if obj.purchase_order else ""
    
    def get_total_amount(self, obj):
        return obj.total_amount or 0
    
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        purchase_return = PurchaseReturn.objects.create(**validated_data)

        for item in items_data:
            product_item = ProductItem.objects.get(
                id=item["product_item"].id
            )

            PurchaseReturnItem.objects.create(
                purchase_return=purchase_return,
                product_item=product_item,
                quantity=item["quantity"]
            )

        return purchase_return
    
class LossAndDamageItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = LossAndDamageItem
        fields = (
            "id",
            "product_item",
            "quantity",
            "condition_notes",
        )


class LossAndDamageSerializer(serializers.ModelSerializer):
    items = LossAndDamageItemSerializer(many=True)
    
    class Meta:
        model = LossAndDamage
        fields = (
            "id",
            "damage_number",
            "damage_date",
            "damage_type",
            "total_items",
            "total_qty",
            "total_amount",
            "description",
            "items",
            "created_at",
            "updated_at"
        )
        read_only_fields = ("id", "total_items", "total_qty", "total_amount", "created_at", "updated_at")
    
    def create(self, validated_data):
        request = self.context.get("request")
        items_data = validated_data.pop("items")
        loss_and_damage = LossAndDamage.objects.create(
            user = request.user,
            **validated_data
            )
        
        for item in items_data:
            product_item = ProductItem.objects.get(
                id=item["product_item"].id
            )
            
            LossAndDamageItem.objects.create(
                loss_and_damage=loss_and_damage,
                product_item=product_item,
                quantity=item["quantity"]
            )
        
        return loss_and_damage
    
    
    
class ProductPurchaseForReturnSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.shop_name", read_only=True)
    purchase_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductPurchase
        fields = (
            "id",
            "vendor_name",
            "purchase_id",
        )
    def get_purchase_id(self, obj):
        if obj.purchase_id:
            return obj.purchase_id
        else:
            return f"FL-PO-VA-{obj.id:06d}"
        
        
        
class ProductMiniSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product")
    class Meta:
        model = Product
        fields = ["id", "name", "sku"] 


class ProductPurchaseItemMiniSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer()

    class Meta:
        model = ProductPurchaseItem
        fields = ["id", "quantity", "product"]
        
