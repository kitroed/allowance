import requests as http_requests
from flask import current_app


def notify_parent(title, message):
    """Send a notification to the parent via ntfy. Fire and forget."""
    server = current_app.config.get("NTFY_SERVER")
    topic = current_app.config.get("NTFY_TOPIC")
    if not server:
        return
    try:
        http_requests.post(
            f"{server}/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": "default"},
            timeout=5,
        )
    except Exception:
        pass
