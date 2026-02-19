import logging

from asgiref.sync import async_to_sync
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order

from apps.call.services.next_gen_services import make_a_call

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def create_order_confirmation_call(sender, instance, created, **kwargs):
    if not created:
        return

    order_id = instance.id

    def _trigger_after_commit():
        try:
            # make_a_call is async; run it safely from this sync signal.
            async_to_sync(make_a_call)(
                to=8801790166212,
                ngs_from=9610994399,
                order_id=order_id,
            )
        except Exception:
            logger.exception("Order confirmation call trigger failed for order id=%s", order_id)

    transaction.on_commit(_trigger_after_commit)
