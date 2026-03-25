"""
Webhook dispatcher — HMAC-SHA256 signed delivery matching the spec envelope.

Payload shape per spec WebhookEventEnvelope:
  { event-id, event-type, occurred-at, wid, payload: { ... } }
"""
import hashlib
import hmac
import json
import secrets
import threading
import time

import requests as _requests

from app import db

WEBHOOK_TIMEOUT = 10
RETRY_DELAYS    = [60, 300, 1800, 7200, 86400]


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _deliver_one(hook: dict, event_type: str, event_payload: dict):
    event_id  = f"evt_{secrets.token_hex(12)}"
    occurred  = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    envelope  = {
        "event-id":    event_id,
        "event-type":  event_type,
        "occurred-at": occurred,
        "wid":         hook["wid"],
        "payload":     event_payload,
    }
    body    = json.dumps(envelope).encode()
    headers = {
        "Content-Type":    "application/json",
        "X-DAR-Event":     event_type,
        "X-DAR-Signature": _sign(hook.get("signing_secret", ""), body),
        "X-DAR-Timestamp": str(int(time.time())),
    }
    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            r = _requests.post(hook["callback_url"], data=body,
                               headers=headers, timeout=WEBHOOK_TIMEOUT)
            if r.status_code < 500:
                return
        except Exception:
            pass


def deliver_event(duid: str, event_type: str,
                  payload: dict, mpxn: str = None):
    if event_type == "tenancy.change" and mpxn:
        hooks = db.get_all_webhooks_for_event(event_type, mpxn)
    else:
        hooks = db.get_webhooks_for_event(duid, event_type)

    for hook in hooks:
        t = threading.Thread(
            target=_deliver_one,
            args=(hook, event_type, payload),
            daemon=True,
        )
        t.start()
