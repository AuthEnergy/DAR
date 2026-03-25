# DAR — Demo Guide

Everything you need to get the Data Access Register running locally from a fresh clone, populate it with demo data, and walk through the UIs and API.

**Time:** ~10 minutes  
**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or [OrbStack](https://orbstack.dev)) installed and running

---

## 1. Clone and start the stack

```bash
git clone https://github.com/AuthEnergy/DAR.git
cd DAR
# docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up --build
```

This starts two containers:

| Container | What it is | Port |
|---|---|---|
| `couchdb` | Database | `5984` |
| `api` | Flask application | `5001` |

Wait until the logs show:

```
api-1  |  * Running on http://0.0.0.0:5001
```

---

## 2. Seed the demo data

Open a **second terminal** in the project directory:

```bash
docker compose -f docker/docker-compose.yml exec api python seed_demo.py
```

This creates six accounts and five access records matching the customer portal mockup:

| Organisation | Legal basis | Status |
|---|---|---|
| Bright Energy Ltd | `uk-consent` | ACTIVE |
| OctopusFlux Ltd | `uk-consent` | ACTIVE |
| Northern Networks plc | `uk-public-task` | ACTIVE — no expiry |
| GreenSwitch Analytics | `uk-consent` | EXPIRED |
| Acme Energy Services Ltd | — | DISCOVERED (DCC detected, unregistered) |

The script is **idempotent** — safe to re-run, it skips anything already present.

When it completes you'll see:

```
── Demo Credentials ─────────────────────────────────────────────────────────
  API:       http://localhost:5001
  Admin:     http://localhost:5001/admin
  Dashboard: http://localhost:5001/dashboard
  Portal:    http://localhost:5001/portal

  Account ID                Role             Secret Key
  ─────────────────────────  ───────────────  ──────────────────────────────
  admin_ops                 admin            admin-secret-demo
  bright_energy             data_user        bright-secret-demo
  octopusflux               data_user        octopus-secret-demo
  northern_networks         data_user        northern-secret-demo
  greenswitch               data_user        greenswitch-secret-demo
  dcc_system                dcc              dcc-secret-demo

  Customer MPxN: 2312345678901
```

---

## 3. Open the interfaces

### Customer Portal — `http://localhost:5001/portal`

The portal loads demo data automatically. You should see the full access register for meter point `2312345678901`:

- **Bright Energy Ltd** — ACTIVE, consent, `HH-CONSUMPTION / HH-EXPORT / TARIFF-IMPORT`, Withdraw button
- **OctopusFlux Ltd** — ACTIVE, consent, `HH-CONSUMPTION`, Withdraw button
- **Northern Networks plc** — ACTIVE, public task, no expiry, Contact link (cannot be withdrawn by the customer)
- **Acme Energy Services Ltd** — purple DETECTED banner (unregistered access, no legal basis on file)
- **GreenSwitch Analytics** — EXPIRED, greyed out row

**To demonstrate consent withdrawal:** click **✕ Withdraw** on Bright Energy or OctopusFlux, choose a reason, and confirm. The record immediately transitions to REVOKED and is removed from the active list.

The **config bar** at the top of the portal lets you switch account credentials or MPxN during a demo without reloading.

---

### Data User Dashboard — `http://localhost:5001/dashboard`

Sign in with any Data User account, for example Bright Energy:

| Field | Value |
|---|---|
| Account ID | `bright_energy` |
| Secret Key | `bright-secret-demo` |

Shows Bright Energy's own access records, webhook subscriptions, account profile, and activity log. Try signing in as `octopusflux` or `northern_networks` to see different views.

---

### Admin UI — `http://localhost:5001/admin`

| Field | Value |
|---|---|
| Account ID | `admin_ops` |
| Secret Key | `admin-secret-demo` |

All accounts across the register, cross-account record search, all webhook subscriptions, and the full audit log.

---

## 4. Try the API

### Get a bearer token

```bash
curl -s -u bright_energy:bright-secret-demo \
  http://localhost:5001/v1/auth/token | python3 -m json.tool
```

Copy the `bearer-token` value:

```bash
TOKEN="eyJ..."
```

### Create an Identity Record

Identity Records hold the person-property relationship separately from access records — MPxN, move-in date, address, and identity verification evidence. Create one first, then link it when registering an access record.

```bash
curl -s -X POST http://localhost:5001/v1/identity-records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pii-principal": {
      "mpxn": "9900000000001",
      "move-in-date": "2023-06-01",
      "address": {
        "addressLine1": "1 Test Street",
        "townCity": "London",
        "postcode": "EC1A 1BB"
      }
    },
    "expressed-by": "data-subject",
    "principal-verification": {
      "method": "credit-card",
      "verified-at": "2024-06-01T10:00:00Z",
      "outcome": "verified",
      "reference": "ch_demo123",
      "submitted": "XXXX-XXXX-XXXX-4242",
      "verified-against": "Stripe customer record"
    }
  }' | python3 -m json.tool
```

Note the `ir` key in the response — you need it for the next step.

### Register an Access Record

```bash
IR="ir_..."   # paste the ir key from above

curl -s -X POST http://localhost:5001/v1/access-records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"record-metadata\": {
      \"schema-version\": \"1.0\",
      \"controller-arrangement\": {
        \"arrangement-type\": \"sole\",
        \"controllers\": [{
          \"name\": \"Bright Energy Ltd\",
          \"role\": \"sole\",
          \"contact-url\": \"https://bright-energy.com/contact\",
          \"privacy-rights-url\": \"https://bright-energy.com/rights\"
        }]
      },
      \"identity-record-ref\": \"$IR\"
    },
    \"notice\": {
      \"shared-notice\": {
        \"terms-url\": \"https://bright-energy.com/privacy-v3.html\",
        \"notice-version\": \"v3.2\",
        \"notice-language\": \"en\"
      }
    },
    \"processing\": {
      \"legal-basis\": \"uk-consent\",
      \"purpose\": \"Energy efficiency analysis and tariff recommendations\",
      \"data-types\": [\"HH-CONSUMPTION\", \"HH-EXPORT\"]
    },
    \"access-event\": {
      \"state\": \"ACTIVE\",
      \"registered-at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
      \"expiry\": \"2028-01-01T00:00:00Z\",
      \"controller-reference\": \"REF-DEMO-001\",
      \"consent\": {
        \"consent-type\": \"expressed-consent\",
        \"method\": \"Explicit web checkbox\"
      }
    }
  }" | python3 -m json.tool
```

Note the `access-token.key` (`ak_...`) in the response.

### Verify an Access Record (as a Data Provider — no auth required)

```bash
AK="ak_..."   # paste the access key from above

curl -s http://localhost:5001/v1/access-records/$AK | python3 -m json.tool
```

This endpoint requires no authentication — the `ak` is the credential. It returns the full access record with no PII. PII stays in the Identity Record, accessible only to authenticated Data Users.

### List all records for a meter point

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/v1/meter-points/2312345678901/access-records \
  | python3 -m json.tool
```

### Look up a Data User (Data Provider directory)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/v1/data-users/duid_brightenergy0000000000 \
  | python3 -m json.tool
```

### Revoke an access record

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5001/v1/access-records/$AK?reason=customer-request" \
  | python3 -m json.tool
```

Valid `reason` values: `customer-request`, `contract-ended`, `lia-lapsed`, `statutory-authority-lapsed`, `data-no-longer-required`, `other`

---

## 5. Run the tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

All tests run with mocked CouchDB — no running stack required.

---

## 6. Inspect the database

CouchDB's built-in admin UI is at:

```
http://localhost:5984/_utils
```

Username: `admin` · Password: `devpassword`

| Database | Contents |
|---|---|
| `dar_identity` | Identity Records — PII, verification evidence, passkey credentials |
| `dar_records` | Access Records and Discovered Records |
| `dar_accounts` | API accounts |
| `dar_webhooks` | Webhook subscriptions |
| `dar_sessions` | Portal sessions and CoT events |
| `dar_audit` | Audit log |

---

## 7. Reset and start over

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up
docker compose -f docker/docker-compose.yml exec api python seed_demo.py
```

---

## Troubleshooting

**`Error: No such service: api`**  
Run `docker compose up` first (step 1), then run the seed script in a second terminal.

**Seed script returns auth errors**  
The API may still be initialising. Wait 5–10 seconds and try again.

**`connection refused` on CouchDB**  
On first boot the `api` container can start before CouchDB is fully ready. The app retries automatically — if the seed script fails immediately after `docker compose up`, wait a few seconds and retry.

**View live API logs**  
```bash
docker compose -f docker/docker-compose.yml logs -f api
```
