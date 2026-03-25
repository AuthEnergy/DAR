"""
Self-service routes — authenticated Data User account management.

GET  /v1/self              — own account profile
POST /v1/self/rotate-secret — rotate secret key (returns new secret once)
"""
import hashlib
import secrets

from flask import Blueprint, request

from app import db
from app.utils import ok, err, meta, require_bearer

bp = Blueprint("self_service", __name__)

REVOKE_REASONS = {
    "customer-request",
    "contract-ended",
    "lia-lapsed",
    "statutory-authority-lapsed",
    "data-no-longer-required",
    "other",
}


@bp.route("/v1/self", methods=["GET"])
@require_bearer("data_user", "admin", "dcc", "data_provider")
def get_self(token_payload):
    account = db.get_account(token_payload["sub"])
    if not account:
        return err("Account not found", 404, "NOT001")
    return ok({
        "response": meta("/v1/self"),
        "account": {
            "account-id":    account["_id"],
            "duid":          account.get("duid"),
            "display-name":  account.get("display_name"),
            "role":          account.get("role"),
            "status":        account.get("status", "active"),
            "contact-url":   account.get("contact_url", ""),
            "registered-at": account.get("registered_at"),
        },
    })


@bp.route("/v1/self/rotate-secret", methods=["POST"])
@require_bearer("data_user", "admin", "dcc", "data_provider")
def rotate_secret(token_payload):
    account_id = token_payload["sub"]
    account    = db.get_account(account_id)
    if not account:
        return err("Account not found", 404, "NOT001")

    new_secret = secrets.token_hex(32)
    account["secret_hash"] = hashlib.sha256(new_secret.encode()).hexdigest()
    account["updated_at"]  = db._now()

    try:
        db._put("dar_accounts", account)
    except Exception:
        return err("Failed to rotate secret", 500, "SRV001")

    db.write_audit(account_id, "account.secret-rotated", {"account_id": account_id})

    return ok({
        "response":   meta("/v1/self/rotate-secret"),
        "secret-key": new_secret,   # returned once only
    })
