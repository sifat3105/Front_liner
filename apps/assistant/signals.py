from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from .models import Assistant, AssistantHistory
from .utils import assistant_to_dict, make_diff


@receiver(pre_save, sender=Assistant)
def assistant_pre_save(sender, instance: Assistant, **kwargs):
    # create হলে old নেই
    if not instance.pk:
        instance._old_snapshot = None
        return

    old = sender.objects.filter(pk=instance.pk).first()
    instance._old_snapshot = assistant_to_dict(old) if old else None


@receiver(post_save, sender=Assistant)
def assistant_post_save(sender, instance: Assistant, created: bool, **kwargs):
    old_data = getattr(instance, "_old_snapshot", None)
    new_data = assistant_to_dict(instance)

    if created:
        AssistantHistory.objects.create(
            assistant=instance,
            changed_by=getattr(instance, "_changed_by", None),  # optional
            old_data={},
            new_data=new_data,
            diff={"__created__": {"old": None, "new": "created"}},
        )
        return

    if not old_data:
        return

    diff = make_diff(old_data, new_data)
    if not diff:
        return

    AssistantHistory.objects.create(
        assistant=instance,
        changed_by=getattr(instance, "_changed_by", None),
        old_data=old_data,
        new_data=new_data,
        diff=diff,
    )
    
    
@receiver(pre_delete, sender=Assistant)
def assistant_pre_delete(sender, instance: Assistant, **kwargs):
    old_data = assistant_to_dict(instance)
    AssistantHistory.objects.create(
        assistant=instance,
        changed_by=getattr(instance, "_changed_by", None),
        old_data=old_data,
        new_data={},
        diff={"__deleted__": {"old": "exists", "new": None}},
    )