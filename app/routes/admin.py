"""
Admin API routes — restricted to role: admin.

GET  /v1/admin/stats
GET  /v1/admin/accounts
POST /v1/admin/accounts
POST /v1/admin/accounts/{account_id}/suspend
POST /v1/admin/accounts/{account_id}/reactivate
GET  /v1/admin/records?q=&state=&legal-basis=&limit=
GET  /v1/admin/webhooks
GET  /v1/admin/audit?account_id=&event_type=&ak=&limit=
"""
import hashlib

from flask import Blueprint, request

from app import db
from app.utils import ok, err, meta, require_bearer, VALID_BASES, VALID_STATES

bp = Blueprint("admin", __name__)


# ── stats dashboard ───────────────────────────────────────────────────────────

@bp.route("/v1/admin/stats", methods=["GET"])
@require_bearer("admin")
def get_stats(token_payload):
    return ok({"response": meta("/v1/admin/stats"), **db.get_account_stats()})


# ── accounts ──────────────────────────────────────────────────────────────────

@bp.route("/v1/admin/accounts", methods=["GET"])
@require_bearer("admin")
def list_accounts(token_payload):
    accounts = db.list_all_accounts()
    return ok({
        "response":  meta("/v1/admin/accounts"),
        "accounts":  [_serialise_account(a) for a in accounts],
        "total":     len(accounts),
    })


@bp.route("/v1/admin/accounts", methods=["POST"])
@require_bearer("admin")
def create_account(token_payload):
    body = request.get_json(silent=True) or {}

    errors = []
    required = ["account-id", "secret-key", "duid", "display-name", "role"]
    for f in required:
        if not body.get(f):
            errors.append(f"'{f}' required")

    valid_roles = {"data_user", "data_provider", "dcc", "admin", "portal"}
    if body.get("role") and body["role"] not in valid_roles:
        errors.append(f"role must be one of {sorted(valid_roles)}")

    if errors:
        return err("; ".join(errors), 400, "VAL001")

    existing = db.get_account(body["account-id"])
    if existing:
        return err(f"Account '{body['account-id']}' already exists", 409, "CON001")

    doc = db.create_account(
        account_id=body["account-id"],
        secret_key=body["secret-key"],
        duid=body["duid"],
        display_name=body["display-name"],
        role=body["role"],
        contact_url=body.get("contact-url", ""),
        data_types=body.get("data-types", []),
    )

    db.write_audit(token_payload["sub"], "account.created", {
        "account_id": body["account-id"],
        "role":       body["role"],
        "duid":       body["duid"],
    })

    return ok({
        "response": meta("/v1/admin/accounts"),
        "account":  _serialise_account(doc),
    }, 201)


@bp.route("/v1/admin/accounts/<account_id>/suspend", methods=["POST"])
@require_bearer("admin")
def suspend_account(account_id, token_payload):
    doc = db.suspend_account(account_id)
    if not doc:
        return err("Account not found", 404, "NOT001")
    db.write_audit(token_payload["sub"], "account.suspended", {"account_id": account_id})
    return ok({"response": meta(f"/v1/admin/accounts/{account_id}"),
                "account": _serialise_account(doc)})


@bp.route("/v1/admin/accounts/<account_id>/reactivate", methods=["POST"])
@require_bearer("admin")
def reactivate_account(account_id, token_payload):
    doc = db.reactivate_account(account_id)
    if not doc:
        return err("Account not found", 404, "NOT001")
    db.write_audit(token_payload["sub"], "account.reactivated", {"account_id": account_id})
    return ok({"response": meta(f"/v1/admin/accounts/{account_id}"),
                "account": _serialise_account(doc)})


# ── access records ────────────────────────────────────────────────────────────

@bp.route("/v1/admin/records", methods=["GET"])
@require_bearer("admin")
def list_records(token_payload):
    q          = request.args.get("q", "").strip()
    state      = request.args.get("state")
    basis      = request.args.get("legal-basis")
    limit      = min(int(request.args.get("limit", 100)), 500)

    if state and state not in VALID_STATES:
        return err(f"state must be one of {sorted(VALID_STATES)}", 400, "VAL002")
    if basis and basis not in VALID_BASES:
        return err("legal-basis invalid", 400, "VAL003")

    if q:
        docs = db.search_records(q, limit)
    else:
        docs = db.list_all_records(limit, state, basis)

    return ok({
        "response": meta("/v1/admin/records"),
        "records":  [_serialise_record(d) for d in docs],
        "total":    len(docs),
    })


# ── webhooks ──────────────────────────────────────────────────────────────────

@bp.route("/v1/admin/webhooks", methods=["GET"])
@require_bearer("admin")
def list_webhooks(token_payload):
    hooks = db.list_all_webhooks()
    return ok({
        "response": meta("/v1/admin/webhooks"),
        "webhooks": [_serialise_webhook(h) for h in hooks],
        "total":    len(hooks),
    })


# ── audit log ─────────────────────────────────────────────────────────────────

@bp.route("/v1/admin/audit", methods=["GET"])
@require_bearer("admin")
def get_audit(token_payload):
    account_id = request.args.get("account_id")
    event_type = request.args.get("event_type")
    ak         = request.args.get("ak")
    limit      = min(int(request.args.get("limit", 100)), 500)

    events = db.list_audit_events(limit, account_id, event_type, ak)
    return ok({
        "response": meta("/v1/admin/audit"),
        "events":   events,
        "total":    len(events),
    })


# ── serialisers ───────────────────────────────────────────────────────────────

def _serialise_account(a: dict) -> dict:
    return {
        "account-id":   a["_id"],
        "duid":         a.get("duid"),
        "display-name": a.get("display_name"),
        "role":         a.get("role"),
        "status":       a.get("status", "active"),
        "contact-url":  a.get("contact_url", ""),
        "registered-at": a.get("registered_at"),
    }

def _serialise_record(d: dict) -> dict:
    p    = d.get("payload", {})
    arr  = p.get("record-metadata", {}).get("controller-arrangement", {})
    lead = next(
        (c.get("name", "") for c in arr.get("controllers", [])
         if c.get("role") in ("sole", "lead")),
        None,
    )
    return {
        "ak":                   d["ak"],
        "duid":                 d.get("duid"),
        "mpxn":                 d.get("mpxn"),
        "state":                d.get("state"),
        "legal-basis":          p.get("processing", {}).get("legal-basis"),
        "purpose":              p.get("processing", {}).get("purpose"),
        "data-types":           p.get("processing", {}).get("data-types", []),
        "lead-controller-name": lead,
        "arrangement-type":     arr.get("arrangement-type"),
        "controller-count":     len(arr.get("controllers", [])),
        "expiry":               p.get("access-event", {}).get("expiry"),
        "created-at":           d.get("created_at"),
        "revoked-at":           d.get("revoked_at"),
    }

def _serialise_webhook(h: dict) -> dict:
    return {
        "wid":                h["wid"],
        "duid":               h.get("duid"),
        "callback-url":       h.get("callback_url"),
        "alert-email":        h.get("alert_email"),
        "notify-days-before": h.get("notify_days_before", 30),
        "event-types":        h.get("event_types", []),
        "active":             h.get("active", True),
        "created-at":         h.get("created_at"),
    }
