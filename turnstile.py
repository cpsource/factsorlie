"""Cloudflare Turnstile verification helper."""
import os
import requests


VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token, remoteip=None):
    """Verify a Turnstile token. Returns True if valid or not configured."""
    secret_key = os.getenv("CLOUDFLARE_TURNSTYLE_SECRET_KEY")
    if not secret_key:
        return True  # skip if not configured

    if not token or not isinstance(token, str):
        return False

    payload = {"secret": secret_key, "response": token}
    if remoteip:
        payload["remoteip"] = remoteip

    try:
        resp = requests.post(VERIFY_URL, data=payload, timeout=10)
        return resp.json().get("success", False)
    except Exception:
        return False
