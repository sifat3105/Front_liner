def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # first IP is the real client
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")
