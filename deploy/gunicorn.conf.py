import multiprocessing


# Bind to local socket for Nginx proxy.
bind = "127.0.0.1:8000"

# ASGI app (supports HTTP + WebSocket through Channels).
wsgi_app = "project.asgi:application"

# Uvicorn worker lets Gunicorn serve ASGI.
worker_class = "uvicorn.workers.UvicornWorker"

# Keep worker count modest; tune later with real traffic.
workers = max(2, multiprocessing.cpu_count() // 2)
threads = 1

timeout = 120
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

accesslog = "/var/log/frontliner/gunicorn-access.log"
errorlog = "/var/log/frontliner/gunicorn-error.log"
loglevel = "info"

capture_output = True
