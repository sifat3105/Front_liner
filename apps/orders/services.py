import logging
import os
from typing import Optional, Tuple

from twilio.rest import Client

from .models import Order, OrderCallConfirmation

logger = logging.getLogger(__name__)


def _resolve_call_assistant(order: Order, from_number: Optional[str] = None):
    from apps.assistant.models import Assistant

    assistants = Assistant.objects.filter(owner=order.user, agent_type="call")

    if from_number:
        matched = assistants.filter(twilio_number=from_number).first()
        if matched:
            return matched

    enabled = assistants.filter(enabled=True).order_by("-updated_at").first()
    if enabled:
        return enabled

    return assistants.order_by("-updated_at").first()


def _resolve_from_number(order: Order) -> Optional[str]:
    assistant = _resolve_call_assistant(order)
    if assistant and assistant.twilio_number:
        return assistant.twilio_number

    from apps.phone_number.models import PhoneNumber

    number = (
        PhoneNumber.objects
        .filter(user=order.user, verified=True)
        .exclude(phone_number="")
        .order_by("-updated_at")
        .first()
    )
    if number:
        return number.phone_number

    fallback = os.getenv("TWILIO_NUMBER", "").strip()
    return fallback or None


def _update_confirmation_failure(confirmation: OrderCallConfirmation, message: str) -> OrderCallConfirmation:
    confirmation.status = "FAILED"
    confirmation.courier_booking_error = message
    confirmation.save(update_fields=["status", "courier_booking_error", "updated_at"])
    return confirmation


def _create_call_log(order: Order, call_sid: str, from_number: str, to_number: str) -> None:
    try:
        from apps.call.models import CallLog
    except Exception:
        logger.exception("Unable to import CallLog for order %s", order.order_id)
        return

    assistant = _resolve_call_assistant(order, from_number)

    try:
        CallLog.objects.create(
            assistant=assistant,
            call_sid=call_sid,
            call_status="ringing",
            direction="outbound",
            caller=from_number,
            callee=to_number,
        )
    except Exception:
        logger.exception("Failed to create call log for order %s", order.order_id)


def trigger_order_confirmation_call(order: Order) -> OrderCallConfirmation:
    confirmation, _ = OrderCallConfirmation.objects.get_or_create(
        order=order,
        defaults={"to_number": order.contact},
    )

    if confirmation.status == "CONFIRMED":
        return confirmation

    if confirmation.to_number != order.contact:
        confirmation.to_number = order.contact
        confirmation.save(update_fields=["to_number", "updated_at"])

    account_sid = os.getenv("TWILIO_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH", "").strip()
    call_url = (
        os.getenv("CALL_WEBHOOK_URL", "").strip()
        or os.getenv("TWILIO_VOICE_WEBHOOK_URL", "").strip()
    )

    if not account_sid or not auth_token or not call_url:
        return _update_confirmation_failure(
            confirmation,
            "Missing TWILIO_SID, TWILIO_AUTH, or CALL_WEBHOOK_URL.",
        )

    from_number = _resolve_from_number(order)
    if not from_number:
        return _update_confirmation_failure(
            confirmation,
            "No caller number configured (assistant.twilio_number, verified phone number, or TWILIO_NUMBER).",
        )

    try:
        client = Client(account_sid, auth_token)
        call = client.calls.create(
            to=order.contact,
            from_=from_number,
            url=call_url,
            record=True,
        )
    except Exception as exc:
        logger.exception("Failed to initiate call for order %s", order.order_id)
        return _update_confirmation_failure(confirmation, str(exc))

    confirmation.call_sid = call.sid
    confirmation.from_number = from_number
    confirmation.to_number = order.contact
    confirmation.status = "CALL_STARTED"
    confirmation.courier_booking_error = ""
    confirmation.save(
        update_fields=[
            "call_sid",
            "from_number",
            "to_number",
            "status",
            "courier_booking_error",
            "updated_at",
        ]
    )

    _create_call_log(order, call.sid, from_number, order.contact)

    return confirmation


def _resolve_courier_booking_ref(courier_order, fallback_ref: str) -> str:
    return courier_order.couriers_id or courier_order.tracking_id or courier_order.invoice or fallback_ref


def book_order_to_active_courier(order: Order) -> Tuple[object, bool, str]:
    from apps.courier.models import CourierOrder, OrderCourierMap, UserCourier

    active_user_courier = (
        UserCourier.objects
        .select_related("courier")
        .filter(user=order.user, is_active=True)
        .first()
    )

    if not active_user_courier or not active_user_courier.courier:
        raise ValueError("No active courier is configured for this user.")

    existing_courier_order = CourierOrder.objects.select_related("courier").filter(order=order).first()
    if existing_courier_order:
        booking_ref = _resolve_courier_booking_ref(existing_courier_order, order.order_id)
        OrderCourierMap.objects.update_or_create(
            order=order,
            defaults={
                "courier": existing_courier_order.courier,
                "courier_order_ref": booking_ref,
            },
        )
        return existing_courier_order, False, booking_ref

    courier_order = CourierOrder.objects.create(
        order=order,
        courier=active_user_courier.courier,
        invoice=order.order_id,
        recipient_name=order.customer,
        recipient_phone=order.contact,
        recipient_address=order.location,
        payment_type="cod",
        status="pending",
        note=f"Auto-booked after call confirmation for order {order.order_id}",
    )

    booking_ref = _resolve_courier_booking_ref(courier_order, order.order_id)

    OrderCourierMap.objects.update_or_create(
        order=order,
        defaults={
            "courier": active_user_courier.courier,
            "courier_order_ref": booking_ref,
        },
    )

    return courier_order, True, booking_ref
