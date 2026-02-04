from rest_framework import serializers

from .models import SubscriptionPlan


class SubscriptionPermissionPayloadSerializer(serializers.Serializer):
    code = serializers.SlugField(max_length=80)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)


class SubscriptionPlanPayloadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    interval = serializers.ChoiceField(choices=SubscriptionPlan.INTERVAL_CHOICES)
    interval_count = serializers.IntegerField(min_value=1)
    is_active = serializers.BooleanField(required=False, default=True)
    features = serializers.JSONField(required=False, default=dict)
    permissions_input = serializers.CharField(required=False, allow_blank=True, write_only=True)
    permissions = SubscriptionPermissionPayloadSerializer(many=True, required=False)

    def validate_permissions(self, value):
        seen = set()
        for idx, item in enumerate(value):
            code = item["code"]
            if code in seen:
                raise serializers.ValidationError(
                    f"Duplicate permission code '{code}' at index {idx}."
                )
            seen.add(code)
        return value

    def validate(self, attrs):
        permissions = attrs.get("permissions")
        permissions_input = attrs.pop("permissions_input", None)
        slug_validator = serializers.SlugField(max_length=80)

        if permissions is not None and permissions_input:
            raise serializers.ValidationError(
                {"permissions_input": "Use either permissions or permissions_input, not both."}
            )

        if permissions_input:
            seen = set()
            parsed = []
            for idx, raw in enumerate(permissions_input.replace(",", "\n").splitlines()):
                code = (raw or "").strip()
                if not code:
                    continue
                try:
                    slug_validator.run_validation(code)
                except serializers.ValidationError:
                    raise serializers.ValidationError(
                        {"permissions_input": f"Invalid permission code '{code}' at line {idx + 1}."}
                    )
                if code in seen:
                    continue
                seen.add(code)
                parsed.append({"code": code})
            attrs["permissions"] = parsed

        return attrs
