from rest_framework import serializers
from .models import Product, Size, Color,ProductPurchaseItem,ProductPurchase
from apps.vendor.models import Vendor

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ("id", "size")


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ("id", "colors")


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False)
    sale_price = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False,read_only=True)
    cost_price = serializers.DecimalField(max_digits=10,decimal_places=2,coerce_to_string=False,read_only=True)

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
            "campaign",
            "price",
            "sale_price",
            "cost_price",
            "quantity",
            "sizes",
            "colors",
            "status",
        )
        read_only_fields = ("id","created_at")

    def create(self, validated_data):
        request = self.context["request"]
        vendor_id = validated_data.pop("vendor_id")

        if not Vendor.objects.filter(id=vendor_id,owner=request.user).exists():
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or this vendor does not belong to you"
            })

        product = Product.objects.create(
            vendor_id=vendor_id,
            **validated_data
            
        )
        return product
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        


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


# PURCHASE SERIALIZER
class ProductPurchaseSerializer(serializers.ModelSerializer):
    items = ProductPurchaseItemSerializer(many=True)
    vendor_id = serializers.IntegerField(write_only=True)

    vendor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductPurchase
        fields = (
            "id",
            "vendor",
            "vendor_id",
            "order_date",
            "notes",
            "items",
        )
        read_only_fields = ("order_date",)

    def create(self, validated_data):
        request = self.context["request"]

        items_data = validated_data.pop("items")
        vendor_id = validated_data.pop("vendor_id")

        vendor = Vendor.objects.filter(
            id=vendor_id,
            owner=request.user
        ).first()

        if not vendor:
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or not owned by you"
            })

        purchase = ProductPurchase.objects.create(
            vendor=vendor,
            **validated_data
        )

        for item in items_data:
            ProductPurchaseItem.objects.create(
                purchase=purchase,
                **item
            )

        return purchase
