from utils.base_view import BaseAPIView as APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from apps.transaction.utils import create_transaction
from apps.user.models import Account
from .models import SubscriptionPlan, UserSubscription


def _add_interval(base, interval, count):
    if interval == "day":
        return base + relativedelta(days=count)
    if interval == "month":
        return base + relativedelta(months=count)
    if interval == "year":
        return base + relativedelta(years=count)
    return base


def _plan_payload(plan, current_plan_id=None, is_active_subscription=False):
    return {
        "id": plan.id,
        "name": plan.name,
        "price": str(plan.price),
        "interval": plan.interval,
        "interval_count": plan.interval_count,
        "features": plan.features or {},
        "is_current": plan.id == current_plan_id,
        "purchase_state": "current" if plan.id == current_plan_id and is_active_subscription else "purchase",
    }


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, "subscription", None)

        if not sub:
            return self.success(
                message="Subscription status",
                data={
                    "active": False,
                    "status": "none",
                    "plan": None,
                    "expires_at": None,
                    "message": "No subscription found. Please subscribe."
                },
                status_code=status.HTTP_200_OK,
                meta={"action": "subscription-status"}
            )

        active = sub.is_active()
        data = {
            "active": active,
            "status": sub.status,
            "plan": getattr(sub.plan, "name", None) if sub.plan else None,
            "expires_at": sub.expires_at,
            "message": "OK" if active else "Subscription expired. Please recharge."
        }

        return self.success(
            message="Subscription status",
            data=data,
            status_code=status.HTTP_200_OK,
            meta={"action": "subscription-status"}
        )


class SubscriptionPlanListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("price", "id")
        sub = getattr(request.user, "subscription", None)
        current_plan_id = sub.plan_id if sub else None
        sub_active = sub.is_active() if sub else False

        data = [_plan_payload(plan, current_plan_id, sub_active) for plan in plans]
        current_subscription = {
            "plan_id": current_plan_id,
            "plan_name": sub.plan.name if sub and sub.plan else None,
            "status": sub.status if sub else "none",
            "active": sub_active,
            "expires_at": sub.expires_at if sub else None,
        }

        return self.success(
            message="Subscription plans fetched",
            data=data,
            extra_data={"current_subscription": current_subscription},
            status_code=status.HTTP_200_OK,
            meta={"action": "subscription-plans"}
        )


class SubscriptionPlanDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plan_id):
        plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()
        if not plan:
            return self.error(
                message="Subscription plan not found",
                status_code=status.HTTP_404_NOT_FOUND,
                meta={"action": "subscription-plan-detail"}
            )

        sub = getattr(request.user, "subscription", None)
        current_plan_id = sub.plan_id if sub else None
        sub_active = sub.is_active() if sub else False

        return self.success(
            message="Subscription plan fetched",
            data=_plan_payload(plan, current_plan_id, sub_active),
            status_code=status.HTTP_200_OK,
            meta={"action": "subscription-plan-detail"}
        )


class PurchaseSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        plan_id = request.data.get("plan_id") or request.data.get("plan")
        if not plan_id:
            return self.error(
                message="plan_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "subscription-purchase"}
            )

        plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()
        if not plan:
            return self.error(
                message="Subscription plan not found or inactive",
                status_code=status.HTTP_404_NOT_FOUND,
                meta={"action": "subscription-purchase"}
            )

        account, _ = Account.objects.select_for_update().get_or_create(user=request.user)
        if plan.price and account.balance < plan.price:
            return self.error(
                message="Insufficient balance",
                status_code=status.HTTP_400_BAD_REQUEST,
                meta={"action": "subscription-purchase"}
            )

        sub, _ = UserSubscription.objects.select_for_update().get_or_create(user=request.user)
        previous_status = sub.status

        now = timezone.now()
        base_date = now
        if sub.status == "active" and sub.expires_at and sub.expires_at > now:
            base_date = sub.expires_at

        expires_at = _add_interval(base_date, plan.interval, plan.interval_count)

        sub.plan = plan
        sub.status = "active"
        if not sub.started_at or previous_status != "active":
            sub.started_at = now
        sub.expires_at = expires_at
        sub.last_renewed_at = now
        sub.save()

        if plan.price:
            account.balance -= plan.price
            account.save(update_fields=["balance"])
            create_transaction(
                user=request.user,
                status="completed",
                category="other",
                amount=plan.price,
                description=f"Subscription purchase: {plan.name}",
                purpose="Subscription Purchase",
                payment_method="balance"
            )

        return self.success(
            message="Subscription purchased successfully",
            data={
                "plan": _plan_payload(plan, plan.id, True),
                "status": sub.status,
                "expires_at": sub.expires_at,
                "balance": str(account.balance),
            },
            status_code=status.HTTP_201_CREATED,
            meta={"action": "subscription-purchase"}
        )
