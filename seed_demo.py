#!/usr/bin/env python3
"""
seed_demo.py — Seed the DAR with demo data matching the customer portal mockup.

Creates identity records first, then links access records via identity-record-ref,
using the real spec schema (controller-arrangement, not inline controller/pii-principal).

Usage:
  python seed_demo.py [--api http://localhost:5000]
"""
import argparse, base64, json, sys, subprocess, os
import urllib.request, urllib.error

DEMO_MPXN = "2312345678901"

ACCOUNTS = [
    {"account-id": "admin_ops",         "secret-key": "admin-secret-demo",
     "duid": "duid_adminops000000000000",   "display-name": "Ops Team",
     "role": "admin",                        "contact-url": "https://central.consent/contact"},
    {"account-id": "bright_energy",     "secret-key": "bright-secret-demo",
     "duid": "duid_brightenergy0000000000",  "display-name": "Bright Energy Ltd",
     "role": "data_user",                    "contact-url": "https://bright-energy.com/contact"},
    {"account-id": "octopusflux",       "secret-key": "octopus-secret-demo",
     "duid": "duid_octopusflux00000000000",  "display-name": "OctopusFlux Ltd",
     "role": "data_user",                    "contact-url": "https://octopusflux.com/contact"},
    {"account-id": "northern_networks", "secret-key": "northern-secret-demo",
     "duid": "duid_northernnetworks000000",  "display-name": "Northern Networks plc",
     "role": "data_user",                    "contact-url": "https://northernnetworks.co.uk/contact"},
    {"account-id": "greenswitch",       "secret-key": "greenswitch-secret-demo",
     "duid": "duid_greenswitch00000000000",  "display-name": "GreenSwitch Analytics",
     "role": "data_user",                    "contact-url": "https://greenswitch.io/contact"},
    {"account-id": "dcc_system",        "secret-key": "dcc-secret-demo",
     "duid": "duid_dccsystem000000000000",   "display-name": "Smart DCC",
     "role": "dcc",                          "contact-url": "https://smartdcc.co.uk"},
    {"account-id": "portal_ops",        "secret-key": "portal-secret-demo",
     "duid": "duid_portalops000000000000",   "display-name": "Central Access Register Portal",
     "role": "portal",                       "contact-url": "https://central.consent"},
]

IDENTITY_RECORDS = [
    {
        "_account": "bright_energy",
        "_label":   "Bright Energy — customer at 14 Acacia Avenue",
        "pii-principal": {
            "mpxn": DEMO_MPXN, "move-in-date": "2022-06-30",
            "address": {"addressLine1": "14 Acacia Avenue",
                        "townCity": "Manchester", "postcode": "M14 5RT"},
        },
        "expressed-by": "data-subject",
        "email": "demo.customer@example.com",
        "principal-verification": {
            "method": "credit-card", "verified-at": "2023-11-07T05:30:45Z",
            "outcome": "verified", "reference": "ch_3ABC123xyz",
            "submitted": "XXXX-XXXX-XXXX-4242",
            "verified-against": "Stripe customer record cus_ABC123",
            "detail": {"last4": "4242", "brand": "visa"},
        },
    },
    {
        "_account": "octopusflux",
        "_label":   "OctopusFlux — same customer",
        "pii-principal": {"mpxn": DEMO_MPXN, "move-in-date": "2022-06-30"},
        "expressed-by": "data-subject",
        "principal-verification": {
            "method": "existing-authenticated-session",
            "verified-at": "2024-01-14T09:58:00Z",
            "outcome": "verified", "reference": "sess_OFX9928abc",
            "submitted": "Authenticated session token",
            "verified-against": "OctopusFlux customer account OFX-9928",
        },
    },
    {
        "_account": "northern_networks",
        "_label":   "Northern Networks — statutory access",
        "pii-principal": {"mpxn": DEMO_MPXN, "move-in-date": "2019-06-01"},
        "expressed-by": "data-subject",
        "principal-verification": None,
    },
    {
        "_account": "greenswitch",
        "_label":   "GreenSwitch — expired consent",
        "pii-principal": {"mpxn": DEMO_MPXN, "move-in-date": "2020-01-01"},
        "expressed-by": "data-subject",
        "principal-verification": {
            "method": "account-postcode", "verified-at": "2022-03-03T08:55:00Z",
            "outcome": "verified", "reference": "VER-GS-20220303-001",
            "submitted": "postcode M14 5RT",
            "verified-against": "GreenSwitch utility account on file",
        },
    },
]

