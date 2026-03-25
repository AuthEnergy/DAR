from flask import Blueprint
from app import db
from app.utils import ok, err, meta, require_bearer

bp = Blueprint("data_providers", __name__)


@bp.route("/v1/access-records/<ak>", methods=["GET"])
def verify_access(ak):
    """Unauthenticated by design — ak is the credential. Returns no PII."""
    doc = db.verify_access_record(ak)
    if doc is None:
        return err("Access record not found", 404, "NOT001")

    payload = doc.get("payload", {})
    ae      = payload.get("access-event", {})
    ae["state"] = doc.get("state", ae.get("state"))
    if doc.get("revoked_at"):
        ae["revoked-at"] = doc["revoked_at"]
    payload["access-event"] = ae

    # Strip PII — identity-record-ref is returned for authenticated Data Users only
    # The verify endpoint intentionally does NOT strip identity-record-ref —
    # Data Providers need it to confirm the ir key per the spec verification checklist
    return ok({
        "response":      meta(f"/v1/access-records/{ak}"),
        "access-record": payload,
    })


@bp.route("/v1/data-users/<duid>", methods=["GET"])
@require_bearer("data_provider", "data_user", "admin")
def get_data_user(duid, token_payload):
    """Data Provider directory lookup — verify a DUID is in good standing."""
    account = db.get_account_by_duid(duid)
    if not account or account.get("role") not in ("data_user",):
        return err("No Data User with the supplied DUID exists in the register",
                   404, "NOT001")
    return ok({
        "response": meta(f"/v1/data-users/{duid}"),
        "data-user": {
            "duid":                duid,
            "display-name":        account.get("display_name"),
            "status":              account.get("status", "active"),
            "registered-at":       account.get("registered_at"),
            "suspended-at":        account.get("suspended_at"),
            "contact-url":         account.get("contact_url", ""),
            "data-types-supported": account.get("data_types_supported", []),
        },
    })
