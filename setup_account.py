#!/usr/bin/env python3
"""
setup_account.py — provision an API account in the DAR register.

Usage:
  python setup_account.py \
    --account-id admin_ops \
    --secret-key s3cr3t \
    --duid duid_$(openssl rand -hex 12) \
    --display-name "Ops Team" \
    --role admin

Roles: data_user | data_provider | dcc | admin
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.config import Config
from app import db


def main():
    parser = argparse.ArgumentParser(description="Provision a DAR account")
    parser.add_argument("--account-id",   required=True)
    parser.add_argument("--secret-key",   required=True)
    parser.add_argument("--duid",         required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--role",         required=True,
                        choices=["data_user", "data_provider", "dcc", "admin"])
    parser.add_argument("--contact-url",  default="")
    args = parser.parse_args()

    print(f"Connecting to CouchDB at {Config.COUCHDB_URL} ...")
    db.init_db()

    existing = db.get_account(args.account_id)
    if existing:
        print(f"Account '{args.account_id}' already exists — skipping.")
        sys.exit(0)

    doc = db.create_account(
        account_id=args.account_id,
        secret_key=args.secret_key,
        duid=args.duid,
        display_name=args.display_name,
        role=args.role,
        contact_url=args.contact_url,
    )
    print(f"✓ Created account '{doc['_id']}' (duid={doc['duid']}, role={doc['role']})")


if __name__ == "__main__":
    main()