ACCESS_RECORDS = [
    {
        "_account": "bright_energy",
        "_ir_index": 0,
        "_label":    "Bright Energy — Consent, ACTIVE",
        "record-metadata": {
            "schema-version": "1.0",
            "controller-arrangement": {
                "arrangement-type": "sole",
                "controllers": [{
                    "name": "Bright Energy Ltd", "role": "sole",
                    "contact-url": "https://bright-energy.com/contact",
                    "address": {"addressLine1": "10 Canary Wharf",
                                "townCity": "London", "postcode": "E14 5AB"},
                    "privacy-rights-url": "https://bright-energy.com/your-rights",
                    "storage-conditions": {"location": "GB", "retention-period": "P2Y"},
                }],
            },
            "identity-record-ref": None,  # filled in at runtime
        },
        "notice": {
            "shared-notice": {
                "terms-url": "https://bright-energy.com/privacy-v3.html",
                "notice-version": "v3.2", "notice-language": "en",
            }
        },
        "processing": {
            "legal-basis": "uk-consent",
            "purpose": "Energy efficiency analysis and tariff recommendations",
            "data-types": ["HH-CONSUMPTION", "HH-EXPORT", "TARIFF-IMPORT"],
        },
        "access-event": {
            "state": "ACTIVE", "registered-at": "2023-11-07T05:31:56Z",
            "expiry": "2027-11-10T17:07:01Z", "controller-reference": "REF-00123",
            "consent": {"consent-type": "expressed-consent", "method": "Explicit web checkbox"},
        },
    },
    {
        "_account": "octopusflux",
        "_ir_index": 1,
        "_label":    "OctopusFlux — Consent, ACTIVE",
        "record-metadata": {
            "schema-version": "1.0",
            "controller-arrangement": {
                "arrangement-type": "sole",
                "controllers": [{
                    "name": "OctopusFlux Ltd", "role": "sole",
                    "contact-url": "https://octopusflux.com/contact",
                    "address": {"addressLine1": "100 Oxford Street",
                                "townCity": "London", "postcode": "W1D 1LL"},
                    "privacy-rights-url": "https://octopusflux.com/rights",
                }],
            },
            "identity-record-ref": None,
        },
        "notice": {
            "shared-notice": {
                "terms-url": "https://octopusflux.com/privacy.html",
                "notice-version": "v1.0", "notice-language": "en",
            }
        },
        "processing": {
            "legal-basis": "uk-consent",
            "purpose": "Flexible tariff optimisation and demand forecasting",
            "data-types": ["HH-CONSUMPTION"],
            "data-source": "Bright Energy Ltd / MPAS",
        },
        "access-event": {
            "state": "ACTIVE", "registered-at": "2024-01-14T10:00:00Z",
            "expiry": "2028-01-14T00:00:00Z", "controller-reference": "OFX-2024-001",
            "consent": {"consent-type": "expressed-consent", "method": "In-app toggle"},
        },
    },
    {
        "_account": "northern_networks",
        "_ir_index": 2,
        "_label":    "Northern Networks — Public Task, ACTIVE, no expiry",
        "record-metadata": {
            "schema-version": "1.0",
            "controller-arrangement": {
                "arrangement-type": "sole",
                "controllers": [{
                    "name": "Northern Networks plc", "role": "sole",
                    "contact-url": "https://northernnetworks.co.uk/contact",
                    "address": {"addressLine1": "1 Grid House",
                                "townCity": "Leeds", "postcode": "LS1 1AA"},
                    "privacy-rights-url": "https://northernnetworks.co.uk/your-rights",
                    "statutory-reference": "Energy Act 2023, s.147",
                }],
            },
            "identity-record-ref": None,
        },
        "notice": None,
        "processing": {
            "legal-basis": "uk-public-task",
            "purpose": "Statutory network safety and capacity monitoring",
            "data-types": ["HH-CONSUMPTION", "HH-EXPORT"],
        },
        "access-event": {
            "state": "ACTIVE", "registered-at": "2024-01-15T00:00:00Z",
            "expiry": None, "controller-reference": "OFGEM-AUTH-2024-0042",
            "consent": None,
        },
    },
    {
        "_account": "greenswitch",
        "_ir_index": 3,
        "_label":    "GreenSwitch — Consent, EXPIRED",
        "record-metadata": {
            "schema-version": "1.0",
            "controller-arrangement": {
                "arrangement-type": "sole",
                "controllers": [{
                    "name": "GreenSwitch Analytics", "role": "sole",
                    "contact-url": "https://greenswitch.io/contact",
                    "address": {"addressLine1": "22 Fintech Quarter",
                                "townCity": "Bristol", "postcode": "BS1 5TR"},
                    "privacy-rights-url": "https://greenswitch.io/rights",
                }],
            },
            "identity-record-ref": None,
        },
        "notice": {
            "shared-notice": {
                "terms-url": "https://greenswitch.io/privacy.html",
                "notice-version": "v2.1", "notice-language": "en",
            }
        },
        "processing": {
            "legal-basis": "uk-consent",
            "purpose": "Annual consumption benchmarking and carbon reporting",
            "data-types": ["ANNUAL-CONSUMPTION"],
        },
        "access-event": {
            "state": "ACTIVE", "registered-at": "2022-03-03T09:00:00Z",
            "expiry": "2024-03-03T00:00:00Z",  # past — will be EXPIRED
            "controller-reference": "GS-2022-882",
            "consent": {"consent-type": "expressed-consent", "method": "Signed paper form"},
        },
    },
]

