"""Email sending via Sweego API (HTTP POST, not SMTP)."""
import asyncio
import json
import logging
import urllib.request
import urllib.error

from app.config import settings

logger = logging.getLogger(__name__)

SWEEGO_API_URL = "https://api.sweego.io/send"
REQUEST_TIMEOUT = 10  # seconds


def _post_email(to: str, subject: str, body: str) -> None:
    """Synchronous Sweego API call (run in thread).

    Logs errors but does not raise — failing registration because Sweego is
    down is worse than a silent email failure. The token is in the DB and
    can be re-sent via /resend-confirmation.
    """
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
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                logger.error("Sweego API returned %s for %s", resp.status, to)
            else:
                logger.info("Email sent to %s", to)
    except urllib.error.URLError as exc:
        logger.error("Sweego API error for %s: %s", to, exc)
    except Exception as exc:
        logger.error("Unexpected error sending email to %s: %s", to, exc)


async def send_email(to: str, subject: str, body: str) -> None:
    """Send a transactional email via the Sweego API.

    Async wrapper around a blocking urllib call.
    """
    await asyncio.to_thread(_post_email, to, subject, body)