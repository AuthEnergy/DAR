import base64

from flask import Blueprint, request

from app import db
from app.auth import create_token
from app.utils import ok, err

bp = Blueprint("auth", __name__)


@bp.route("/v1/auth/token", methods=["GET"])
def get_token():
    """Exchange Basic Auth credentials for a JWT bearer token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return err("Basic Auth required", 401, "AUTH004")
    try:
        decoded    = base64.b64decode(auth[6:]).decode()
        account_id, secret_key = decoded.split(":", 1)
    except Exception:
        return err("Malformed Basic Auth credentials", 401, "AUTH004")

    if not db.verify_account(account_id, secret_key):
        return err("Invalid credentials", 401, "AUTH005")

    account = db.get_account(account_id)
    token, expires = create_token(account_id, account["duid"], account["role"])
    return ok({"bearer-token": token, "expires": expires})
