import re
from flask import Blueprint, request
from app import db
from app.config import Config
from app.utils import ok, err, meta, require_bearer, MPXN_RE
from app.webhooks import deliver_event

bp = Blueprint("portal_dcc", __name__)
URI_RE = re.compile(r"^https?://")


@bp.route("/v1/customer-sessions", methods=["POST"])
@require_bearer("data_user")
def create_portal_session(token_payload):
    body       = request.get_json(silent=True) or {}
    mpxn       = body.get("mpxn", "")
    return_url = body.get("return-url", "")
    purpose    = body.get("purpose", "")

    errors = []
    if not mpxn or not MPXN_RE.match(str(mpxn)):
        errors.append("mpxn required and must be valid MPxN format")
    if not return_url or not URI_RE.match(return_url):
        errors.append("return-url required and must be a valid URI")
    if not purpose:
        errors.append("purpose required")

    account = db.get_data_user_profile(token_payload["duid"])
    if account:
        registered = account.get("callback_urls", [])
        if registered and return_url not in registered:
            errors.append("return-url is not pre-registered for this account")

    if errors:
        return err("; ".join(errors), 400, "VAL001")

    doc        = db.create_portal_session(token_payload["duid"], mpxn,
                                           return_url, purpose)
    token      = doc["token"]
    portal_url = f"{Config.PORTAL_BASE_URL}/consents?token={token}"

    return ok({
        "response":      meta("/v1/customer-sessions"),
        "session-token": token,
        "expires-in":    60,
        "portal-url":    portal_url,
    }, 201)


@bp.route("/v1/discovered-access", methods=["POST"])
@require_bearer("dcc")
def submit_discovered(token_payload):
    body   = request.get_json(silent=True) or {}
    errors = []
    required = ["mpxn", "organisation-name", "organisation-reference",
                "first-seen", "data-types-observed", "source-reference"]
    for f in required:
        if not body.get(f):
            errors.append(f"'{f}' required")
    if body.get("mpxn") and not MPXN_RE.match(str(body["mpxn"])):
        errors.append("mpxn invalid format")
    if errors:
        return err("; ".join(errors), 400, "VAL001")

    doc, created = db.submit_discovered_record(body)
    return ok({
        "response": meta("/v1/discovered-access"),
        "ak":       doc["ak"],
        "state":    doc["state"],
    }, 201 if created else 200)


@bp.route("/v1/cot-events", methods=["POST"])
@require_bearer("dcc")
def submit_cot_event(token_payload):
    body   = request.get_json(silent=True) or {}
    errors = []
    for f in ["mpxn", "effective-date", "source-reference"]:
        if not body.get(f):
            errors.append(f"'{f}' required")
    if body.get("mpxn") and not MPXN_RE.match(str(body["mpxn"])):
        errors.append("mpxn invalid format")
    if errors:
        return err("; ".join(errors), 400, "VAL001")

    doc, created = db.submit_cot_event(body)
    mpxn         = body["mpxn"]

    active_records    = db.get_active_records_for_mpxn(mpxn) if created else []
    affected_aks      = [r["ak"] for r in active_records]
    notified_duids    = list({r["duid"] for r in active_records})

    if created:
        deliver_event(
            duid=None,
            event_type="tenancy.change",
            payload={
                "mpxn":           mpxn,
                "effective-date": body["effective-date"],
                "affected-aks":   affected_aks,
            },
            mpxn=mpxn,
        )

    return ok({
        "response":               meta("/v1/cot-events"),
        "mpxn":                   mpxn,
        "effective-date":         body["effective-date"],
        "source-reference":       body["source-reference"],
        "active-records-affected": len(affected_aks),
        "data-users-notified":    notified_duids,
    }, 201 if created else 200)
