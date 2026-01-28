from django.contrib.auth import get_user_model

User = get_user_model()

def get_user(**kwargs):
    user_id = kwargs.get("user_id")
    if not user_id:
        return None
    