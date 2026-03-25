"""
Identity Records routes.

GET  /v1/identity-records?mpxn=&email=
POST /v1/identity-records
GET  /v1/identity-records/{ir}
DELETE /v1/identity-records/{ir}
DELETE /v1/identity-records/{ir}/credentials/{credentialId}
POST /v1/identity-records/{ir}/re-identify
GET  /v1/identity-records/{ir}/re-identify/{tokenRef}
"""
from flask import Blueprint, request
from app import db
from app.utils import (ok, err, meta, require_bearer,
                        validate_identity_record, serialise_identity_record,
                        MPXN_RE)

bp = Blueprint("identity_records", __name__)


@bp.route("/v1/identity-records", methods=["GET"])
@require_bearer("data_user")
def lookup_identity_records(token_payload):
    mpxn  = request.args.get("mpxn")
    email = request.args.get("email")
    if not mpxn and not email:
        return err("At least one of mpxn or email must be supplied", 400, "VAL001")
    if mpxn and not MPXN_RE.match(str(mpxn)):
        return err("mpxn invalid format", 400, "VAL001")

    docs = db.lookup_identity_records(token_payload["duid"], mpxn=mpxn, email=email)
    return ok({
        "response":         meta("/v1/identity-records"),
        "identity-records": [serialise_identity_record(d) for d in docs],
    })


@bp.route("/v1/identity-records", methods=["POST"])
@require_bearer("data_user")
def create_identity_record(token_payload):
    body   = request.get_json(silent=True) or {}
    errors = validate_identity_record(body)
    if errors:
        return err("; ".join(errors), 400, "VAL001")

    doc, passkey_redirect = db.create_identity_record(token_payload["duid"], body)
    ir = doc["ir"]

    try:
        db.write_audit(token_payload["sub"], "identity-record.created",
                       {"ir": ir, "mpxn": doc.get("mpxn")})
    except Exception:
        pass

    resp = ok({
        "response":                    meta(f"/v1/identity-records/{ir}"),
        "ir":                          ir,
        "passkey-registration-redirect": passkey_redirect,
    }, 201)
    resp[0].headers["Location"] = f"/v1/identity-records/{ir}"
    return resp


@bp.route("/v1/identity-records/<ir>", methods=["GET"])
@require_bearer("data_user")
def get_identity_record(ir, token_payload):
    doc = db.get_identity_record(ir, token_payload["duid"])
    if not doc:
        return err("Identity record not found or access denied", 404, "NOT001")
    return ok({
        "response":        meta(f"/v1/identity-records/{ir}"),
        "identity-record": serialise_identity_record(doc),
    })


@bp.route("/v1/identity-records/<ir>", methods=["DELETE"])
@require_bearer("data_user")
def anonymise_identity_record(ir, token_payload):
    doc, error = db.anonymise_identity_record(ir, token_payload["duid"])
    if error == "NOT_FOUND":
        return err("Identity record not found or access denied", 404, "NOT001")
    if error == "CONFLICT":
        return err("One or more linked access records are still ACTIVE. "
                   "Revoke all linked records before anonymising.", 409, "CON001")

    try:
        db.write_audit(token_payload["sub"], "identity-record.anonymised", {"ir": ir})
    except Exception:
        pass
    return ok({
        "response":      meta(f"/v1/identity-records/{ir}"),
        "ir":            ir,
        "anonymised-at": doc["anonymised_at"],
    })


@bp.route("/v1/identity-records/<ir>/credentials/<credential_id>",
          methods=["DELETE"])
@require_bearer("data_user")
def remove_passkey_credential(ir, credential_id, token_payload):
    if not db.remove_passkey_credential(ir, token_payload["duid"], credential_id):
        return err("Identity record or credential not found", 404, "NOT001")
    return ("", 204)


@bp.route("/v1/identity-records/<ir>/re-identify", methods=["POST"])
@require_bearer("data_user")
def re_identify(ir, token_payload):
    body   = request.get_json(silent=True) or {}
    method = body.get("method")
    if not method:
        return err("method required", 400, "VAL001")

    result, error = db.initiate_reidentify(
        ir=ir,
        duid=token_payload["duid"],
        method=method,
        redirect_url=body.get("redirect-url"),
        passkey_return_url=body.get("passkey-return-url"),
    )

    if error == "NOT_FOUND":
        return err("Identity record not found or access denied", 404, "NOT001")
    if error == "ANONYMISED":
        return err("Identity record has been anonymised", 409, "CON001")
    if error == "NO_EMAIL":
        return err("magic-link requested but no email stored on this record", 422, "VAL002")
    if error == "NO_CREDENTIALS":
        return err("passkey-assert requested but no credentials registered", 422, "VAL003")
    if error == "INVALID_METHOD":
        return err(f"method must be magic-link, passkey-assert, or passkey-register",
                   400, "VAL001")

    return ok({"response": meta(f"/v1/identity-records/{ir}/re-identify"), **result})


@bp.route("/v1/identity-records/<ir>/re-identify/<token_ref>",
          methods=["GET"])
@require_bearer("data_user")
def poll_reidentify(ir, token_ref, token_payload):
    result, error = db.poll_reidentify(ir, token_payload["duid"], token_ref)
    if error == "NOT_FOUND":
        return err("Identity record or token not found", 404, "NOT001")
    return ok({
        "response":     meta(f"/v1/identity-records/{ir}/re-identify/{token_ref}"),
        "method":       result["method"],
        "status":       result["status"],
        "confirmed-at": result["confirmed-at"],
    })
