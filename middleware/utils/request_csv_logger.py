import csv
import os
import threading
import queue
from datetime import datetime

CSV_FILE = "request_logs.csv"
log_queue = queue.Queue()

def csv_worker():
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="", buffering=1) as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "request_id",
                "ip",
                "method",
                "path",
                "status",
                "message",
                "user_email"
            ])

        while True:
            row = log_queue.get()
            if row is None:
                break
            writer.writerow(row)
            log_queue.task_done()

threading.Thread(target=csv_worker, daemon=True).start()


def log_to_csv(request_id, ip, method, path, status, message=None, user_email=None):
    log_queue.put([
        datetime.utcnow().isoformat(),
        request_id,
        ip,
        method,
        path,
        status,
        message,
        user_email
    ])