DISCOVERED_RECORD = {
    "mpxn": DEMO_MPXN,
    "organisation-name": "Acme Energy Services Ltd",
    "organisation-reference": "SEC-OU-00429",
    "source-reference": "DCC-TRANS-2024-06-01",
    "first-seen": "2024-06-01",
    "last-seen":  "2026-02-28",
    "data-types-observed": ["HH-CONSUMPTION"],
}


def http(method, url, body=None, headers=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method,
                                  headers=headers or {})
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def basic_auth(account_id, secret):
    return "Basic " + base64.b64encode(f"{account_id}:{secret}".encode()).decode()

def get_token(api_base, account_id, secret):
    status, data = http("GET", f"{api_base}/v1/auth/token",
                        headers={"Authorization": basic_auth(account_id, secret)})
    if status != 200:
        raise RuntimeError(f"Auth failed for {account_id}: {status} {data}")
    return data["bearer-token"]

def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def seed_accounts(api_base, admin_token):
    print("\n── Accounts ─────────────────────────────────────────────────")
    secrets_map = {}
    for acc in ACCOUNTS:
        status, data = http("POST", f"{api_base}/v1/admin/accounts",
                            body=acc, headers=bearer(admin_token))
        if status == 201:
            print(f"  ✓  {acc['account-id']:25} ({acc['role']})")
        elif status == 409:
            print(f"  ·  {acc['account-id']:25} already exists")
        else:
            print(f"  ✗  {acc['account-id']:25} ERROR {status}: {data}")
        secrets_map[acc["account-id"]] = acc["secret-key"]
    return secrets_map


def seed_identity_records(api_base, account_secrets):
    print("\n── Identity Records ─────────────────────────────────────────")
    ir_keys = []
    for ir_body in IDENTITY_RECORDS:
        account_id = ir_body.pop("_account")
        label      = ir_body.pop("_label")
        secret     = account_secrets.get(account_id)
        try:
            token = get_token(api_base, account_id, secret)
        except RuntimeError as e:
            print(f"  ✗  {label} — {e}")
            ir_keys.append(None)
            continue

        status, data = http("POST", f"{api_base}/v1/identity-records",
                            body=ir_body, headers=bearer(token))
        if status == 201:
            ir = data["ir"]
            print(f"  ✓  {label}")
            print(f"     ir: {ir}")
            ir_keys.append(ir)
        else:
            print(f"  ✗  {label} ERROR {status}: {data}")
            ir_keys.append(None)
    return ir_keys


def seed_access_records(api_base, account_secrets, ir_keys):
    print("\n── Access Records ───────────────────────────────────────────")
    created_aks = []
    for rec in ACCESS_RECORDS:
        account_id = rec.pop("_account")
        ir_index   = rec.pop("_ir_index")
        label      = rec.pop("_label")
        ir_key     = ir_keys[ir_index] if ir_index < len(ir_keys) else None
        if not ir_key:
            print(f"  ✗  {label} — no identity record")
            continue

        rec["record-metadata"]["identity-record-ref"] = ir_key

        secret = account_secrets.get(account_id)
        try:
            token = get_token(api_base, account_id, secret)
        except RuntimeError as e:
            print(f"  ✗  {label} — {e}")
            continue

        status, data = http("POST", f"{api_base}/v1/access-records",
                            body=rec, headers=bearer(token))
        if status == 201:
            ak = data["access-token"]["key"]
            print(f"  ✓  {label}")
            print(f"     ak: {ak}")
            created_aks.append((label, ak))
        else:
            print(f"  ✗  {label} ERROR {status}: {data}")
    return created_aks


