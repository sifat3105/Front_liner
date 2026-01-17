from rest_framework import serializers
from .models import Product, ProductPurchaseItem,ProductPurchase, ProductItem, Stock, StockItem
from apps.vendor.models import Vendor
from rest_framework.exceptions import ValidationError
import json

class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "size", "color", "quantity", "unit_cost", "sell_price")


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
        read_only_fields = ("id","sku","created_at")
        

    def create(self, validated_data):
        request = self.context["request"]
        vendor_id = validated_data.pop("vendor_id")
        items = validated_data.pop("items")
        item = json.loads(items)

        if not Vendor.objects.filter(id=vendor_id,owner=request.user).exists():
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or this vendor does not belong to you"
            })

        product = Product.objects.create(
            vendor_id=vendor_id,
            **validated_data
            
        )
        for item in items:
            ProductItem.objects.create(
                product=product,
                **item
            )
        
        opening_qty = sum(
            item.quantity for item in product.items.all() if (item.quantity or 0) > 0
        )
            
        Stock.objects.update_or_create(
            product=product,
            defaults={
                "opening": opening_qty,
                "purchase": 0,
                "customer_return": 0,
                "sales": 0,
                "supplier_return": 0,
                "damage": 0,
                "balance": 0,
                "amount": 0,
            }
        )
        
        return product
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        

class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    size = serializers.CharField()
    color = serializers.CharField()
    quantity = serializers.IntegerField()


    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    sell_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
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
    items = serializers.JSONField(default=dict, write_only=True)
    class Meta:
        model = ProductPurchase
        fields = (
            "id",
            "vendor",
            "order_date",
            "vendor_id",
            "items",
            "notes",
        )
        read_only_fields = ("order_date", 'vendor')

    def create(self, validated_data):
        request = self.context["request"]
        vendor_id = validated_data.pop("vendor_id")
        items_data = validated_data.pop("items")
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or not owned by you"
            })
        
        purchase = ProductPurchase.objects.create(
            vendor=vendor,
            **validated_data
        )
        
        required_fields = ["product", "size", "color", "unit_cost", "quntity", "sell_price"]
        total_unit = 0
        total_item = len(items_data)
        for index, item in enumerate(items_data):
            for field in required_fields:
                if field not in item or item[field] in ("", None):
                    raise ValidationError({
                        "items": f"Item {index + 1}: '{field}' is required."
                    })

            product_id = item.pop("product")
            size = item.pop("size")
            color = item.pop("color")
            unit_cost = item.pop("unit_cost")
            quantity = item.pop("quntity")
            sell_price = item.pop("sell_price")
            total_unit += quantity
            
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                raise ValidationError({
                    "items": f"Item {index + 1}: Product not found."
                })
            try:
                product_item, created = ProductItem.objects.get_or_create(
                    product=product,
                    size=size,
                    color=color,
                )
                if created:
                    product_item.quantity = quantity
                    product_item.unit_cost = unit_cost
                    product_item.sell_price = sell_price
                    product_item.save()
                else:
                    product_item.quantity += quantity
                    product_item.unit_cost += unit_cost
                    product_item.sell_price += sell_price
                    product_item.save()
            except:
                raise ValidationError({
                    "items": f"Item {index + 1}: Product Item not found."
                })
                
        purchase.items = {
            "unit": total_unit,
            "items": total_item
        }
        purchase.save()
        return purchase


    
    
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

    
    

        total_price = Decimal(quantity) * sell_price

        item = OrderItem.objects.create(
            order=order,
            product=variant.product,
            size=variant.size,
            color=variant.color,
            quantity=quantity,
            unit_cost=unit_cost,
            sell_price=sell_price,
            total_price=total_price,
        )


        variant.total_quantity += quantity
        variant.save(update_fields=['total_quantity'])

        return item




class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    size = serializers.CharField()
    color = serializers.CharField()
    quantity = serializers.IntegerField()

    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    sell_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )

    def create(self, validated_data):
        order = self.context['order']

        quantity = validated_data['quantity']

        try:
            variant = OrderItem.objects.select_for_update().get(
                product_id=validated_data['product_id'],
                size=validated_data['size'],
                color=validated_data['color'],
            )
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError(
                "Product variant does not exist"
            )

        unit_cost = variant.unit_cost
        sell_price = variant.sell_price

        total_price = Decimal(quantity) * sell_price


        item = OrderItem.objects.create(
            order=order,
            product=variant.product,
            size=variant.size,
            color=variant.color,
            quantity=quantity,
            unit_cost=unit_cost,
            sell_price=sell_price,
            total_price=total_price,
        )

        variant.total_quantity += quantity
        variant.save(update_fields=['total_quantity'])

        return item


class OrderCreateSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    order_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemCreateSerializer(many=True)

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')

        order = OrderItem.objects.create(**validated_data)

        total_sell = Decimal('0')
        total_cost = Decimal('0')

        for item_data in items_data:
            serializer = OrderItemCreateSerializer(
                data=item_data,
                context={'order': order}
            )
            serializer.is_valid(raise_exception=True)
            item = serializer.save()

            total_sell += item.total_price
            total_cost += item.unit_cost * item.quantity

        order.total_sell = total_sell
        order.total_cost = total_cost
        order.total_profit = total_sell - total_cost
        order.save(
            update_fields=['total_sell', 'total_cost', 'total_profit']
        )

        return {
            "vendor_id": validated_data['vendor_id'],
            "order_date": validated_data['order_date'],
            "notes": validated_data.get('notes'),
            "items": items_data
        }
