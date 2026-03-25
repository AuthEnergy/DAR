"""
Webhook management routes.
Uses spec field names: callback-url, alert-email, notify-days-before.
"""
import secrets
from flask import Blueprint, request
from app import db
from app.utils import ok, err, meta, require_bearer

bp = Blueprint("webhooks", __name__)

VALID_EVENT_TYPES = {"consent.expiring", "tenancy.change", "consent.withdrawal"}


@bp.route("/v1/webhooks", methods=["GET"])
@require_bearer("data_user", "admin")
def list_webhooks(token_payload):
    hooks = db.list_webhooks(token_payload["duid"])
    return ok({
        "response": meta("/v1/webhooks"),
        "webhooks": [_serialise(h) for h in hooks],
    })


@bp.route("/v1/webhooks", methods=["POST"])
@require_bearer("data_user", "admin")
def create_webhook(token_payload):
    body         = request.get_json(silent=True) or {}
    callback_url = body.get("callback-url", "")
    alert_email  = body.get("alert-email", "")
    notify_days  = body.get("notify-days-before", 30)
    event_types  = body.get("event-types", list(VALID_EVENT_TYPES))

    errors = []
    if not callback_url or not callback_url.startswith("https://"):
        errors.append("callback-url must be an HTTPS URL")
    if not alert_email or "@" not in alert_email:
        errors.append("alert-email required and must be a valid email address")
    bad = [e for e in event_types if e not in VALID_EVENT_TYPES]
    if bad:
        errors.append(f"unknown event-types: {bad}")
    if errors:
        return err("; ".join(errors), 400, "VAL001")

    # Check for duplicate callback-url
    existing = db.get_webhook_by_callback_url(token_payload["duid"], callback_url)
    if existing:
        return err("A subscription with this callback-url already exists. "
                   "Use PATCH to update it.", 409, "CON001")

    signing_secret = secrets.token_hex(32)
    doc = db.create_webhook(token_payload["duid"], callback_url, alert_email,
                             notify_days, event_types, signing_secret)
    return ok({
        "response":       meta("/v1/webhooks"),
        "webhook":        _serialise(doc),
        "signing-secret": signing_secret,
    }, 201)


@bp.route("/v1/webhooks/<wid>", methods=["DELETE"])
@require_bearer("data_user", "admin")
def delete_webhook(wid, token_payload):
    if not db.delete_webhook(wid, token_payload["duid"]):
        return err("Webhook not found or access denied", 404, "NOT001")
    return ("", 204)


@bp.route("/v1/webhooks/<wid>", methods=["PATCH"])
@require_bearer("data_user", "admin")
def update_webhook(wid, token_payload):
    body   = request.get_json(silent=True) or {}
    errors = []
    if "callback-url" in body and not body["callback-url"].startswith("https://"):
        errors.append("callback-url must be HTTPS")
    if "alert-email" in body and "@" not in body.get("alert-email", ""):
        errors.append("alert-email must be a valid email address")
    if "event-types" in body:
        bad = [e for e in body["event-types"] if e not in VALID_EVENT_TYPES]
        if bad:
            errors.append(f"unknown event-types: {bad}")
    if errors:
        return err("; ".join(errors), 400, "VAL001")

    doc, new_secret = db.update_webhook(wid, token_payload["duid"], body)
    if doc is None:
        return err("Webhook not found or access denied", 404, "NOT001")

    resp = {"response": meta(f"/v1/webhooks/{wid}"), "webhook": _serialise(doc)}
    if new_secret:
        resp["signing-secret"] = new_secret
    return ok(resp)


def _serialise(h: dict) -> dict:
    return {
        "wid":                h["wid"],
        "callback-url":       h.get("callback_url"),
        "alert-email":        h.get("alert_email"),
        "notify-days-before": h.get("notify_days_before", 30),
        "event-types":        h.get("event_types", []),
        "created-at":         h.get("created_at"),
    }
