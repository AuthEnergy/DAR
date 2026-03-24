# Data Access Register (DAR)

Design documentation and API specification for the **Central Data Access Register** — a lightweight, open register of lawful customer energy data access across all UK GDPR legal bases.

> **This is a design proposal for review and not yet a completed and implementable service.**  
> To discuss the design, contact [contact@auth.energy](mailto:contact@auth.energy).

**Docs:** [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)

---

## What Is It?

The DAR is a practical, lightweight alternative to a full [Consumer Consent Solution](https://retailenergycode.co.uk/our-programmes/consumer-consent-solution/) being designed by [Retail Energy Code](https://retailenergycode.co.uk/). It records all lawful access to customer energy meter data — not just consent — and is designed for UK energy industry use under the Smart Energy Code.

Key properties:

* Records access under **any lawful basis** — consent, legitimate interests, public task, legal obligation, or contract
* **ISO/IEC TS 27560:2023** compliant record structure
* **SEC compliant** — Data Users are registered as SEC Other Users
* Supports any approved **Identity Verification Scheme**
* Supports **automatic discovery** of access via DCC transaction logs
* Notifies Data Users of **Change of Tenancy** events via webhook
* Supports a **Central Customer Portal** and in-app consent display
* Enables **re-identification** of returning customers via passkey or magic link — no re-collection required
* Historic and expired access records can be submitted at any time

---

## Party Model

| Party | UK GDPR Role | Description |
| --- | --- | --- |
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

Full specification and endpoint details: [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)

---

## Contributing

This is an open design proposal. Feedback and contributions are welcome — open an issue or contact [contact@auth.energy](mailto:contact@auth.energy).

---

## License

See [LICENSE.md](LICENSE.md).

---

*[Auth Energy](https://auth.energy) · [docs.auth.energy/data-access-register](https://docs.auth.energy/data-access-register)*
