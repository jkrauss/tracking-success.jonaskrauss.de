"""Email sending via Sweego API (HTTP POST, not SMTP)."""
import asyncio
import json
import urllib.request
import urllib.error

from app.config import settings

SWEEGO_API_URL = "https://api.sweego.io/send"


def _post_email(to: str, subject: str, body: str) -> None:
    """Synchronous Sweego API call (run in thread)."""
    payload = json.dumps({
        "channel": "email",
        "provider": "sweego",
        "recipients": [{"email": to}],
        "from": {
            "name": settings.smtp_from_name,
            "email": settings.smtp_from_email,
        },
        "subject": subject,
        "message-txt": body,
        "campaign-type": "transac",
    }).encode("utf-8")

    req = urllib.request.Request(
        SWEEGO_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Api-Key": settings.sweego_api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.URLError:
        # In production, log the error. Don't crash the request.
        pass


async def send_email(to: str, subject: str, body: str) -> None:
    """Send a transactional email via the Sweego API.

    Async wrapper around a blocking urllib call.
    """
    await asyncio.to_thread(_post_email, to, subject, body)