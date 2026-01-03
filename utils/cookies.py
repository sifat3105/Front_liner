import json

DEFAULT_COOKIE_OPTIONS = {
    "httponly": True,
    "secure": True,
    "samesite": "Lax",
    "path": "/",
}

COOKIE_MAX_AGE = {
    "at": 15 * 60,          # 15 min
    "rt": 7 * 24 * 3600,    # 7 days
    "sid": 7 * 24 * 3600,
    "ctx": 7 * 24 * 3600,
}

def set_cookies(response, cookies: dict):

    for key, value in cookies.items():
        response.set_cookie(
            key=key,
            value=json.dumps(value) if isinstance(value, (dict, list)) else value,
            max_age=COOKIE_MAX_AGE.get(key),
            **DEFAULT_COOKIE_OPTIONS
        )

    return response
