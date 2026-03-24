# Data Access Register (DAR)

Design documentation and API specification for the **Central Data Access Register** — a lightweight, open register of lawful customer energy data access across all UK GDPR legal bases.

> **This is a design proposal for review and not yet a completed and implementable service.**  
> To discuss the design, contact [contact@auth.energy](mailto:contact@auth.energy).

**Docs:** [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)

---

## What Is It?

The DAR is a practical, lightweight alternative to a full [Consumer Consent Solution](https://retailenergycode.co.uk/our-programmes/consumer-consent-solution/) being design by [Retail Energy Code](https://retailenergycode.co.uk/). It records all lawful access to customer energy meter data — not just consent — and is designed for UK energy industry use under the Smart Energy Code.

Key properties:

- Records access under **any lawful basis** — consent, legitimate interests, public task, legal obligation, or contract
- **ISO/IEC TS 27560:2023** compliant record structure
- **SEC compliant** — Data Users are registered as SEC Other Users
- Supports any approved **Identity Verification Scheme**
- Supports **automatic discovery** of access via DCC transaction logs
- Notifies Data Users of **Change of Tenancy** events via webhook
- Supports a **Central Customer Portal** and in-app consent display
- Enables **re-identification** of returning customers via passkey or magic link — no re-collection required
- Historic and expired access records can be submitted at any time

---

## Party Model

| Party | UK GDPR Role | Description |
|---|---|---|
| **Data User** | Processor | Registers and manages access records. Authenticated via bearer token. SEC Other User. |
| **Controller** | Data Controller | B2B customer of the Data User. Bears GDPR accountability for the legal basis claimed. |
| **Customer** | Data Subject | The energy customer. Identified by MPxN and an Identity Record. |
| **Data Provider** | Data Source | Verifies access records before releasing meter data. |
| **DCC** | — | Submits discovered access records and Change of Tenancy events. |

---

## Record Architecture

Registration is a two-step process that separates PII from access authorisation:

```
AccessRecord
└── record-metadata
    ├── controller              (who is accessing)
    └── identity-record-ref → ir_...
                                    │
                              IdentityRecord
                              ├── pii-principal   (MPxN, address, move-in)
                              ├── expressed-by
                              ├── principal-verification
                              ├── email (hashed)
                              └── credentials[]   (passkey public keys)
```

**Why separated?** The unauthenticated verification endpoint used by Data Providers (`GET /access-records/{ak}`) never exposes customer PII. Identity evidence is accessible only to authenticated Data Users.

---

## API Reference

Full specification: [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)

### Authentication

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/token` | Exchange Basic Auth credentials for a JWT bearer token (7200s) |

### Identity Records

| Method | Path | Description |
|---|---|---|
| `GET` | `/identity-records` | Look up identity records by MPxN or email |
| `POST` | `/identity-records` | Create an identity record |
| `GET` | `/identity-records/{ir}` | Retrieve an identity record |
| `DELETE` | `/identity-records/{ir}` | Anonymise an identity record (GDPR Art. 17) |
| `DELETE` | `/identity-records/{ir}/credentials/{credentialId}` | Remove a passkey credential |
| `POST` | `/identity-records/{ir}/re-identify` | Initiate re-identification (passkey or magic link) |
| `GET` | `/identity-records/{ir}/re-identify/{token-ref}` | Confirm re-identification status |

### Data Users

| Method | Path | Description |
|---|---|---|
| `POST` | `/access-records` | Create an access record |
| `PUT` | `/access-records/{ak}` | Replace an access record |
| `DELETE` | `/access-records/{ak}` | Revoke an access record |
| `GET` | `/meter-points/{mpxn}/access-records` | List access records for a meter point |

### Data Providers

| Method | Path | Description |
|---|---|---|
| `GET` | `/access-records/{ak}` | Verify an access record (unauthenticated) |
| `GET` | `/data-users/{duid}` | Look up a Data User by DUID |

### DCC

| Method | Path | Description |
|---|---|---|
| `POST` | `/access-records/discovered` | Submit a discovered access record |
| `POST` | `/tenancy-changes` | Submit a Change of Tenancy event |

### Webhooks

| Method | Path | Description |
|---|---|---|
| `GET` | `/webhooks` | List webhook subscriptions |
| `POST` | `/webhooks` | Register a webhook subscription |
| `DELETE` | `/webhooks/{id}` | Delete a webhook subscription |
| `PATCH` | `/webhooks/{id}` | Update a webhook subscription |

---

## Access Record Lifecycle

Records are never hard-deleted. All state transitions are recorded with timestamps.

```
[ACTIVE] ──revoke──▶ [REVOKED]
[ACTIVE] ──expiry──▶ [EXPIRED]
```

Data Providers must deny access for any record not in `ACTIVE` state with a future (or null) expiry.

---

## Webhook Events

Data Users subscribe to lifecycle events delivered to a single callback URL, distinguished by `event-type`:

| Event | Trigger |
|---|---|
| `consent.withdrawal` | Customer withdraws consent via the Customer Portal |
| `consent.expiry` | Access record within the configured notification window of expiry (default 30 days) |
| `tenancy.change` | DCC reports a Change of Tenancy on an MPxN with active records |

---

## Customer Portal

A centralised web interface at `central.consent` allows customers to view all registered access to their meter point and withdraw consent directly, without going through a Data User. See [Customer Portal docs](https://docs.auth.energy/data-access-register/customer-portal).

---

## Re-identification

When a customer returns, Data Users can re-identify them against their existing Identity Record without re-collecting details. Three methods are supported:

| Method | When to use |
|---|---|
| **Passkey assertion** | Customer has a registered passkey — one tap via biometric |
| **Magic link** | Email stored, no passkey or new device |
| **Passkey registration** | No passkey registered — enrol a new one |

The WebAuthn ceremony is hosted on `id.central.consent` so passkeys work consistently across all Data Users and the Customer Portal.

---

## Contributing

This is an open design proposal. Feedback and contributions are welcome — see the [GitHub repo](https://github.com/AuthEnergy/dar) or contact [contact@auth.energy](mailto:contact@auth.energy).

---

## License

See [LICENSE.md](LICENSE.md).

---

*[Auth Energy](https://auth.energy) · [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)*