def seed_discovered(api_base, account_secrets):
    print("\n── Discovered Record (DCC) ──────────────────────────────────")
    secret = account_secrets.get("dcc_system")
    try:
        token = get_token(api_base, "dcc_system", secret)
    except RuntimeError as e:
        print(f"  ✗  {e}"); return
    status, data = http("POST", f"{api_base}/v1/discovered-access",
                        body=DISCOVERED_RECORD, headers=bearer(token))
    if status in (200, 201):
        verb = "created" if status == 201 else "already exists"
        print(f"  ✓  Acme Energy Services Ltd (DISCOVERED) — {verb}")
        print(f"     ak: {data['ak']}")
    else:
        print(f"  ✗  ERROR {status}: {data}")


def verify_demo(api_base, account_secrets, aks):
    print("\n── Verification ─────────────────────────────────────────────")
    print(f"  MPxN: {DEMO_MPXN}")
    for label, ak in aks:
        status, data = http("GET", f"{api_base}/v1/access-records/{ak}")
        if status == 200:
            rec   = data["access-record"]
            state = rec.get("access-event", {}).get("state", "?")
            basis = rec.get("processing", {}).get("legal-basis", "?")
            arr   = rec.get("record-metadata", {}).get("controller-arrangement", {})
            ctrl  = next((c.get("name","?") for c in arr.get("controllers",[])
                          if c.get("role") in ("sole","lead")), "?")
            print(f"  ✓  {ctrl:30} {basis:30} {state}")
        else:
            print(f"  ✗  {ak} ERROR {status}")

    bright_secret = account_secrets.get("bright_energy")
    if bright_secret:
        try:
            token  = get_token(api_base, "bright_energy", bright_secret)
            status, data = http(
                "GET",
                f"{api_base}/v1/meter-points/{DEMO_MPXN}/access-records",
                headers=bearer(token),
            )
            if status == 200:
                records = data.get("access-records", [])
                print(f"\n  GET /v1/meter-points/{DEMO_MPXN}/access-records")
                print(f"  {len(records)} record(s):")
                for r in records:
                    state = r.get("state", "?")
                    basis = r.get("legal-basis") or "discovered"
                    ctrl  = r.get("lead-controller-name") or \
                            (r.get("discovered-access") or {}).get("organisation-name","?")
                    print(f"    · {ctrl:30} {basis:30} {state}")
        except RuntimeError as e:
            print(f"  ✗  Could not list: {e}")


def print_summary(api_base):
    # Always show host-facing URLs in the summary (port 5001 on the host)
    host_base = api_base.replace("localhost:5000", "localhost:5001")
    print("\n── Demo Credentials ─────────────────────────────────────────")
    print(f"  API:       {host_base}")
    print(f"  Admin:     {host_base}/admin")
    print(f"  Dashboard: {host_base}/dashboard")
    print(f"  Portal:    {host_base}/portal")
    print()
    print(f"  {'Account ID':<25}  {'Role':<15}  Secret Key")
    print(f"  {'─'*25}  {'─'*15}  {'─'*30}")
    for acc in ACCOUNTS:
        print(f"  {acc['account-id']:<25}  {acc['role']:<15}  {acc['secret-key']}")
    print(f"\n  Customer MPxN: {DEMO_MPXN}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:5000")
    args    = parser.parse_args()
    api_base = args.api.rstrip("/")

    print(f"DAR Demo Seed — {api_base}")
    print("─" * 60)

    print("\n── Bootstrap admin ──────────────────────────────────────────")
    admin = next(a for a in ACCOUNTS if a["account-id"] == "admin_ops")
    result = subprocess.run(
        [sys.executable,
         os.path.join(os.path.dirname(__file__), "setup_account.py"),
         "--account-id",   admin["account-id"],
         "--secret-key",   admin["secret-key"],
         "--duid",         admin["duid"],
         "--display-name", admin["display-name"],
         "--role",         admin["role"],
         "--contact-url",  admin["contact-url"]],
        capture_output=True, text=True,
    )
    print(f"  {(result.stdout or result.stderr).strip()}")

    admin_token = get_token(api_base, admin["account-id"], admin["secret-key"])
    print(f"  ✓  Admin token obtained")

    account_secrets = seed_accounts(api_base, admin_token)
    ir_keys         = seed_identity_records(api_base, account_secrets)
    aks             = seed_access_records(api_base, account_secrets, ir_keys)
    seed_discovered(api_base, account_secrets)
    verify_demo(api_base, account_secrets, aks)
    print_summary(api_base)


if __name__ == "__main__":
    main()
