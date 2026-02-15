from django.utils import timezone
from rest_framework import permissions

from utils.base_view import BaseAPIView as APIView

from .models import Order, OrderCallConfirmation
from .serializers import OrderListSerializer, OrderSerializer
from .services import book_order_to_active_courier


class OrderListAPIView(APIView):

    def get(self, request, *args, **kwargs):
        order_type = kwargs.get('type')

        status_map = {
            'confirm': 'CONFIRM',
            'reject': 'CANCEL',
            'list': 'PENDING',
        }

        orders = Order.objects.filter(
            user=request.user,
            order_status=status_map.get(order_type)
        ) if order_type in status_map else Order.objects.none()

        serializer = OrderListSerializer(orders, many=True)
        return self.success(data=serializer.data)


class OrderDetailAPIView(APIView):

    def get(self, request, order_id):
        if not Order.objects.filter(user=request.user, id=order_id).exists():
            return self.error(message="Order not found")
        order = Order.objects.prefetch_related('items').get(user=request.user, id=order_id)
        serializer = OrderSerializer(order, context={'request': request})
        return self.success(data=serializer.data)


class OrderCallConfirmationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _get_order_for_user(user, order_id):
        order_qs = Order.objects.filter(id=order_id)
        if not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            order_qs = order_qs.filter(user=user)
        return order_qs.first()

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        return None

    def get(self, request, order_id):
        order = self._get_order_for_user(request.user, order_id)
        if not order:
            return self.error(message="Order not found")

        confirmation = getattr(order, "call_confirmation", None)

        data = {
            "order_id": order.order_id,
            "order_status": order.order_status,
            "call_confirmation": {
                "status": confirmation.status if confirmation else "PENDING",
                "call_sid": confirmation.call_sid if confirmation else None,
                "from_number": confirmation.from_number if confirmation else None,
                "to_number": confirmation.to_number if confirmation else order.contact,
                "courier_booking_ref": confirmation.courier_booking_ref if confirmation else None,
                "courier_booking_error": confirmation.courier_booking_error if confirmation else None,
                "confirmed_at": confirmation.confirmed_at if confirmation else None,
            }
        }

        return self.success(data=data)

    def post(self, request, order_id):
        order = self._get_order_for_user(request.user, order_id)
        if not order:
            return self.error(message="Order not found")

        confirmed = self._parse_bool(request.data.get("confirmed"))
        if confirmed is None:
            return self.error(message="'confirmed' must be a boolean value")

        notes = request.data.get("notes")

        confirmation, _ = OrderCallConfirmation.objects.get_or_create(
            order=order,
            defaults={"to_number": order.contact},
        )

        confirmation.notes = notes
        confirmation.confirmed_by = request.user
        confirmation.confirmed_at = timezone.now()

        if confirmed:
            order.order_status = "CONFIRM"
            order.save(update_fields=["order_status", "updated_at"])

            confirmation.status = "CONFIRMED"
            confirmation.courier_booking_error = ""

            courier_order = None
            booking_ref = None
            created = False
            try:
                courier_order, created, booking_ref = book_order_to_active_courier(order)
                confirmation.courier_booking_ref = booking_ref
            except Exception as exc:
                confirmation.courier_booking_error = str(exc)

            confirmation.save()

            return self.success(
                message="Order confirmed successfully",
                data={
                    "order_id": order.order_id,
                    "order_status": order.order_status,
                    "confirmed": True,
                    "courier_booked": bool(courier_order),
                    "courier_booking_ref": booking_ref,
                    "courier_booking_created": created,
                    "courier_booking_error": confirmation.courier_booking_error,
                }
            )

        order.order_status = "CANCEL"
        order.save(update_fields=["order_status", "updated_at"])

        confirmation.status = "REJECTED"
        confirmation.courier_booking_ref = None
        confirmation.courier_booking_error = ""
        confirmation.save()

        return self.success(
            message="Order marked as rejected",
            data={
                "order_id": order.order_id,
                "order_status": order.order_status,
                "confirmed": False,
            }
        )
