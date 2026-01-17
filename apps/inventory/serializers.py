from rest_framework import serializers
from .models import Product, ProductItem,OrderItem
from apps.vendor.models import Vendor

from decimal import Decimal
from django.db import transaction

class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "size", "color", "quantity", "unit_cost")


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False)
    sale_price = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False,read_only=True)
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
            "price",
            "sale_price",
            "quantity",
            "items",
            "status",
        )
        read_only_fields = ("id","created_at")

    def create(self, validated_data):
        request = self.context["request"]
        vendor_id = validated_data.pop("vendor_id")
        items = validated_data.pop("items")

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
