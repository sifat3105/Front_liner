from utils.base_view import BaseAPIView as APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

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

