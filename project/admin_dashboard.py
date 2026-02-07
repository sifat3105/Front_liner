from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.db.models import Count


def dashboard_callback(request, context):
    user_model = get_user_model()

    role_totals = {
        row["role"]: row["total"]
        for row in user_model.objects.values("role").annotate(total=Count("id"))
    }

    context["dashboard_stats"] = [
        {
            "label": "User Count",
            "value": role_totals.get("user", 0),
            "description": "Standard user accounts",
        },
        {
            "label": "Reseller Count",
            "value": role_totals.get("reseller", 0),
            "description": "Top-level reseller accounts",
        },
        {
            "label": "Sub Reseller Count",
            "value": role_totals.get("sub_reseller", 0),
            "description": "Child reseller accounts",
        },
        {
            "label": "Total Accounts",
            "value": user_model.objects.count(),
            "description": "All accounts in the system",
        },
    ]

    log_entries = LogEntry.objects.select_related("user", "content_type").order_by(
        "-action_time"
    )

    if not request.user.is_superuser:
        log_entries = log_entries.filter(user=request.user)

    history = []
    for entry in log_entries[:40]:
        is_addition = entry.is_addition()
        is_change = entry.is_change()
        is_deletion = entry.is_deletion()

        if is_addition:
            action_label = "Add"
        elif is_change:
            action_label = "Change"
        elif is_deletion:
            action_label = "Delete"
        else:
            action_label = "Action"

        history.append(
            {
                "action_label": action_label,
                "is_addition": is_addition,
                "is_change": is_change,
                "is_deletion": is_deletion,
                "object_repr": entry.object_repr,
                "content_type": (
                    entry.content_type.name.title()
                    if entry.content_type
                    else "Unknown content"
                ),
                "user": (
                    entry.user.email
                    if getattr(entry.user, "email", None)
                    else str(entry.user)
                ),
                "action_time": entry.action_time,
                "admin_url": None if is_deletion else entry.get_admin_url(),
            }
        )

    context["dashboard_history"] = history
    return context
