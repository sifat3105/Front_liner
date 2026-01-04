from rest_framework import serializers
from .models import Order, Size, Color
from apps.vendor.models import Vendor


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ("id", "name")


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ("id", "name", "code")


class ProductSerializer(serializers.ModelSerializer):
    # write (POST / PUT)
    sizes = serializers.PrimaryKeyRelatedField(
        queryset=Size.objects.all(),
        many=True,
        required=False
    )
    colors = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(),
        many=True,
        required=False
    )

    vendor_id = serializers.IntegerField(write_only=True)

    vendor = serializers.StringRelatedField(read_only=True)
    sizes_detail = SizeSerializer(source="sizes", many=True, read_only=True)
    colors_detail = ColorSerializer(source="colors", many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "vendor",
            "vendor_id",
            "image",
            "product",
            "short_description",
            "brand",
            "campaign",
            "price",
            "sale_price",
            "cost_price",
            "quantity",
            "sizes",
            "sizes_detail",
            "colors",
            "colors_detail",
            "status",
            "created",
        )

    def create(self, validated_data):
        request = self.context["request"]

        vendor_id = validated_data.pop("vendor_id")
        sizes = validated_data.pop("sizes", [])
        colors = validated_data.pop("colors", [])

        # vendor must belong to logged-in user
        vendor = Vendor.objects.filter(
            id=vendor_id,
            owner=request.user
        ).first()

        if not vendor:
            raise serializers.ValidationError({
                "vendor_id": "Invalid vendor or this vendor does not belong to you"
            })

        product = Order.objects.create(
            vendor=vendor,
            **validated_data
        )

        product.sizes.set(sizes)
        product.colors.set(colors)

        return product