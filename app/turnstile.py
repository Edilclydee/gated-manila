import logging

import requests
from flask import current_app

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
log = logging.getLogger(__name__)


def verify_turnstile(token, remote_ip=None):
    """Return True only if Cloudflare confirms the token. Fails closed on any problem."""
    secret = current_app.config.get("TURNSTILE_SECRET_KEY")
    if not secret or not token:
        return False
    try:
        resp = requests.post(
            VERIFY_URL,
            data={"secret": secret, "response": token, "remoteip": remote_ip or ""},
            timeout=5,
        )
        return bool(resp.json().get("success"))
    except (requests.RequestException, ValueError):
        log.warning("Turnstile verification request failed")
        return False
