import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .services import trigger_order_confirmation_call

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def create_order_confirmation_call(sender, instance, created, **kwargs):
    if not created:
        return

    order_id = instance.id

    def _trigger_after_commit():
        order = Order.objects.select_related("user").filter(id=order_id).first()
        if order:
            try:
                trigger_order_confirmation_call(order)
            except Exception:
                logger.exception("Order confirmation call trigger failed for order id=%s", order_id)

    transaction.on_commit(_trigger_after_commit)
