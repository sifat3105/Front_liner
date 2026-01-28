
import uuid
from django.db.models.fields.files import FieldFile

EXCLUDE_FIELDS = {"updated_at"} 

def assistant_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        name = field.name
        if name in EXCLUDE_FIELDS:
            continue

        value = getattr(instance, name, None)

        if isinstance(value, uuid.UUID):
            value = str(value)
        elif isinstance(value, FieldFile):
            value = value.url if value and hasattr(value, "url") else ""
        elif hasattr(value, "isoformat"):
            value = value.isoformat()

        data[name] = value
    return data


def make_diff(old_data, new_data):
    diff = {}
    keys = set(old_data.keys()) | set(new_data.keys())
    for key in keys:
        if old_data.get(key) != new_data.get(key):
            diff[key] = {
                "old": old_data.get(key),
                "new": new_data.get(key),
            }
    return diff


def generate_history_topic(diff: dict) -> str:
    if not diff:
        return "No changes"

    if "__created__" in diff:
        return "Assistant created"

    keys = list(diff.keys())

    if len(keys) == 1:
        return f"Updated {keys[0]}"

    return f"Updated {len(keys)} fields"